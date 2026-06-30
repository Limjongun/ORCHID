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

# ─── Konfigurasi Backend ────────────────────────────────────────────
OLLAMA_BASE_URL  = "http://localhost:11434/v1"
AZURE_BASE_URL   = "https://models.inference.ai.azure.com"

SYSTEM_PROMPT = """
Kamu adalah ORCHID, asisten AI desktop canggih yang berjalan langsung di komputer pengguna.

=== ATURAN WAJIB (TIDAK BOLEH DILANGGAR) ===

1. JANGAN PERNAH memberi instruksi manual kepada pengguna. Selalu eksekusi langsung menggunakan tools.
2. Selalu jawab dalam Bahasa Indonesia kecuali pengguna meminta bahasa lain.
3. Untuk tugas multi-langkah, eksekusi tools satu per satu secara berurutan TANPA menunggu konfirmasi.
4. Setelah semua tool selesai, baru berikan laporan singkat kepada pengguna.

=== PANDUAN PEMILIHAN TOOL (ROUTING) ===

PENCARIAN INTERNET / INFO TERBARU:
  → Gunakan: search_duckduckgo(query)
  → JANGAN pakai: keyboard_hotkey, open_website, atau cara browser manual

MEMBUKA WEBSITE:
  → Gunakan: open_website(url)
  → JANGAN pakai: keyboard_hotkey win+r, atau keyboard_type

MEMBUAT / MENULIS FILE:
  → Gunakan: write_file(file_path, content)
  → JANGAN tampilkan kode ke chat

MEMBUAT FOLDER:
  → Gunakan: create_directory(dir_path)

MENJALANKAN PERINTAH SHELL / TERMINAL:
  → Gunakan: execute_powershell(command)

MEMBACA DOKUMEN (PDF/Word/Excel):
  → Gunakan: read_pdf / read_docx / read_excel

INFO HARDWARE / SISTEM:
  → Gunakan: get_system_info atau get_hardware_info

MOUSE & KEYBOARD (input_control):
  → HANYA gunakan jika pengguna secara eksplisit meminta otomatisasi UI
    (misal: "klik tombol di aplikasi X", "ketikkan teks di Notepad")
  → JANGAN pakai untuk pencarian internet, membuka website, atau tugas
    yang sudah punya tool khusus di atas

=== HIERARKI PRIORITAS TOOL ===
Tool khusus (search_duckduckgo, write_file, dll) > execute_powershell > mouse/keyboard
"""

MAX_AGENT_ITERATIONS = 15  # Batas maksimum putaran tool calling agar tidak infinite loop

class ChatEngine:
    def __init__(self):
        load_dotenv()
        self.token_1 = os.environ.get("GITHUB_TOKEN_1") or os.environ.get("GITHUB_TOKEN")
        self.token_2 = os.environ.get("GITHUB_TOKEN_2")
        self.sandbox = SecuritySandbox()

        # Gabungkan semua Tools dari Plugins
        self.tools = (
            SYSTEM_TOOLS + GIT_TOOLS + FILE_TOOLS +
            HARDWARE_TOOLS + WEB_TOOLS + TERMINAL_TOOLS +
            INPUT_TOOLS + OFFICE_TOOLS
        )
        self.tool_map = {
            **SYSTEM_TOOL_MAP, **GIT_TOOL_MAP, **FILE_TOOL_MAP,
            **HARDWARE_TOOL_MAP, **WEB_TOOL_MAP, **TERMINAL_TOOL_MAP,
            **INPUT_TOOL_MAP, **OFFICE_TOOL_MAP
        }

        # Default: coba Ollama lokal dulu, fallback ke Azure jika ada token
        self._init_ollama()

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
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # ─── Pergantian Model dari UI ────────────────────────────────────
    def switch_account(self, account_index):
        """
        1 → Ollama qwen2.5 (lokal)
        2 → Azure GPT-4o Akun 1
        3 → Azure GPT-4o Akun 2
        """
        if account_index == 1:
            self._init_ollama("qwen2.5:latest")
            return True
        elif account_index == 2:
            if not self.token_1:
                return False
            self._init_azure(self.token_1, "gpt-4o")
            return True
        elif account_index == 3:
            if not self.token_2:
                return False
            self._init_azure(self.token_2, "gpt-4o")
            return True
        return False

    # ─── Gaya Bicara ─────────────────────────────────────────────────
    def set_speaking_style(self, style):
        base = SYSTEM_PROMPT
        if style == "Singkat & Padat":
            new_prompt = base + " Jawablah dengan SANGAT SINGKAT, PADAT, dan langsung ke intinya. Jangan bertele-tele."
        elif style == "Panjang & Detail":
            new_prompt = base + " Jawablah dengan PANJANG LEBAR, SANGAT DETAIL, dan berikan penjelasan mendalam untuk setiap langkah."
        else:
            new_prompt = base

        if self.messages and self.messages[0]["role"] == "system":
            self.messages[0]["content"] = new_prompt
        return True

    # ─── Generate Respon (Agentic Loop) ──────────────────────────────────
    def generate_response(self, user_message, on_tool_call=None):
        """
        Agentic loop: terus memanggil AI hingga tidak ada lagi tool_calls.
        - on_tool_call: callback opsional fn(tool_name, args) untuk update UI.
        - Maksimum MAX_AGENT_ITERATIONS putaran untuk mencegah infinite loop.
        """
        self.messages.append({"role": "user", "content": user_message})

        try:
            for iteration in range(MAX_AGENT_ITERATIONS):
                kwargs = {
                    "model": self.model,
                    "messages": self.messages,
                    "temperature": 0.7,
                    "max_tokens": 2048,
                    "tools": self.tools,
                }

                response = self.client.chat.completions.create(**kwargs)
                response_message = response.choices[0].message
                self.messages.append(response_message)

                # ── Tidak ada tool call → AI sudah selesai, kembalikan jawaban ──
                if not response_message.tool_calls:
                    return response_message.content or "Maaf, respons kosong."

                # ── Ada tool call → eksekusi semua, lanjut iterasi berikutnya ──
                for tool_call in response_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)

                    # Notifikasi ke UI (opsional)
                    if on_tool_call:
                        on_tool_call(function_name, function_args)

                    # Validasi Sandbox
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
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": str(function_response),
                    })

            # Jika loop habis tanpa jawaban final, minta ringkasan
            final_response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages + [{"role": "user", "content": "Berikan laporan singkat hasil semua yang sudah dikerjakan."}],
                temperature=0.7,
                max_tokens=1024,
            )
            return final_response.choices[0].message.content or "Semua tugas selesai."

        except Exception as e:
            if self.messages and self.messages[-1]["role"] == "user":
                self.messages.pop()
            return f"[ERROR ORCHID] Gagal berkomunikasi dengan AI ({self.model}): {str(e)}"
