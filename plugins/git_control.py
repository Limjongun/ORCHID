import subprocess

def execute_git_command(subcommand, directory="."):
    """Mengeksekusi perintah git di direktori tertentu."""
    try:
        if subcommand.startswith("git "):
            subcommand = subcommand[4:]
            
        cmd = f"git {subcommand}"
        
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=directory,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode == 0:
            return f"Sukses menjalankan '{cmd}':\n{result.stdout}"
        else:
            return f"Error ({result.returncode}) saat menjalankan '{cmd}':\n{result.stderr}"
    except Exception as e:
        return f"Gagal menjalankan perintah Git: {e}"

GIT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "execute_git_command",
            "description": "Menjalankan perintah Git CLI (contoh: status, log, add ., commit -m 'pesan', push, init, dll). Berguna untuk version control.",
            "parameters": {
                "type": "object",
                "properties": {
                    "subcommand": {
                        "type": "string",
                        "description": "Perintah git yang akan dijalankan (TIDAK perlu menulis kata 'git' di awalnya). Contoh yang benar: 'status', 'add .', 'commit -m \"Pesan update\"', 'push origin main'."
                    },
                    "directory": {
                        "type": "string",
                        "description": "Direktori target tempat perintah git akan dieksekusi. Gunakan '.' untuk direktori kerja saat ini."
                    }
                },
                "required": ["subcommand"]
            }
        }
    }
]

GIT_TOOL_MAP = {
    "execute_git_command": execute_git_command
}
