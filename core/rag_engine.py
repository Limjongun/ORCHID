"""
rag_engine.py — Retrieval-Augmented Generation Engine
Retrieval berbasis TF-IDF manual (tanpa dependency eksternal).
Mengindeks dokumen proyek ORCHID dan menyuntikkan konteks relevan
ke dalam prompt sebelum dikirim ke Ollama.
"""
import os
import re
import json
import math
from typing import Optional

ROOT_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_PATH = os.path.join(ROOT_DIR, "data", "rag_index.json")

# ─── Sumber Dokumen yang Akan Diindeks ───────────────────────────────────────
KNOWLEDGE_SOURCES = [
    # Dokumentasi Markdown
    os.path.join(ROOT_DIR, "README.md"),
    os.path.join(ROOT_DIR, "ORCHID_dokumentasi.md"),
    os.path.join(ROOT_DIR, "architecture.md"),
    os.path.join(ROOT_DIR, "core(kerjakan dulu).md"),
    os.path.join(ROOT_DIR, "ui_concept.md"),
]

# Deskripsi statis tentang ORCHID yang selalu dimasukkan ke index
ORCHID_STATIC_KNOWLEDGE = """
ORCHID adalah asisten AI desktop lokal berbasis Python yang berjalan menggunakan Ollama.
ORCHID menggunakan CustomTkinter sebagai antarmuka grafis dan mendukung multi-model Ollama.
ORCHID memiliki agentic loop yang dapat memanggil tools secara berulang (maks 15 iterasi).

ORCHID memiliki 9 plugin dengan total lebih dari 83 tools:
1. System Control (system_control.py): Screenshot, volume, shutdown, manajemen aplikasi dan proses.
2. File Explorer (file_explorer.py): Buat, baca, hapus, pindahkan, rename, zip file dan folder.
3. Git Control (git_control.py): Commit, push, pull, branch, status, log Git.
4. Hardware Info (hardware_info.py): Info CPU, RAM, GPU, disk, suhu, performa sistem.
5. Web & Network (web_network.py): Pencarian DuckDuckGo, buka URL, cek koneksi internet.
6. Terminal Control (terminal_control.py): Eksekusi perintah PowerShell dan shell.
7. Input Control (input_control.py): Otomasi mouse dan keyboard (RPA), klik, ketik, shortcut.
8. Office Tools (office_tools.py): Baca dan tulis PDF, Word (docx), Excel (xlsx), CSV.
9. Code Assistant (code_assistant/): Plugin coding kompleks dengan 5 sub-modul dan 28 tools:
   - Executor: Jalankan kode Python di venv terisolasi, REPL persisten dengan memori variabel.
   - Analyzer: Analisis AST, linting pyflakes, code metrics, kompleksitas siklomatik, deteksi TODO.
   - Context Engine: Index proyek, pencarian kode lintas-file, pohon direktori, dependency graph.
   - Diff Engine: Edit kode secara presisi per-fungsi, backup/restore otomatis.
   - Test Runner: Jalankan pytest, parse hasil, generate template test, laporan coverage.

Smart Tool Router: Sebelum mengirim request ke Ollama, ORCHID mengklasifikasikan intent pesan
menggunakan keyword matching untuk memilih hanya tools yang relevan (menghemat ~80% token).

RAG Engine: ORCHID menggunakan TF-IDF retrieval untuk menjawab pertanyaan tentang dirinya sendiri
dengan akurat berdasarkan dokumen proyek.

Model yang didukung: qwen3:4b (default), qwen2.5:latest, gemma4:latest (semua via Ollama lokal),
serta Azure GPT-4o via GitHub Models API.

Security Sandbox: Setiap aksi berbahaya (hapus file, eksekusi skrip, dll.) meminta konfirmasi
pengguna sebelum dieksekusi.

Settings yang bisa dikonfigurasi: Temperature, Max Tokens, System Prompt, Theme.
"""


# ─── TF-IDF Manual Implementation ────────────────────────────────────────────

def _tokenize(text: str) -> list[str]:
    """Tokenisasi teks menjadi list kata (lowercase, hanya huruf/angka)."""
    text = text.lower()
    # Ganti karakter khusus markdown
    text = re.sub(r"[#*`>\[\]()_\-=|\\]", " ", text)
    tokens = re.findall(r"\b[a-z0-9][a-z0-9]+\b", text)
    # Stopwords Bahasa Indonesia & Inggris sederhana
    stop = {
        "dan", "atau", "yang", "ini", "itu", "dengan", "untuk", "dari",
        "ke", "di", "ada", "adalah", "pada", "tidak", "jika", "maka",
        "the", "and", "or", "is", "in", "of", "to", "a", "an", "for",
        "with", "as", "at", "by", "be", "it", "its", "are", "was",
        "that", "this", "have", "has", "can", "will", "not", "but",
    }
    return [t for t in tokens if t not in stop and len(t) > 1]


def _compute_tf(tokens: list[str]) -> dict[str, float]:
    tf: dict[str, float] = {}
    total = len(tokens) or 1
    for t in tokens:
        tf[t] = tf.get(t, 0) + 1
    return {k: v / total for k, v in tf.items()}


def _cosine_similarity(vec_a: dict, vec_b: dict) -> float:
    keys = set(vec_a) & set(vec_b)
    if not keys:
        return 0.0
    dot = sum(vec_a[k] * vec_b[k] for k in keys)
    mag_a = math.sqrt(sum(v ** 2 for v in vec_a.values()))
    mag_b = math.sqrt(sum(v ** 2 for v in vec_b.values()))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


# ─── RAGEngine ────────────────────────────────────────────────────────────────

class RAGEngine:
    """
    Engine RAG berbasis TF-IDF untuk proyek ORCHID.
    Retrieval latensi < 10ms, tanpa dependency eksternal.
    """

    def __init__(self):
        self.chunks: list[dict] = []   # {"text": str, "source": str, "tf": dict}
        self.idf: dict[str, float] = {}
        self._build_index()

    def _build_index(self):
        """Scan semua sumber, chunk, dan build TF-IDF index."""
        raw_chunks: list[dict] = []

        # ── 1. Static ORCHID knowledge ──
        for chunk_text in self._split_into_chunks(ORCHID_STATIC_KNOWLEDGE, source="ORCHID Built-in Knowledge"):
            raw_chunks.append(chunk_text)

        # ── 2. Dokumen Markdown dari filesystem ──
        for fpath in KNOWLEDGE_SOURCES:
            if not os.path.isfile(fpath):
                continue
            try:
                with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                source_name = os.path.basename(fpath)
                for chunk in self._split_into_chunks(content, source=source_name):
                    raw_chunks.append(chunk)
            except Exception:
                pass

        # ── 3. Deskripsi tools dari semua plugin ──
        try:
            tool_descriptions = self._extract_tool_descriptions()
            for chunk in self._split_into_chunks(tool_descriptions, source="Plugin Tool Descriptions"):
                raw_chunks.append(chunk)
        except Exception:
            pass

        if not raw_chunks:
            return

        # ── Build TF-IDF ──
        all_tokens_per_chunk = []
        for chunk in raw_chunks:
            tokens = _tokenize(chunk["text"])
            chunk["tokens"] = tokens
            chunk["tf"] = _compute_tf(tokens)
            all_tokens_per_chunk.append(set(tokens))

        # IDF = log(N / df) di mana df = jumlah chunk yang mengandung term
        N = len(raw_chunks)
        vocab: set[str] = set()
        for token_set in all_tokens_per_chunk:
            vocab |= token_set

        for term in vocab:
            df = sum(1 for ts in all_tokens_per_chunk if term in ts)
            self.idf[term] = math.log((N + 1) / (df + 1)) + 1  # smoothed IDF

        # TF-IDF vector per chunk
        for chunk in raw_chunks:
            tfidf = {t: chunk["tf"].get(t, 0) * self.idf.get(t, 0) for t in chunk["tf"]}
            chunk["tfidf"] = tfidf

        # Simpan ke self.chunks (hapus field sementara)
        self.chunks = []
        for chunk in raw_chunks:
            self.chunks.append({
                "text":   chunk["text"],
                "source": chunk["source"],
                "tfidf":  chunk["tfidf"],
            })

        # Persist index ke disk (opsional, untuk debug)
        try:
            os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)
            summary = {
                "chunk_count": len(self.chunks),
                "vocab_size": len(self.idf),
                "sources": list({c["source"] for c in self.chunks}),
            }
            with open(INDEX_PATH, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def _split_into_chunks(self, text: str, source: str, max_words: int = 180) -> list[dict]:
        """
        Potong teks menjadi chunk ~180 kata dengan overlap 20 kata.
        Prioritaskan batas paragraf (baris kosong).
        """
        # Split per paragraf
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        chunks = []
        current_words: list[str] = []
        current_text_parts: list[str] = []

        for para in paragraphs:
            words = para.split()
            if len(current_words) + len(words) <= max_words:
                current_words.extend(words)
                current_text_parts.append(para)
            else:
                # Simpan chunk saat ini
                if current_text_parts:
                    chunks.append({"text": "\n\n".join(current_text_parts), "source": source})
                # Mulai chunk baru dengan overlap
                overlap = current_words[-20:] if len(current_words) >= 20 else current_words[:]
                current_words = overlap + words
                current_text_parts = [para]

        if current_text_parts:
            chunks.append({"text": "\n\n".join(current_text_parts), "source": source})

        return chunks

    def _extract_tool_descriptions(self) -> str:
        """Ekstrak deskripsi tools dari semua plugin menggunakan import dinamis."""
        descriptions = []
        try:
            from plugins.system_control import SYSTEM_TOOLS
            from plugins.git_control import GIT_TOOLS
            from plugins.file_explorer import FILE_TOOLS
            from plugins.hardware_info import HARDWARE_TOOLS
            from plugins.web_network import WEB_TOOLS
            from plugins.terminal_control import TERMINAL_TOOLS
            from plugins.input_control import INPUT_TOOLS
            from plugins.office_tools import OFFICE_TOOLS
            from plugins.code_assistant import CODE_TOOLS

            all_plugin_tools = (
                SYSTEM_TOOLS + GIT_TOOLS + FILE_TOOLS + HARDWARE_TOOLS +
                WEB_TOOLS + TERMINAL_TOOLS + INPUT_TOOLS + OFFICE_TOOLS + CODE_TOOLS
            )
            for tool in all_plugin_tools:
                fn = tool.get("function", {})
                name = fn.get("name", "")
                desc = fn.get("description", "")
                if name and desc:
                    descriptions.append(f"Tool '{name}': {desc}")
        except Exception:
            pass
        return "\n".join(descriptions)

    def retrieve(self, query: str, top_k: int = 3) -> list[dict]:
        """
        Ambil top_k chunk paling relevan untuk query.
        Returns: list of {"text": str, "source": str, "score": float}
        """
        if not self.chunks:
            return []

        query_tokens = _tokenize(query)
        query_tf = _compute_tf(query_tokens)
        query_tfidf = {t: query_tf.get(t, 0) * self.idf.get(t, 0) for t in query_tf}

        scored = []
        for chunk in self.chunks:
            score = _cosine_similarity(query_tfidf, chunk["tfidf"])
            if score > 0:
                scored.append({
                    "text":   chunk["text"],
                    "source": chunk["source"],
                    "score":  round(score, 4),
                })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    def augment_prompt(self, query: str, top_k: int = 3) -> str:
        """
        Kembalikan string konteks siap pakai untuk disisipkan ke system message.
        Format: blok teks yang berisi chunk-chunk paling relevan.
        """
        results = self.retrieve(query, top_k=top_k)
        if not results:
            return ""

        lines = ["=== KONTEKS PROYEK ORCHID ==="]
        for i, r in enumerate(results, 1):
            lines.append(f"[{i}] (Sumber: {r['source']})")
            lines.append(r["text"])
            lines.append("")

        lines.append("Gunakan konteks di atas untuk menjawab pertanyaan pengguna dengan akurat.")
        return "\n".join(lines)

    def index_stats(self) -> dict:
        """Kembalikan statistik index RAG untuk debug/monitoring."""
        return {
            "chunk_count": len(self.chunks),
            "vocab_size": len(self.idf),
            "sources": list({c["source"] for c in self.chunks}),
            "index_file": INDEX_PATH,
        }


# ─── Kata kunci yang memicu RAG (pesan self-referential tentang ORCHID) ───────
ORCHID_KEYWORDS = re.compile(
    r"\b("
    r"orchid|kamu bisa|apa yang bisa|kemampuan|fitur|plugin|tools?|tool\b|"
    r"jelaskan tentang|cara kerja|apa itu|diri kamu|dirimu|tentang kamu|"
    r"siapa kamu|kamu itu|kamu adalah|kamu punya|fungsi kamu|"
    r"apa saja|apa aja|list|daftar|sebutkan|"
    r"sandbox|router|rag|agentic|loop|repl|venv|executor|analyzer|"
    r"context.?engine|diff.?engine|test.?runner|code.?assistant"
    r")\b",
    re.IGNORECASE
)


def is_orchid_query(message: str) -> bool:
    """True jika pesan adalah pertanyaan tentang ORCHID itu sendiri."""
    return bool(ORCHID_KEYWORDS.search(message))
