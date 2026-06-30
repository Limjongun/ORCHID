import webbrowser
import socket
import subprocess
import urllib.request
try:
    from duckduckgo_search import DDGS
    HAS_DDGS = True
except ImportError:
    HAS_DDGS = False

def open_website(url):
    """Membuka website di browser default."""
    try:
        if not url.startswith('http://') and not url.startswith('https://'):
            url = 'https://' + url
        webbrowser.open(url)
        return f"Perintah membuka website '{url}' telah dikirim ke browser default."
    except Exception as e:
        return f"Gagal membuka website: {e}"

def search_duckduckgo(query):
    """Melakukan pencarian di internet dan mengembalikan ringkasan teks."""
    if not HAS_DDGS:
        return "Library 'duckduckgo-search' belum diinstal. Jalankan: pip install duckduckgo-search"
        
    try:
        results = []
        with DDGS() as ddgs:
            # Ambil 5 hasil pertama
            for r in ddgs.text(query, max_results=5):
                results.append(f"Judul: {r.get('title')}\nURL: {r.get('href')}\nDeskripsi: {r.get('body')}\n")
        
        if not results:
            return f"Tidak ada hasil yang ditemukan untuk pencarian '{query}'."
            
        return f"Hasil pencarian untuk '{query}':\n\n" + "-"*40 + "\n" + "\n".join(results)
    except Exception as e:
        return f"Gagal mencari di internet: {e}"

def check_network_status():
    """Mengecek apakah komputer terkoneksi internet dan melakukan ping test."""
    try:
        # Cek koneksi sederhana
        urllib.request.urlopen("https://1.1.1.1", timeout=3)
        status = "Terkoneksi ke Internet."
        
        # Coba ping google untuk mengecek latensi
        ping_result = subprocess.run(
            ["ping", "-n", "2", "8.8.8.8"], 
            capture_output=True, text=True
        )
        
        if ping_result.returncode == 0:
            lines = ping_result.stdout.split('\n')
            avg_ping = [line for line in lines if "Average" in line or "Rata-rata" in line]
            if avg_ping:
                status += f"\nLatensi Ping (ke Google): {avg_ping[0].strip()}"
        
        return status
    except Exception:
        return "Tidak ada koneksi internet atau koneksi sangat lambat."

def get_ip_address():
    """Mendapatkan IP Lokal dan IP Publik (jika terkoneksi)."""
    try:
        # IP Lokal
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        result = f"Hostname: {hostname}\nIP Lokal: {local_ip}"
        
        # Coba ambil IP publik
        try:
            with urllib.request.urlopen('https://api.ipify.org', timeout=3) as response:
                public_ip = response.read().decode('utf-8')
                result += f"\nIP Publik: {public_ip}"
        except Exception:
            result += "\nIP Publik: (Gagal memuat, mungkin offline)"
            
        return result
    except Exception as e:
        return f"Gagal mendapatkan informasi IP: {e}"

WEB_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "open_website",
            "description": "Membuka sebuah halaman website di browser utama.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL website yang akan dibuka (contoh: 'google.com', 'https://youtube.com')."}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_duckduckgo",
            "description": "Melakukan pencarian di internet (Google/DuckDuckGo) untuk mencari informasi real-time dan berita terbaru.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Kata kunci pertanyaan yang ingin dicari di internet."}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_network_status",
            "description": "Mengecek apakah ada koneksi internet dan berapa nilai ping-nya."
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_ip_address",
            "description": "Melihat IP lokal komputer di jaringan Wi-Fi/LAN dan IP Publik Internet."
        }
    }
]

WEB_TOOL_MAP = {
    "open_website": open_website,
    "search_duckduckgo": search_duckduckgo,
    "check_network_status": check_network_status,
    "get_ip_address": get_ip_address
}
