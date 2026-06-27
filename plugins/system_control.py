import platform
import psutil
import subprocess
import os
import json

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

def list_chrome_profiles():
    """Mengembalikan daftar nama profil Google Chrome yang tersedia di komputer ini."""
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
            name = info.get("name", profile_dir)
            result.append(name)
            
        if not result:
            return "Tidak ada profil yang ditemukan."
            
        return f"Profil Chrome yang tersedia: {', '.join(result)}"
    except Exception as e:
        return f"Gagal membaca profil Chrome: {e}"

def open_chrome_profile(profile_name):
    """Membuka Google Chrome dengan nama profil yang spesifik."""
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
        
        target_dir = None
        # Pencarian case-insensitive
        for profile_dir, info in profiles.items():
            name = info.get("name", profile_dir)
            if name.lower() == profile_name.lower():
                target_dir = profile_dir
                break
                
        if not target_dir:
            return f"Profil Chrome dengan nama '{profile_name}' tidak ditemukan."
            
        subprocess.Popen(f'start chrome --profile-directory="{target_dir}"', shell=True)
        return f"Perintah untuk membuka Chrome dengan profil '{profile_name}' telah dikirim."
        
    except Exception as e:
        return f"Gagal membuka profil Chrome: {e}"

# Definisi tool dalam format spesifikasi API OpenAI
SYSTEM_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_system_info",
            "description": "Dapatkan informasi real-time tentang status sistem komputer (penggunaan RAM, Memori, dan CPU saat ini)."
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_application",
            "description": "Buka berbagai aplikasi di komputer (seperti notepad, kalkulator, chrome, vscode, coreldraw, figma, photoshop, word, excel, dll).",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {
                        "type": "string",
                        "description": "Nama aplikasi yang ingin dibuka, misalnya 'chrome', 'coreldraw', 'vscode', atau 'figma'."
                    }
                },
                "required": ["app_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_chrome_profiles",
            "description": "Menampilkan semua profil Google Chrome (user accounts) yang terdaftar di komputer ini."
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_chrome_profile",
            "description": "Membuka Google Chrome dengan profil (user account) tertentu.",
            "parameters": {
                "type": "object",
                "properties": {
                    "profile_name": {
                        "type": "string",
                        "description": "Nama profil Chrome yang ingin dibuka (contoh: 'agung', 'alim')."
                    }
                },
                "required": ["profile_name"]
            }
        }
    }
]

# Peta string nama ke fungsi asli Python
SYSTEM_TOOL_MAP = {
    "get_system_info": get_system_info,
    "open_application": open_application,
    "list_chrome_profiles": list_chrome_profiles,
    "open_chrome_profile": open_chrome_profile
}
