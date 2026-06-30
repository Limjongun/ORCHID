import subprocess
import platform

def execute_powershell(command):
    """Menjalankan perintah terminal atau PowerShell di latar belakang."""
    try:
        # Peringatan keamanan: Ini sangat rentan jika perintah destruktif dijalankan.
        # Fungsi Sandbox (sandbox.py) HARUS selalu memvalidasi argumen `command`.
        
        if platform.system() == "Windows":
            # Gunakan PowerShell untuk Windows
            cmd_args = ["powershell", "-Command", command]
        else:
            # Fallback untuk Linux/Mac
            cmd_args = ["bash", "-c", command]
            
        result = subprocess.run(
            cmd_args, 
            capture_output=True, 
            text=True, 
            timeout=30 # Batas waktu agar tidak hang
        )
        
        output = ""
        if result.stdout:
            output += "Output:\n" + result.stdout.strip()
        if result.stderr:
            output += "\nError:\n" + result.stderr.strip()
            
        if not output:
            output = f"Perintah `{command}` berhasil dijalankan tanpa output."
            
        return output
    except subprocess.TimeoutExpired:
        return f"Perintah `{command}` dihentikan karena memakan waktu lebih dari 30 detik."
    except Exception as e:
        return f"Gagal mengeksekusi terminal: {e}"

TERMINAL_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "execute_powershell",
            "description": "Menjalankan perintah PowerShell / Terminal (seperti membuat layanan, mengatur pengaturan Windows, atau skrip admin).",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Perintah bash / powershell lengkap yang ingin dieksekusi."}
                },
                "required": ["command"]
            }
        }
    }
]

TERMINAL_TOOL_MAP = {
    "execute_powershell": execute_powershell
}
