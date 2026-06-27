# ORCHID - Ultimate Local AI Assistant Blueprint (.EXE Desktop App)

Dokumen ini adalah rancangan implementasi master (Master Blueprint) untuk **ORCHID**, sebuah proyek jangka panjang untuk membangun Asisten AI Desktop (*Super App*) yang berjalan secara lokal, aman, dan memiliki kapabilitas kontrol komputer secara penuh.

---

## Master Feature List (24 Core Modules)

Berikut adalah daftar lengkap fitur yang akan dikembangkan secara bertahap dalam proyek ORCHID:

### 🧠 1. AI Core
Mesin utama AI dengan obrolan offline multi-model (Qwen, Llama, Mistral, dll). Mendukung peralihan model tanpa *restart*, *Tool/Function Calling*, *Reasoning Mode* (Deep/Fast), kompresi konteks, dan memori jangka pendek/panjang menggunakan *Semantic Search* (Local RAG).

### 💻 2. Computer Control
Kontrol OS total: membuka/menutup aplikasi paksa, manajemen multi-monitor, kontrol virtual *mouse/keyboard*, dan *Screen Understanding* (mendeteksi dan berinteraksi dengan elemen UI, tombol, dan teks di layar).

### 📂 3. File System
Manajemen file tingkat lanjut: membaca, menulis, mengubah nama massal (*batch rename*), ekstrak/kompres ZIP, pencarian file duplikat/besar, hingga sinkronisasi dan penandaan (*tagging*) folder secara otomatis.

### 🔐 4. Permission System
Keamanan berbasis *Sandbox*. Pengguna dapat mengatur *Allow/Deny list* untuk folder, mendeteksi akses ke data sensitif, memblokir perintah berbahaya, dan memaksa dialog konfirmasi sebelum eksekusi (*Human-in-the-Loop*).

### 🖥️ 5. Terminal Assistant
Integrasi langsung ke CMD, PowerShell, Bash, dan WSL. ORCHID dapat menjalankan perintah terminal, menjelaskan maksud suatu perintah, memperbaiki pesan *error* otomatis, dan memonitor proses.

### 🌐 6. Browser Automation
Kendali *browser* (Chrome, Edge, Firefox) untuk membuka situs web, mengisi formulir, otomatisasi *login*, ekstraksi data (*scraping*, PDF, tabel), dan pengelolaan *cookie* serta *tab*.

### 👁️ 7. Computer Vision
Analisis layar secara langsung (*live screen*). Fitur meliputi OCR teks, deteksi wajah/objek dengan YOLO, pembacaan QR/Barcode, segmentasi UI, dan perbandingan gambar.

### 🎤 8. Voice Assistant
Interaksi suara 100% *offline*. Mendukung *Wake word* ("Hey ORCHID"), Speech-to-Text (STT), Text-to-Speech (TTS), pengenalan pembicara, hingga peredam bising (*Noise Suppression*).

### 🧑‍💻 9. Coding Assistant
Asisten *developer* pribadi untuk *generate* kode, *debug*, dan *refactor*. Bisa membuat *Unit Test*, merancang struktur *Database/Docker*, menulis *README*, dan membuat pesan *commit* Git secara otomatis.

### 📊 10. Office Assistant
Otomasi dokumen produktivitas. Mampu membuat/meringkas Word, merumuskan *Pivot/Chart* di Excel, membuat *slide* PowerPoint, hingga OCR dan penggabungan/kompresi PDF.

### 📈 11. Data Analysis
Analisis mendalam dari file CSV/Excel/SQL. Mendukung visualisasi data, regresi, *clustering*, *forecasting*, dan pembuatan laporan wawasan otomatis (*Auto Insight*).

### 🤖 12. AI Model Manager
Manajer bawaan untuk mengunduh, menghapus, atau melakukan *quantization* model AI. Memiliki panel pemantauan performa GPU, VRAM, RAM, CPU, dan alat *benchmark* model.

### 🧩 13. Plugin Marketplace
Ekosistem *plugin* komunitas. Pengguna dapat menginstal ekstensi alat tambahan melalui *Plugin SDK*, dijalankan dalam area *Sandbox* agar tetap aman.

### 🔄 14. Automation
Pembuatan *workflow* otomasi visual (*zapier-like*). Pengguna dapat membuat jadwal (scheduler) atau pemicu (*trigger*) untuk otomasi email, *folder watcher*, *auto backup*, dan pembersihan rutin.

### 🗂️ 15. Project Manager
Manajemen proyek terintegrasi Git, fitur daftar tugas (*TODO*), *timeline*, catatan rapat, dan templat *workspace* yang bisa disesuaikan dengan alur kerja.

### 🧠 16. Memory
Kemampuan ORCHID untuk mengingat preferensi Anda, letak proyek, gaya penulisan kode, dengan kapabilitas pencarian memori historis (*Timeline Memory*) dan hak untuk menghapus ingatan (*Forget Memory*).

### 📦 17. Package Manager
Manajemen *environment* terpusat. Menginstal dan mengelola pustaka Python, Node, Java, Rust, Go, Docker, dan CUDA tanpa perlu membuka terminal terpisah.

### 🛠️ 18. Developer Tools
Kumpulan perkakas *developer* internal: *Client* REST API/GraphQL, *Database Viewer*, FTP/SSH client, integrasi Kubernetes/Docker, dan koneksi langsung ke VSCode.

### 📡 19. Monitoring
Dashboard pemantauan status komputer (*Real-time*): Suhu perangkat, penggunaan jaringan (*Internet Speed*), CPU, GPU, sisa baterai, dan proses yang sedang berjalan.

### 🛡️ 20. Security
Sistem keamanan proaktif untuk memindai *Malware*, mendeteksi perintah mencurigakan/ransowmare, menyensor kata sandi (*Password Masking*), dan melindungi API/SSH Key (*Secret Scanner*).

### 🎨 21. UI (User Interface)
Tampilan CustomTkinter berestetika modern: *Acrylic Blur*, *Light/Dark Mode*, widget yang dapat ditarik (*Drag & Drop*), *Command Palette*, dan mode asisten melayang (*Floating* / *Dock mode*).

### ☁️ 22. Cloud (Opsional)
Integrasi pihak ketiga (API) ke layanan *Cloud* seperti Google Drive, OneDrive, Notion, GitLab/GitHub, Discord, dan Slack.

### 📜 23. History & Logs
Penyimpanan arsip aktivitas: Riwayat obrolan, riwayat perintah OS, riwayat *browser*, *error log*, dan log ringkasan alasan AI (*AI reasoning log*) untuk keperluan audit.

### ⚙️ 24. Settings
Panel kendali sentral untuk mengubah konfigurasi: Batas memori AI, aturan perizinan (*Permission rules*), kustomisasi jalan pintas keyboard (*Shortcut manager*), bahasa, dan *Backup/Restore* konfigurasi.

---

## Strategi Implementasi Jangka Panjang

Mengingat skalanya yang sangat masif, proyek ini akan menggunakan **Arsitektur Modular (Plugin-based)**. Core AIOS dan UI akan dibangun terlebih dahulu (Modul 1, 4, dan 21), kemudian fitur lain (seperti Computer Vision, Office, Voice) akan ditambahkan sebagai skrip modul terpisah yang saling berkomunikasi.
