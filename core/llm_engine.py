import os
import json
from openai import OpenAI
from dotenv import load_dotenv

from core.sandbox import SecuritySandbox
from plugins.system_control import SYSTEM_TOOLS, SYSTEM_TOOL_MAP
from plugins.git_control import GIT_TOOLS, GIT_TOOL_MAP
from plugins.file_explorer import FILE_TOOLS, FILE_TOOL_MAP
from plugins.hardware_info import HARDWARE_TOOLS, HARDWARE_TOOL_MAP
from plugins.web_network import WEB_TOOLS, WEB_TOOL_MAP
from plugins.terminal_control import TERMINAL_TOOLS, TERMINAL_TOOL_MAP
from plugins.input_control import INPUT_TOOLS, INPUT_TOOL_MAP
from plugins.office_tools import OFFICE_TOOLS, OFFICE_TOOL_MAP
from plugins.code_assistant import CODE_TOOLS, CODE_TOOL_MAP
from core.settings_manager import SettingsManager
from core.tool_router import ToolRouter

# ─── Konfigurasi Backend ────────────────────────────────────────────
OLLAMA_BASE_URL  = "http://localhost:11434/v1"
AZURE_BASE_URL   = "https://models.inference.ai.azure.com"

MAX_AGENT_ITERATIONS = 15  # Batas maksimum putaran tool calling agar tidak infinite loop

class ChatEngine:
    def __init__(self):
        load_dotenv()
        self.settings_mgr = SettingsManager()
        self.token_1 = os.environ.get("GITHUB_TOKEN_1") or os.environ.get("GITHUB_TOKEN")
        self.token_2 = os.environ.get("GITHUB_TOKEN_2")
        self.sandbox = SecuritySandbox()

        # Gabungkan semua Tools dari Plugins (dipakai sebagai pool oleh ToolRouter)
        self.tools = (
            SYSTEM_TOOLS + GIT_TOOLS + FILE_TOOLS +
            HARDWARE_TOOLS + WEB_TOOLS + TERMINAL_TOOLS +
            INPUT_TOOLS + OFFICE_TOOLS + CODE_TOOLS
        )
        self.tool_map = {
            **SYSTEM_TOOL_MAP, **GIT_TOOL_MAP, **FILE_TOOL_MAP,
            **HARDWARE_TOOL_MAP, **WEB_TOOL_MAP, **TERMINAL_TOOL_MAP,
            **INPUT_TOOL_MAP, **OFFICE_TOOL_MAP, **CODE_TOOL_MAP
        }

        # Smart Tool Router — memilih tools yang relevan per request
        self.tool_router = ToolRouter(verbose=False)

        # Default: Jangan inisiasi backend otomatis di sini agar bisa di-load secara async oleh UI
        self.client = None
        self.model = None
        self.backend = None

    # ─── Inisialisasi Backend ────────────────────────────────────────
    def _init_ollama(self, model_tag="qwen2.5:latest"):
        """Koneksi ke Ollama yang berjalan secara lokal."""
        self.client = OpenAI(
            base_url=OLLAMA_BASE_URL,
            api_key="ollama",  # Ollama tidak perlu API key, tapi OpenAI client butuh nilai apapun
        )
        self.model = model_tag
        self.backend = "ollama"
        self._reset_messages()

    def _init_azure(self, token, model_name="gpt-4o"):
        """Koneksi ke Azure OpenAI / GitHub Models."""
        self.client = OpenAI(
            base_url=AZURE_BASE_URL,
            api_key=token,
        )
        self.model = model_name
        self.backend = "azure"
        self._reset_messages()

    def _reset_messages(self):
        self.messages = [
            {"role": "system", "content": self.settings_mgr.get("system_prompt")}
        ]

    def preload_model(self):
        """Kirim dummy request untuk memaksa model dimuat ke VRAM/verifikasi koneksi."""
        if not self.client or not self.model:
            raise ValueError("Klien AI belum diinisialisasi.")
            
        # Kirim 1 token kosong agar Ollama me-load model ke VRAM
        self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=1
        )

    # ─── Pergantian Model dari UI ────────────────────────────────────
    def switch_account(self, account_index, ollama_model_tag: str = None):
        """
        Ganti model backend secara dinamis.
        account_index:
          1   → Ollama lokal (gunakan ollama_model_tag untuk memilih model)
          2   → Azure GPT-4o Akun 1
          3   → Azure GPT-4o Akun 2
        Returns: (success_bool, message_str)
        """
        try:
            if account_index == 1:
                model_tag = ollama_model_tag or "qwen2.5:latest"
                self._init_ollama(model_tag)
                self.preload_model()
                return True, f"Model Ollama '{model_tag}' siap digunakan."
            elif account_index == 2:
                if not self.token_1:
                    return False, "Token GitHub Akun 1 tidak ditemukan di file .env"
                self._init_azure(self.token_1, "gpt-4o")
                self.preload_model()
                return True, "Azure GPT-4o (Akun 1) terhubung."
            elif account_index == 3:
                if not self.token_2:
                    return False, "Token GitHub Akun 2 tidak ditemukan di file .env"
                self._init_azure(self.token_2, "gpt-4o")
                self.preload_model()
                return True, "Azure GPT-4o (Akun 2) terhubung."
            return False, "Indeks akun tidak valid."
        except Exception as e:
            return False, f"Gagal memuat model: {str(e)}"
    # ─── Gaya Bicara ─────────────────────────────────────────────────
    def set_speaking_style(self, style):
        base = self.settings_mgr.get("system_prompt")
        if style == "Singkat & Padat":
            new_prompt = base + " Jawablah dengan SANGAT SINGKAT, PADAT, dan langsung ke intinya. Jangan bertele-tele."
        elif style == "Panjang & Detail":
            new_prompt = base + " Jawablah dengan PANJANG LEBAR, SANGAT DETAIL, dan berikan penjelasan mendalam untuk setiap langkah."
        else:
            new_prompt = base

        if self.messages and self.messages[0]["role"] == "system":
            self.messages[0]["content"] = new_prompt
        return True

    # ─── Helper: Strip qwen3 <think> tags ────────────────────────────────────
    @staticmethod
    def _strip_think_tags(text: str) -> str:
        """
        qwen3 dan model 'thinking' lainnya menyisipkan proses penalaran
        di dalam tag <think>...</think>. Strip tag ini dari output akhir
        sebelum ditampilkan ke pengguna.
        """
        import re
        # Hapus blok <think>...</think> beserta isinya
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
        return text.strip()

    # ─── Generate Respon (Agentic Loop) ──────────────────────────────────
    def generate_response(self, user_message, on_tool_call=None):
        """
        Agentic loop: terus memanggil AI hingga tidak ada lagi tool_calls.
        - on_tool_call: callback opsional fn(tool_name, args) untuk update UI.
        - Maksimum MAX_AGENT_ITERATIONS putaran untuk mencegah infinite loop.
        """
        self.messages.append({"role": "user", "content": user_message})

        try:
            temp  = float(self.settings_mgr.get("temperature"))
            max_tok = int(self.settings_mgr.get("max_tokens"))

            # ── Smart Tool Routing ──────────────────────────────────────────
            active_tools = self.tool_router.select(user_message)

            for iteration in range(MAX_AGENT_ITERATIONS):
                kwargs = {
                    "model":       self.model,
                    "messages":    self.messages,
                    "temperature": temp,
                    "max_tokens":  max_tok,
                }
                # Jangan kirim tools sama sekali jika kosong
                # (tools=None menyebabkan error pada beberapa versi Ollama)
                if active_tools:
                    kwargs["tools"] = active_tools

                response = self.client.chat.completions.create(**kwargs)
                response_message = response.choices[0].message
                self.messages.append(response_message)

                # ── Tidak ada tool call → AI sudah selesai ──
                if not response_message.tool_calls:
                    content = response_message.content or ""

                    # ── Tangani qwen3 <think>...</think> tags ──
                    # qwen3:4b menyisipkan proses berpikir dalam tag <think>
                    # Kita strip tag tersebut agar tidak tampil di UI
                    content = self._strip_think_tags(content)

                    return content if content.strip() else "Maaf, tidak ada jawaban yang dihasilkan."

                # ── Ada tool call → eksekusi semua, lanjut iterasi berikutnya ──
                for tool_call in response_message.tool_calls:
                    function_name = tool_call.function.name
                    try:
                        function_args = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        function_args = {}

                    if on_tool_call:
                        on_tool_call(function_name, function_args)

                    if not self.sandbox.validate_action(function_name, **function_args):
                        function_response = (
                            f"[SANDBOX BLOCKED] Pengguna tidak mengizinkan perintah "
                            f"'{function_name}' dengan argumen {function_args}."
                        )
                    else:
                        if function_name in self.tool_map:
                            try:
                                function_response = self.tool_map[function_name](**function_args)
                            except Exception as e:
                                function_response = f"[TOOL ERROR] {function_name}: {e}"
                        else:
                            function_response = f"[NOT FOUND] Fungsi '{function_name}' tidak terdaftar."

                    self.messages.append({
                        "role":        "tool",
                        "tool_call_id": tool_call.id,
                        "name":        function_name,
                        "content":     str(function_response),
                    })

            # Jika loop habis tanpa jawaban final
            final_response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages + [{"role": "user", "content": "Berikan laporan singkat hasil semua yang sudah dikerjakan."}],
                temperature=temp,
                max_tokens=max_tok,
            )
            content = final_response.choices[0].message.content or "Semua tugas selesai."
            return self._strip_think_tags(content)

        except Exception as e:
            if self.messages and self.messages[-1]["role"] == "user":
                self.messages.pop()

            return f"[ERROR ORCHID] Gagal berkomunikasi dengan AI ({self.model}): {str(e)}"
