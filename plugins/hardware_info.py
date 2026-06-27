import platform
import psutil
import subprocess

def get_full_hardware_info():
    """Mengambil spesifikasi detail tentang CPU, RAM, Disk, dan GPU."""
    info = []
    
    # 1. OS Info
    info.append(f"OS: {platform.system()} {platform.release()} ({platform.version()})")
    info.append(f"Arsitektur: {platform.machine()}")
    
    # 2. CPU Info
    cpu_freq = psutil.cpu_freq()
    freq_str = f"{cpu_freq.current:.2f}MHz" if cpu_freq else "Unknown"
    info.append(f"CPU: {platform.processor()}")
    info.append(f"CPU Cores: {psutil.cpu_count(logical=False)} Physical, {psutil.cpu_count(logical=True)} Logical")
    info.append(f"CPU Freq: {freq_str}")
    info.append(f"CPU Usage: {psutil.cpu_percent(interval=0.5)}%")
    
    # 3. RAM Info
    ram = psutil.virtual_memory()
    info.append(f"RAM Total: {round(ram.total / (1024**3), 2)} GB")
    info.append(f"RAM Terpakai: {round(ram.used / (1024**3), 2)} GB ({ram.percent}%)")
    
    # 4. Disk Info
    info.append("Disk:")
    for partition in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            info.append(f"  - {partition.device} ({partition.fstype}): "
                        f"{round(usage.total / (1024**3), 2)} GB Total, "
                        f"{round(usage.free / (1024**3), 2)} GB Free ({usage.percent}% Terpakai)")
        except Exception:
            continue
            
    # 5. GPU Info (Menggunakan WMIC di Windows)
    try:
        if platform.system() == "Windows":
            gpu_cmd = subprocess.run(
                ["wmic", "path", "win32_VideoController", "get", "name"],
                capture_output=True, text=True, check=True
            )
            gpus = [line.strip() for line in gpu_cmd.stdout.split('\n') if line.strip() and "Name" not in line]
            info.append(f"GPU: {', '.join(gpus)}")
    except Exception as e:
        info.append(f"GPU: (Gagal membaca GPU: {e})")
        
    return "\n".join(info)

def check_drivers(driver_name=""):
    """Mengecek daftar driver yang terinstal di sistem Windows."""
    if platform.system() != "Windows":
        return "Fitur ini hanya tersedia di sistem operasi Windows."
        
    try:
        # Menggunakan driverquery
        cmd = subprocess.run(["driverquery", "/FO", "CSV"], capture_output=True, text=True, check=True)
        lines = cmd.stdout.strip().split('\n')
        
        if not lines:
            return "Tidak ada data driver."
            
        header = lines[0]
        results = []
        
        query = driver_name.lower().strip()
        
        for line in lines[1:]:
            if query in line.lower():
                results.append(line)
                
        if not results:
            if query:
                return f"Tidak ditemukan driver yang mengandung kata '{driver_name}'."
            else:
                # Kembalikan 20 driver pertama jika tidak difilter
                results = lines[1:21]
                return f"Menampilkan 20 driver pertama (dari total {len(lines)-1}):\n" + "\n".join(results)
                
        # Batasi hasil jika terlalu banyak (misal lebih dari 30)
        if len(results) > 30:
            return f"Ditemukan {len(results)} driver yang cocok (menampilkan 30 pertama):\n" + "\n".join(results[:30])
            
        return f"Ditemukan {len(results)} driver:\n" + "\n".join(results)
        
    except Exception as e:
        return f"Gagal mengecek driver: {e}"

HARDWARE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_full_hardware_info",
            "description": "Mendapatkan spesifikasi detail perangkat keras komputer (CPU, RAM, Partisi Disk, dan Kartu Grafis/GPU)."
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_drivers",
            "description": "Mengecek daftar driver sistem yang terinstal di Windows (Audio, VGA, Network, dll).",
            "parameters": {
                "type": "object",
                "properties": {
                    "driver_name": {
                        "type": "string",
                        "description": "Kata kunci pencarian nama driver (contoh: 'nvidia', 'audio', 'intel', 'realtek'). Kosongkan untuk melihat daftar umum."
                    }
                }
            }
        }
    }
]

HARDWARE_TOOL_MAP = {
    "get_full_hardware_info": get_full_hardware_info,
    "check_drivers": check_drivers
}
