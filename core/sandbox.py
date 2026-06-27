import json
import os
import tkinter.messagebox

class SecuritySandbox:
    def __init__(self):
        self.config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "security.json")
        self._load_config()

    def _load_config(self):
        if not os.path.exists(self.config_path):
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            default_config = {
                "require_approval_for": ["delete_file", "execute_terminal", "open_application"],
                "allowed_directories": ["C:\\Users\\ALIM\\Downloads\\ORCHID"]
            }
            with open(self.config_path, "w") as f:
                json.dump(default_config, f, indent=4)
        
        with open(self.config_path, "r") as f:
            self.config = json.load(f)

    def validate_action(self, action_name, **kwargs):
        """
        Memvalidasi aksi. Jika butuh persetujuan, munculkan Pop-up dialog.
        Mengembalikan True jika diizinkan, False jika ditolak.
        """
        # Penanganan khusus untuk agen Git
        if action_name == "execute_git_command":
            subcommand = kwargs.get("subcommand", "").lower()
            
            # Perintah modifikasi wajib minta izin
            if any(subcommand.startswith(cmd) for cmd in ["add", "commit", "push", "init", "reset", "clean", "checkout", "merge"]):
                msg = f"⚠️ ORCHID ingin mengeksekusi perintah Git yang akan memodifikasi repositori:\n\n'git {subcommand}'\n\nDirektori: {kwargs.get('directory', '.')}\n\nApakah Anda mengizinkan aksi ini?"
                result = tkinter.messagebox.askyesno("Keamanan Git Sandbox ORCHID", msg)
                return result
            # Perintah baca (status, log, diff) langsung diizinkan tanpa pop-up
            return True

        if action_name in self.config.get("require_approval_for", []):
            msg = f"⚠️ ORCHID ingin menjalankan fungsi: '{action_name}'.\n\nDetail:\n{kwargs}\n\nApakah Anda mengizinkan aksi ini?"
            result = tkinter.messagebox.askyesno("Keamanan Sandbox ORCHID", msg)
            return result
            
        return True
