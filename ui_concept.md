# Konsep Desain Antarmuka ORCHID

Dokumen ini menjelaskan struktur UI untuk aplikasi desktop ORCHID, berdasarkan referensi visual yang telah disepakati dan disimpan di folder ini (`ORCHID_UI_Concept.png`).

## 1. Tema Visual (Theme & Vibe)
*   **Warna Latar Utama:** Dark Navy (Biru Gelap), agar nyaman di mata saat digunakan dalam jangka waktu lama (produktivitas harian).
*   **Warna Aksen:** Sky Blue (Biru Langit), untuk menyorot tombol aktif, teks gelembung obrolan (*chat bubble*), dan ikon.
*   **Material Efek:** *Frosted Glass* atau *Acrylic Blur* (Glassmorphism) yang transparan, tipis, dan elegan. Khususnya diterapkan pada *Sidebar*.
*   **Rasio & Bentuk:** Menggunakan layar penuh (*fullscreen*) laptop (rasio 16:9), dengan desain *flat* yang rapi, profesional, membuang efek *sci-fi* berlebih.

## 2. Tata Letak (Layout Structure)

### A. Sidebar Kiri (Navigasi Modul)
Sidebar adalah menu kendali utama yang berfungsi sebagai *Router*. Mengklik menu di sini akan mengubah konten di panel tengah.
*   **Chat:** Jendela interaksi utama dengan asisten AI.
*   **Tools:** Daftar *Plugin* (Voice, Computer Vision, Office) dengan sakelar (*toggle on/off*) untuk menghemat memori jika tidak dipakai.
*   **Security (Sandbox):** Panel pengaturan *Whitelist/Blacklist* untuk melindungi folder sensitif.
*   **Monitoring:** Grafik visualisasi performa CPU, GPU, RAM, dan Jaringan secara *real-time*.
*   **Settings:** Pengaturan model AI (lokal/API), ukuran teks, dan kustomisasi pintasan (*shortcut*).

### B. Area Konten Utama (Tengah)
*   Bersih dan bebas distraksi. Pada mode **Chat**, area ini akan menampilkan riwayat obrolan layaknya ChatGPT.
*   Mendukung *Markdown rendering* (teks tebal, miring, tabel) dan *Syntax Highlighting* jika AI merespons dengan kode pemrograman (*code block*).

### C. Kolom Input Bawah
*   Kotak teks sederhana untuk mengetik (*Prompt*).
*   Ikon penjepit kertas (Attachment) untuk melampirkan file PDF/Gambar agar bisa dianalisis AI (Modul *File System* & *Vision*).
*   Ikon mikrofon untuk mode *Voice Assistant*.

---
*(Implementasi ke depannya akan dibangun menggunakan library `CustomTkinter` di Python)*
