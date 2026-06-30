"""
tool_router.py — Smart Tool Router (Dynamic Tool Selection)
Mengklasifikasikan intent pesan pengguna dan memilih hanya tool group
yang relevan untuk dikirim ke Ollama, mengurangi token overhead ~80-85%.

Algoritma: Pure keyword/pattern heuristic — zero latency, no second AI call.
"""
import re
from typing import Optional

from plugins.system_control import SYSTEM_TOOLS
from plugins.git_control import GIT_TOOLS
from plugins.file_explorer import FILE_TOOLS
from plugins.hardware_info import HARDWARE_TOOLS
from plugins.web_network import WEB_TOOLS
from plugins.terminal_control import TERMINAL_TOOLS
from plugins.input_control import INPUT_TOOLS
from plugins.office_tools import OFFICE_TOOLS
from plugins.code_assistant import CODE_TOOLS

# ─── Tool Groups Registry ────────────────────────────────────────────────────
TOOL_GROUPS = {
    "coding":   CODE_TOOLS,
    "files":    FILE_TOOLS,
    "git":      GIT_TOOLS,
    "web":      WEB_TOOLS,
    "system":   SYSTEM_TOOLS,
    "hardware": HARDWARE_TOOLS,
    "terminal": TERMINAL_TOOLS,
    "office":   OFFICE_TOOLS,
    "input":    INPUT_TOOLS,
}

# Tools yang SELALU disertakan karena sering dibutuhkan sebagai pendukung
CORE_TOOLS = [
    t for t in FILE_TOOLS
    if t["function"]["name"] in ("write_file", "read_file", "create_directory", "list_directory")
] + [
    t for t in SYSTEM_TOOLS
    if t["function"]["name"] in ("get_system_info", "open_application")
]

# ─── Keyword Maps ─────────────────────────────────────────────────────────────
# Setiap entry adalah (list_kata_kunci, nama_grup)
# Urutan dari atas ke bawah = prioritas pencocokan
_KEYWORD_RULES: list[tuple[list[str], str]] = [
    # Coding & Debugging
    ([
        "debug", "error", "traceback", "syntax", "bug", "fungsi", "function",
        "class", "kelas", "import", "pytest", "test", "unittest", "coverage",
        "analisis kode", "analisis file", "analisis proyek", "lint", "refactor",
        "run code", "jalankan kode", "eksekusi kode", "python code", "kode python",
        "script", "snippet", "repl", "variabel", "output kode", "compile",
        "kompleksitas", "cyclomatic", "ast", "index proyek", "struktur proyek",
        "dependency", "todo", "fixme", "backup kode", "restore kode",
        "ganti fungsi", "replace function", "patch", "diff",
    ], "coding"),

    # File & Folder Management
    ([
        "buat file", "buat folder", "hapus file", "hapus folder", "buat direktori",
        "create file", "create folder", "delete file", "mkdir", "rename",
        "pindahkan", "move", "copy", "salin", "zip", "compress", "extract",
        "buka file", "read file", "tulis file", "write file", "list folder",
        "tampilkan isi", "direktori", "path", "folder",
    ], "files"),

    # Git & Version Control
    ([
        "git", "commit", "push", "pull", "merge", "branch", "checkout",
        "repository", "repo", "clone", "status git", "log git", "diff git",
        "staged", "unstaged", "stash", "rebase",
    ], "git"),

    # Web & Internet
    ([
        "cari di internet", "search", "googling", "cari informasi", "berita",
        "terbaru", "website", "buka web", "open url", "browse", "duckduckgo",
        "download info", "cek website", "ping", "ip address", "jaringan",
        "network", "koneksi internet",
    ], "web"),

    # System & OS Control
    ([
        "screenshot", "volume", "mute", "shutdown", "restart", "sleep",
        "hibernate", "buka aplikasi", "tutup aplikasi", "kill process",
        "open app", "close app", "proses", "process", "task manager",
        "layar", "screen",
    ], "system"),

    # Hardware Info
    ([
        "cpu", "ram", "gpu", "memory", "disk", "storage", "processor",
        "hardware", "suhu", "temperature", "driver", "spesifikasi", "spec",
        "benchmark", "vram", "performa sistem",
    ], "hardware"),

    # Terminal & Shell
    ([
        "powershell", "cmd", "terminal", "command", "shell", "bash",
        "jalankan perintah", "run command", "execute", "eksekusi perintah",
        "install", "pip install", "npm", "script shell",
    ], "terminal"),

    # Office & Documents
    ([
        "pdf", "word", "excel", "docx", "xlsx", "csv", "spreadsheet",
        "dokumen", "document", "baca pdf", "buka word", "buka excel",
        "tabel", "laporan", "report",
    ], "office"),

    # Input Control (RPA)
    ([
        "klik", "click", "mouse", "keyboard", "ketik di", "type in",
        "otomasi ui", "ui automation", "drag", "scroll", "shortcut",
        "hotkey", "gerakkan mouse",
    ], "input"),
]

# ─── Regex Patterns (lebih akurat untuk pola struktural) ─────────────────────
_PATTERN_RULES: list[tuple[re.Pattern, str]] = [
    (re.compile(r'\.(py|pyx|pyi)\b', re.I),       "coding"),
    (re.compile(r'\.(docx?|xlsx?|csv|pdf)\b', re.I), "office"),
    (re.compile(r'https?://', re.I),               "web"),
    (re.compile(r'\bgit\s+\w+', re.I),             "git"),
    (re.compile(r'def\s+\w+|class\s+\w+|import\s+\w+', re.I), "coding"),
    (re.compile(r'powershell|\.ps1\b', re.I),      "terminal"),
]

# Kata kunci untuk pesan non-teknis (percakapan biasa)
_CASUAL_KEYWORDS = {
    "halo", "hai", "hi", "hello", "apa kabar", "selamat", "terima kasih",
    "thanks", "ok", "oke", "baik", "siap", "lanjut", "ya", "tidak",
    "bagaimana", "apa itu", "jelaskan", "ceritakan", "tolong", "bantu",
}

# Minimal tools untuk percakapan biasa (tidak ada tool call yang diperlukan)
_CASUAL_TOOLS: list = []   # Kosong → AI cukup menjawab dengan text


class ToolRouter:
    """
    Classifier berbasis keyword untuk memilih tool group yang relevan
    berdasarkan pesan pengguna. Zero latency, no external dependency.
    """

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self._compile_keywords()

    def _compile_keywords(self):
        """Pre-compile semua keyword rules menjadi regex untuk efisiensi."""
        self._compiled_keyword_rules: list[tuple[re.Pattern, str]] = []
        for keywords, group in _KEYWORD_RULES:
            # Gabungkan semua keyword menjadi satu pattern OR
            pattern_str = "|".join(re.escape(kw) for kw in keywords)
            compiled = re.compile(rf'\b(?:{pattern_str})\b', re.I | re.UNICODE)
            self._compiled_keyword_rules.append((compiled, group))

    def select(self, message: str) -> list:
        """
        Analisis pesan dan kembalikan daftar tools yang relevan.
        Selalu menyertakan CORE_TOOLS sebagai fondasi.

        Returns:
            list: Daftar tool schema siap dikirim ke Ollama.
        """
        matched_groups = set()

        # ── Lapisan 1: Keyword matching ──
        for pattern, group in self._compiled_keyword_rules:
            if pattern.search(message):
                matched_groups.add(group)

        # ── Lapisan 2: Regex pattern matching ──
        for pattern, group in _PATTERN_RULES:
            if pattern.search(message):
                matched_groups.add(group)

        # ── Lapisan 3: Fallback logic ──
        is_casual = self._is_casual_message(message)

        if not matched_groups and is_casual:
            # Percakapan biasa → tidak perlu tools sama sekali
            selected_tools = []
            if self.verbose:
                print(f"[ToolRouter] CASUAL -> 0 tools")
        elif not matched_groups:
            # Pesan teknis tapi tidak terklasifikasi → kirim semua (safe fallback)
            selected_tools = self._get_all_tools()
            if self.verbose:
                print(f"[ToolRouter] FALLBACK -> {len(selected_tools)} tools (semua)")
        else:
            # Build selected tools dari grup yang match
            tools_set = list(CORE_TOOLS)  # Selalu sertakan core
            seen_names = {t["function"]["name"] for t in CORE_TOOLS}

            for group in matched_groups:
                for tool in TOOL_GROUPS.get(group, []):
                    name = tool["function"]["name"]
                    if name not in seen_names:
                        tools_set.append(tool)
                        seen_names.add(name)

            selected_tools = tools_set
            if self.verbose:
                print(f"[ToolRouter] Groups: {matched_groups} -> {len(selected_tools)} tools")

        return selected_tools

    def _is_casual_message(self, message: str) -> bool:
        """Deteksi apakah pesan adalah percakapan biasa tanpa intent teknis."""
        msg_lower = message.lower().strip()
        # Pesan sangat pendek (< 5 kata) dan mengandung kata santai
        words = set(msg_lower.split())
        casual_overlap = words & _CASUAL_KEYWORDS
        is_short = len(message.split()) <= 6
        return bool(casual_overlap) and is_short

    def _get_all_tools(self) -> list:
        """Kembalikan semua tools (safe fallback)."""
        all_tools = []
        seen = set()
        for tools_list in TOOL_GROUPS.values():
            for tool in tools_list:
                name = tool["function"]["name"]
                if name not in seen:
                    all_tools.append(tool)
                    seen.add(name)
        return all_tools

    def describe(self, message: str) -> dict:
        """Debug helper: tampilkan detail seleksi tanpa mengembalikan tools."""
        old_verbose = self.verbose
        self.verbose = True
        selected = self.select(message)
        self.verbose = old_verbose
        return {
            "message": message,
            "tools_count": len(selected),
            "tool_names": [t["function"]["name"] for t in selected]
        }
