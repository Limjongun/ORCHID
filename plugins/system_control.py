import platform
import psutil
import subprocess
import os
import json
from PIL import ImageGrab
import datetime

def get_system_info():
    """Mengembalikan informasi CPU dan RAM saat ini."""
    ram = psutil.virtual_memory()
    cpu = psutil.cpu_percent(interval=0.5)
    
    info = {
        "os": platform.system(),
        "os_version": platform.version(),
        "cpu_usage_percent": cpu,
        "ram_total_gb": round(ram.total / (1024**3), 2),
        "ram_used_gb": round(ram.used / (1024**3), 2),
        "ram_percent": ram.percent
    }
    return str(info)

def open_application(app_name):
    """Membuka aplikasi sistem dan aplikasi populer di Windows."""
    app_name = app_name.lower().strip()
    
    app_mapping = {
        "notepad": "notepad.exe",
        "kalkulator": "calc.exe",
        "calc": "calc.exe",
        "calculator": "calc.exe",
        "chrome": "chrome.exe",
        "google chrome": "chrome.exe",
        "edge": "msedge.exe",
        "browser": "msedge.exe", 
        "vscode": "code",
        "vs code": "code",
        "visual studio code": "code",
        "word": "winword",
        "excel": "excel",
        "powerpoint": "powerpnt",
        "spotify": "spotify",
        "explorer": "explorer.exe",
        "file explorer": "explorer.exe",
        "cmd": "cmd.exe",
        "terminal": "wt.exe", 
        "settings": "ms-settings:",
        "paint": "mspaint.exe",
        "corel": "coreldrw.exe",
        "coreldraw": "coreldrw.exe",
        "illustrator": "illustrator.exe",
        "photoshop": "photoshop.exe",
        "figma": "figma.exe",
        "whatsapp": "whatsapp.exe",
        "zoom": "zoom.exe"
    }
    
    exe_name = app_mapping.get(app_name, app_name)
    
    try:
        subprocess.Popen(f"start {exe_name}", shell=True)
        return f"Perintah untuk membuka '{app_name}' telah dikirim ke sistem Windows."
    except Exception as e:
        return f"Gagal membuka aplikasi '{app_name}': {e}"

def close_application(app_name):
    """Menutup (force kill) aplikasi yang sedang berjalan berdasarkan namanya."""
    try:
        count = 0
        target = app_name.lower()
        for proc in psutil.process_iter(['pid', 'name']):
            if target in proc.info['name'].lower():
                proc.kill()
                count += 1
        if count > 0:
            return f"Sukses menghentikan {count} proses '{app_name}'."
        else:
            return f"Tidak ditemukan proses dengan nama '{app_name}' yang sedang berjalan."
    except Exception as e:
        return f"Gagal menghentikan aplikasi: {e}"

def take_screenshot(save_path=None):
    """Mengambil tangkapan layar (screenshot) penuh dan menyimpannya."""
    try:
        if not save_path:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = f"screenshot_{timestamp}.png"
            
        screenshot = ImageGrab.grab()
        screenshot.save(save_path)
        return f"Tangkapan layar berhasil disimpan di: {os.path.abspath(save_path)}"
    except Exception as e:
        return f"Gagal mengambil tangkapan layar: {e}"

def set_system_volume(level_percent):
    """Mengubah volume sistem (0-100) menggunakan PowerShell."""
    try:
        level = max(0, min(100, int(level_percent)))
        # Menggunakan nirCMD jika ada, tapi karena mungkin tidak terinstal, gunakan script SoundVolumeView atau PowerShell volume set (membutuhkan modul tambahan)
        # Sebagai alternatif tanpa modul pihak ketiga, kita dapat mensimulasikan penekanan tombol Volume Up/Down 50 kali lalu menaikkannya sesuai persen.
        # Pendekatan lebih bersih: menggunakan skrip PowerShell (dimana 0 = unmute & set 0, lalu naikkan per 2%).
        ps_script = f"""
$obj = new-object -com wscript.shell
# Turunkan volume ke 0 (tekan vol down 50x)
for ($i = 0; $i -lt 50; $i++) {{ $obj.SendKeys([char]174) }}
# Naikkan ke target (tekan vol up sebanyak level/2)
$steps = [math]::Round({level}/2)
for ($i = 0; $i -lt $steps; $i++) {{ $obj.SendKeys([char]175) }}
"""
        subprocess.run(["powershell", "-Command", ps_script], capture_output=True)
        return f"Volume sistem telah diatur mendekati {level}%."
    except Exception as e:
        return f"Gagal mengatur volume: {e}"

def power_action(action):
    """Melakukan aksi Sleep, Hibernate, Restart, atau Shutdown."""
    action = action.lower()
    try:
        if action == "sleep":
            subprocess.run("rundll32.exe powrprof.dll,SetSuspendState 0,1,0", shell=True)
            return "Perintah Sleep telah dikirim."
        elif action == "hibernate":
            subprocess.run("shutdown /h", shell=True)
            return "Perintah Hibernate telah dikirim."
        elif action == "restart":
            # subprocess.run("shutdown /r /t 5", shell=True)
            return "Simulator Restart: (Command sebenarnya dikomentari demi keamanan saat development)."
        elif action == "shutdown":
            # subprocess.run("shutdown /s /t 5", shell=True)
            return "Simulator Shutdown: (Command sebenarnya dikomentari demi keamanan saat development)."
        else:
            return f"Aksi '{action}' tidak dikenal."
    except Exception as e:
        return f"Gagal melakukan aksi power: {e}"

def list_chrome_profiles():
    """Mengembalikan daftar nama profil Google Chrome yang tersedia."""
    local_app_data = os.environ.get('LOCALAPPDATA')
    if not local_app_data:
        return "Tidak dapat menemukan folder LocalAppData."
    
    local_state_path = os.path.join(local_app_data, "Google", "Chrome", "User Data", "Local State")
    if not os.path.exists(local_state_path):
        return "Google Chrome tidak terinstal atau belum dikonfigurasi."
        
    try:
        with open(local_state_path, "r", encoding="utf-8") as f:
            local_state = json.load(f)
            
        profiles = local_state.get("profile", {}).get("info_cache", {})
        result = []
        for profile_dir, info in profiles.items():
            result.append(info.get("name", profile_dir))
            
        return f"Profil Chrome yang tersedia: {', '.join(result)}" if result else "Tidak ada profil yang ditemukan."
    except Exception as e:
        return f"Gagal membaca profil Chrome: {e}"

def open_chrome_profile(profile_name):
    """Membuka Google Chrome dengan nama profil spesifik."""
    local_app_data = os.environ.get('LOCALAPPDATA')
    if not local_app_data:
        return "Tidak dapat menemukan folder LocalAppData."
    
    local_state_path = os.path.join(local_app_data, "Google", "Chrome", "User Data", "Local State")
    if not os.path.exists(local_state_path):
        return "Google Chrome tidak terinstal."
        
    try:
        with open(local_state_path, "r", encoding="utf-8") as f:
            local_state = json.load(f)
            
        profiles = local_state.get("profile", {}).get("info_cache", {})
        target_dir = None
        for profile_dir, info in profiles.items():
            if info.get("name", profile_dir).lower() == profile_name.lower():
                target_dir = profile_dir
                break
                
        if not target_dir:
            return f"Profil Chrome '{profile_name}' tidak ditemukan."
            
        subprocess.Popen(f'start chrome --profile-directory="{target_dir}"', shell=True)
        return f"Perintah membuka profil '{profile_name}' dikirim."
    except Exception as e:
        return f"Gagal membuka profil Chrome: {e}"

# Definisi tool dalam format API OpenAI
SYSTEM_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_system_info",
            "description": "Dapatkan info RAM, Memori, dan CPU saat ini."
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_application",
            "description": "Buka aplikasi di komputer (notepad, chrome, vscode, dll).",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "Nama aplikasi."}
                },
                "required": ["app_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "close_application",
            "description": "Menutup secara paksa (force close/kill) aplikasi yang berjalan.",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "Nama aplikasi atau nama proses (contoh: 'chrome', 'notepad')."}
                },
                "required": ["app_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "take_screenshot",
            "description": "Mengambil tangkapan layar (screenshot) monitor komputer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "save_path": {"type": "string", "description": "Path tempat menyimpan file PNG. Biarkan kosong untuk auto-generate nama."}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_system_volume",
            "description": "Mengubah volume audio sistem Windows.",
            "parameters": {
                "type": "object",
                "properties": {
                    "level_percent": {"type": "integer", "description": "Tingkat volume dari 0 (Mute) hingga 100."}
                },
                "required": ["level_percent"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "power_action",
            "description": "Melakukan fungsi kontrol daya pada komputer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "Pilih salah satu: 'sleep', 'hibernate', 'restart', 'shutdown'."}
                },
                "required": ["action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_chrome_profiles",
            "description": "Menampilkan semua profil Google Chrome yang terdaftar."
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_chrome_profile",
            "description": "Membuka profil Google Chrome tertentu.",
            "parameters": {
                "type": "object",
                "properties": {
                    "profile_name": {"type": "string", "description": "Nama profil Chrome (contoh: 'Agung')."}
                },
                "required": ["profile_name"]
            }
        }
    }
]

SYSTEM_TOOL_MAP = {
    "get_system_info": get_system_info,
    "open_application": open_application,
    "close_application": close_application,
    "take_screenshot": take_screenshot,
    "set_system_volume": set_system_volume,
    "power_action": power_action,
    "list_chrome_profiles": list_chrome_profiles,
    "open_chrome_profile": open_chrome_profile
}
