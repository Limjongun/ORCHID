# Arsitektur Modular ORCHID (Plugin-based System)

Dokumen ini menjelaskan rancangan arsitektur teknis agar proyek skala besar (24 Modul) dapat dikembangkan secara rapi, aman, dan ringan saat dibundel ke `.exe`.

---

## 1. Konsep Inti (The Core vs The Plugins)
Karena besarnya skala ORCHID, aplikasi ini tidak boleh ditulis dalam satu file Python raksasa. ORCHID akan dibagi menjadi dua bagian utama:
1. **The Core (Inti):** Sangat ringan dan stabil. Bertugas menjalankan UI, menghubungkan ke LLM (AI), menjaga keamanan (Sandbox), dan menjadi "Router".
2. **The Plugins (Modul Ekstensi):** Semua 24 fitur (Computer Vision, Browser Automation, File System, dll) diperlakukan sebagai Plugin independen. Jika ada satu plugin yang *error*, aplikasi ORCHID tidak akan *crash*.

---

## 2. Struktur Direktori Proyek

Ini adalah struktur folder yang direkomendasikan saat kita mulai menulis kode:

```text
ORCHID_Project/
│
├── core/                   # Logika sistem inti (Fundamental)
│   ├── llm_engine.py       # Koneksi ke Ollama / API
│   ├── memory.py           # Database SQLite untuk chat
│   ├── sandbox.py          # Sistem keamanan (Whitelist/Blacklist path)
│   └── router.py           # Pengarah tugas (Tool caller)
│
├── ui/                     # Antarmuka Pengguna (CustomTkinter)
│   ├── app.py              # File utama pembentuk GUI
│   ├── components/         # Tombol, Chat bubble, Sidebar
│   └── theme/              # Warna Dark/Light mode
│
├── plugins/                # Tempat ke-24 modul fitur berada
│   ├── 01_file_system/     # Modul untuk rename, copy, hapus file
│   ├── 02_sys_control/     # Modul mengatur Volume, Baterai, Buka Aplikasi
│   ├── 03_web_browser/     # Modul buka Chrome, scraping
│   ├── 04_vision/          # Modul deteksi layar
│   └── ... (plugin lain ditambahkan bertahap)
│
├── data/                   # Data lokal pengguna
│   ├── memory.db           # Ingatan AI
│   └── security.json       # Aturan Sandbox
│
├── requirements.txt        # Daftar library Python
└── main.py                 # Titik masuk eksekusi (Entry point ke .exe)
```

---

## 3. Siklus Hidup Eksekusi (Lifecycle)

Mari kita ambil contoh saat Anda mengetik: **"Tolong carikan file bernama laporan.pdf di drive D dan rangkum isinya."**

1. **Input (UI):** Pesan Anda dikirim dari `ui/app.py` ke `core/llm_engine.py`.
2. **Reasoning (Core LLM):** AI berpikir dan memutuskan ia butuh 2 alat: *File Search Tool* dan *Summarizer Tool*.
3. **Routing (Router):** `core/router.py` mencari plugin yang relevan di folder `plugins/`.
4. **Validasi (Sandbox):** Sebelum mengeksekusi pencarian di Drive D, `core/sandbox.py` akan mengecek `security.json`. Apakah Drive D ada di Blacklist? Jika aman, lanjut.
5. **Eksekusi (Plugin):** `plugins/01_file_system` bekerja membaca file `.pdf` tersebut.
6. **Respons (UI):** LLM merangkum teks dari plugin dan menampilkannya kembali ke jendela obrolan CustomTkinter Anda.

Dengan arsitektur ini, Anda bisa menambah fitur serumit apa pun di masa depan hanya dengan membuat folder baru di dalam `plugins/` tanpa merusak *Core System*!
