# 🌸 ORCHID — Dokumentasi Lengkap Proyek
**Versi:** 0.3.0-dev  
**Terakhir diperbarui:** 30 Juni 2026  
**Stack:** Python 3.11 · CustomTkinter · Ollama (qwen2.5) · OpenAI-compatible API

---

## 📐 Arsitektur Sistem

```
ORCHID/
├── main.py                  # Entry point aplikasi
├── core/
│   ├── llm_engine.py        # Mesin AI + Agentic Loop (maks 15 iterasi)
│   └── sandbox.py           # Security Sandbox (validasi pop-up)
├── plugins/                 # Semua tool calling ada di sini
│   ├── file_explorer.py
│   ├── system_control.py
│   ├── hardware_info.py
│   ├── git_control.py
│   ├── web_network.py
│   ├── terminal_control.py
│   ├── input_control.py
│   └── office_tools.py
├── ui/
│   └── app.py               # Antarmuka CustomTkinter
├── data/
│   └── security.json        # Konfigurasi whitelist sandbox
└── requirements.txt
```

### Alur Kerja Agentic Loop

```
User Input
    ↓
llm_engine.generate_response()
    ↓
[LOOP maks 15x]
    ├─ Panggil AI (Ollama / Azure)
    ├─ AI returns tool_calls?
    │       ├─ YES → Sandbox.validate_action()
    │       │           ├─ Ditolak → kirim pesan blokir ke AI
    │       │           └─ Diizinkan → eksekusi tool → hasilnya masuk messages
    │       │         (lanjut iterasi berikutnya)
    │       └─ NO  → Kembalikan teks jawaban ke UI
    ↓
UI menghapus loading bubble → tampilkan jawaban
```

---

## 🤖 Core Engine (`core/llm_engine.py`)

### Backend yang Didukung
| Slot | Backend | Model | Token Diperlukan |
|---|---|---|---|
| 1 (Default) | 🤖 Ollama Lokal | `qwen2.5:latest` | ❌ Tidak |
| 2 | ☁️ Azure / GitHub Models | `gpt-4o` | ✅ GITHUB_TOKEN_1 |
| 3 | ☁️ Azure / GitHub Models | `gpt-4o` | ✅ GITHUB_TOKEN_2 |

### Konfigurasi Engine
- **Max Tokens:** 2048 per respons
- **Temperature:** 0.7
- **Max Agentic Iterations:** 15 putaran tool calling per satu pesan
- **System Prompt:** Berisi aturan wajib + panduan routing tool (Tool Routing Guide)

---

## 🔐 Security Sandbox (`core/sandbox.py`)

Setiap tool yang dipanggil AI **WAJIB** melewati validasi sandbox. Jika sebuah aksi masuk daftar `require_approval_for`, akan muncul **pop-up dialog konfirmasi** kepada pengguna sebelum dieksekusi.

**Aksi yang memerlukan konfirmasi (default):**
- `delete_file` — Menghapus file/folder
- `execute_terminal` — Menjalankan perintah terminal
- `open_application` — Membuka aplikasi

**Perintah Git dengan konfirmasi otomatis:**
- `add`, `commit`, `push`, `init`, `reset`, `clean`, `checkout`, `merge`
- Perintah baca (`status`, `log`, `diff`) langsung diizinkan tanpa pop-up

**Konfigurasi:** `data/security.json`

---

## 🧩 Plugin & Tools yang Sudah Ada

> **Total: 55+ tools aktif** terdistribusi di 8 plugin

---

### 📂 1. File Explorer (`plugins/file_explorer.py`)
*Kontrol penuh sistem file komputer*

| Tool | Fungsi |
|---|---|
| `list_directory(path)` | Melihat isi folder |
| `read_file(path)` | Membaca isi file teks |
| `search_files(query, path)` | Cari file berdasarkan nama |
| `write_file(path, content)` | **Buat / timpa file** |
| `create_directory(path)` | **Buat folder baru** |
| `delete_file_or_folder(path)` | **Hapus file/folder** *(butuh sandbox approval)* |
| `move_rename_item(src, dest)` | Pindahkan / rename |
| `compress_to_zip(folder, output)` | Kompres folder → `.zip` |

---

### 🖥️ 2. System Control (`plugins/system_control.py`)
*Kontrol OS dan aplikasi Windows*

| Tool | Fungsi |
|---|---|
| `get_system_info()` | Cek CPU%, RAM% real-time |
| `open_application(name)` | Buka aplikasi (Chrome, VSCode, Notepad, dll) |
| `close_application(name)` | Force kill proses yang berjalan |
| `take_screenshot(path?)` | Ambil tangkapan layar |
| `set_system_volume(0-100)` | Atur volume speaker |
| `power_action(action)` | Sleep / Hibernate / Restart / Shutdown |
| `list_chrome_profiles()` | Daftar profil Google Chrome |
| `open_chrome_profile(name)` | Buka profil Chrome tertentu |

---

### 💾 3. Hardware Info (`plugins/hardware_info.py`)
*Diagnostik spesifikasi perangkat keras*

| Tool | Fungsi |
|---|---|
| `get_full_hardware_info()` | CPU, RAM, semua partisi disk, GPU |
| `check_drivers(name?)` | Daftar driver Windows yang terinstal |

---

### 🔧 4. Git Control (`plugins/git_control.py`)
*Version control via Git CLI*

| Tool | Fungsi |
|---|---|
| `execute_git_command(subcmd, dir)` | Jalankan perintah git apapun: `status`, `add .`, `commit -m "..."`, `push`, `pull`, `log`, `init`, `clone`, dll |

> ⚠️ Perintah modifikasi memerlukan konfirmasi sandbox

---

### 🌐 5. Web & Network (`plugins/web_network.py`)
*Konektivitas internet dan pencarian*

| Tool | Fungsi |
|---|---|
| `search_duckduckgo(query)` | **Cari di internet** (DuckDuckGo), kembalikan 5 hasil |
| `open_website(url)` | Buka URL di browser default |
| `check_network_status()` | Cek koneksi + uji ping |
| `get_ip_address()` | IP lokal + IP publik |

---

### ⚡ 6. Terminal Control (`plugins/terminal_control.py`)
*Eksekusi skrip shell langsung*

| Tool | Fungsi |
|---|---|
| `execute_powershell(command)` | Jalankan perintah PowerShell / Bash (timeout 30 detik) |

---

### 🖱️ 7. Input Control (`plugins/input_control.py`)
*Otomatisasi UI — Mouse & Keyboard (RPA)*

> Gunakan **hanya** jika pengguna secara eksplisit meminta otomatisasi UI

**Mouse:**
| Tool | Fungsi |
|---|---|
| `mouse_move(x, y)` | Gerakkan kursor |
| `mouse_click(x, y, button)` | Klik kiri/kanan/tengah |
| `mouse_double_click(x, y)` | Double-click |
| `mouse_right_click(x, y)` | Klik kanan (context menu) |
| `mouse_drag(fx, fy, tx, ty)` | Drag & drop |
| `scroll(x, y, amount)` | Scroll naik/turun |
| `get_mouse_position()` | Posisi kursor saat ini |

**Keyboard:**
| Tool | Fungsi |
|---|---|
| `keyboard_type(text)` | Ketik teks otomatis |
| `keyboard_hotkey(*keys)` | Kombinasi tombol (Ctrl+S, Alt+F4, Win+D) |
| `keyboard_press(key)` | Tekan satu tombol (Enter, Esc, F5, dll) |
| `keyboard_write_and_enter(text)` | Ketik teks + langsung Enter |

---

### 📄 8. Office Tools (`plugins/office_tools.py`)
*Membaca dan membuat dokumen produktivitas*

| Tool | Fungsi |
|---|---|
| `read_pdf(path, max_pages?)` | Ekstrak teks dari PDF |
| `get_pdf_info(path)` | Metadata PDF (halaman, author, dll) |
| `read_docx(path)` | Baca dokumen Word (.docx) |
| `create_docx(path, title, content)` | **Buat file Word baru** |
| `get_docx_info(path)` | Info ringkas dokumen Word |
| `read_excel(path, sheet?, max_rows?)` | Baca tabel Excel (.xlsx) |
| `get_excel_info(path)` | Daftar sheet & dimensi Excel |
| `read_csv(path, max_rows?)` | Baca file CSV |

---

## 🖼️ UI (`ui/app.py`)

**Framework:** CustomTkinter  
**Resolusi:** 1280×720 (16:9)

### Fitur UI yang Ada:
- **Chat Bubble** — Warna berbeda untuk user (biru) vs AI (abu gelap)
- **Loading Animation** — Teks berubah dinamis setiap tool dieksekusi  
  Contoh: *"📁 Membuat folder: website_test..."* → *"✍️ Menulis file: index.html..."*
- **Model Switcher** — Dropdown ganti backend (Ollama / GPT-4o Akun 1 / Akun 2)
- **Style Switcher** — Gaya jawaban: Normal / Singkat & Padat / Panjang & Detail
- **Sidebar** — Chat, Tools & Plugins, Security Sandbox, Monitoring, Settings *(tab belum aktif)*
- **Input** — Enter / tombol Send
- **Auto-scroll** ke bawah setiap pesan baru

---

## 📦 Dependencies (`requirements.txt`)

```
customtkinter     # UI framework
pillow            # Screenshot + image processing
darkdetect        # Dark mode detection
openai            # API client (Ollama + Azure)
python-dotenv     # .env loader
psutil            # CPU/RAM/Disk info
duckduckgo-search # Internet search
pyautogui         # Mouse & keyboard automation
PyMuPDF           # Baca PDF
python-docx       # Baca/tulis Word
openpyxl          # Baca/tulis Excel
pyperclip         # Clipboard
winotify          # Windows toast notification
```

---

## 🗺️ Roadmap — Rencana Implementasi ke Depan

### 🟡 Prioritas Tinggi (Segera)

#### A. Clipboard Manager (`plugins/clipboard_manager.py`)
- `get_clipboard()` — Baca isi clipboard
- `set_clipboard(text)` — Copy teks ke clipboard
- `clear_clipboard()` — Kosongkan clipboard
> **Dependensi:** `pyperclip` *(sudah terinstal)*

#### B. Process Manager (`plugins/process_manager.py`)
- `list_running_processes()` — Semua proses dengan CPU% & RAM%
- `kill_process_by_pid(pid)` — Kill berdasarkan PID spesifik
- `get_process_details(name_or_pid)` — Detail proses (path, uptime, thread)
- `list_startup_programs()` — Program yang berjalan saat startup Windows
- `get_open_network_connections()` — Koneksi jaringan aktif (seperti netstat)
> **Dependensi:** `psutil` *(sudah terinstal)*

#### C. Screen Vision / OCR (`plugins/screen_vision.py`) ⏸️ *ditunda*
- `ocr_screenshot()` — Baca semua teks dari tangkapan layar
- `ocr_region(x, y, w, h)` — OCR pada area layar tertentu
- `find_text_on_screen(query)` — Cari teks di layar, kembalikan koordinatnya
> **Dependensi:** `pytesseract` + Tesseract-OCR (installer terpisah)

#### D. Notification System (`plugins/notification.py`)
- `send_notification(title, message)` — Kirim Windows toast notification
- `play_sound(type)` — Putar suara sistem (beep, error, notif)
> **Dependensi:** `winotify` *(sudah terinstal)*

---

### 🔵 Prioritas Menengah

#### E. Image Processing (`plugins/image_tools.py`)
- `resize_image(path, w, h, out)` — Ubah resolusi gambar
- `convert_image(path, format, out)` — Konversi format (PNG→JPG→WebP)
- `crop_image(path, x, y, w, h, out)` — Potong gambar
- `get_image_info(path)` — Metadata gambar
- `compress_image(path, quality, out)` — Kompres ukuran file
> **Dependensi:** `Pillow` *(sudah terinstal)*

#### F. Python Code Executor (`plugins/code_executor.py`)
- `run_python_code(code)` — Jalankan kode Python, kembalikan output/error
- `run_python_file(path)` — Jalankan file `.py` yang sudah ada
- `pip_install(package)` — Install paket Python baru
- `list_installed_packages()` — Daftar semua paket pip

#### G. Scheduled Tasks (`plugins/scheduler.py`)
- `create_task(name, command, cron_expr)` — Buat jadwal tugas
- `list_tasks()` — Daftar semua tugas terjadwal ORCHID
- `cancel_task(name)` — Batalkan jadwal
> Memungkinkan AI menjalankan tugas otomatis (backup jam 12 malam, dll)

---

### 🟣 Prioritas Rendah / Riset

#### H. Memory Persistence (`core/memory.py`)
- Simpan riwayat percakapan ke SQLite
- Recall konteks sesi sebelumnya saat aplikasi dibuka ulang
- Sistem "ingatan jangka panjang" berbasis embedding

#### I. UI Tabs yang Belum Aktif
- **Tools & Plugins** — Daftar semua plugin, toggle aktif/nonaktif
- **Security Sandbox** — UI untuk kelola whitelist, lihat log aksi
- **Monitoring** — Dashboard CPU/RAM/Disk real-time (grafik)
- **Settings** — Ganti model, suhu, max token, gaya bicara default

#### J. Multi-Modal Vision (Future)
- Integrasi dengan model vision (LLaVA, Qwen-VL) untuk analisis gambar
- Bisa menganalisis screenshot dan mendeskripsikan isinya

#### K. Voice Input/Output (Future)
- Speech-to-text untuk input suara
- Text-to-speech untuk membaca respons AI

---

## 📊 Ringkasan Statistik Proyek

| Metrik | Nilai |
|---|---|
| Total Plugin | 8 aktif |
| Total Tools | ~55 tools |
| Total Dependensi | 14 paket |
| AI Backend | 3 slot (Ollama + 2x Azure) |
| Agentic Loop Max | 15 iterasi |
| Lines of Code (estimasi) | ~1.200 baris |

---

> [!NOTE]
> Dokumen ini dibuat otomatis berdasarkan kode yang ada per 30 Juni 2026. Update setiap kali ada plugin atau fitur baru yang ditambahkan.
