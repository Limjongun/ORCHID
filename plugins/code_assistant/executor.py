"""
executor.py — Code Executor & Persistent REPL
Menjalankan kode Python secara terisolasi di dalam subprocess dengan venv.
"""
import os
import sys
import subprocess
import threading
import queue
import tempfile
import shutil
import time
from typing import Optional

# ─── Konfigurasi ────────────────────────────────────────────────────────────
ROOT_DIR    = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VENV_DIR    = os.path.join(ROOT_DIR, "data", "code_venv")
OUTPUT_CAP  = 10_000   # Batas karakter output untuk mencegah flooding ke AI
EXEC_TIMEOUT = 30       # detik

def _get_python_bin() -> str:
    """Kembalikan path Python interpreter di dalam venv ORCHID."""
    if sys.platform == "win32":
        return os.path.join(VENV_DIR, "Scripts", "python.exe")
    return os.path.join(VENV_DIR, "bin", "python")

def _ensure_venv() -> tuple[bool, str]:
    """Buat venv jika belum ada."""
    python_bin = _get_python_bin()
    if not os.path.exists(python_bin):
        result = subprocess.run(
            [sys.executable, "-m", "venv", VENV_DIR],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            return False, f"Gagal membuat venv: {result.stderr}"
    return True, python_bin


# ─── Tool 1: run_python_code ─────────────────────────────────────────────────
def run_python_code(code: str, timeout: int = EXEC_TIMEOUT) -> dict:
    """
    Jalankan kode Python di subprocess terisolasi (venv).
    Mengembalikan dict dengan stdout, stderr, exit_code, dan execution_time.
    """
    ok, python_bin = _ensure_venv()
    if not ok:
        return {"stdout": "", "stderr": python_bin, "exit_code": -1, "execution_time": 0}

    # Tulis ke file sementara agar bisa menjalankan multi-baris dengan aman
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", encoding="utf-8", delete=False
    ) as tmp:
        tmp.write(code)
        tmp_path = tmp.name

    start = time.time()
    try:
        result = subprocess.run(
            [python_bin, tmp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=ROOT_DIR
        )
        elapsed = round(time.time() - start, 3)
        stdout = result.stdout[:OUTPUT_CAP]
        stderr = result.stderr[:OUTPUT_CAP]
        return {
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": result.returncode,
            "execution_time": elapsed,
            "success": result.returncode == 0
        }
    except subprocess.TimeoutExpired:
        return {
            "stdout": "",
            "stderr": f"Timeout: Eksekusi melampaui {timeout} detik.",
            "exit_code": -1,
            "execution_time": timeout,
            "success": False
        }
    except Exception as e:
        return {"stdout": "", "stderr": str(e), "exit_code": -1, "execution_time": 0, "success": False}
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


# ─── Tool 2: run_python_file ─────────────────────────────────────────────────
def run_python_file(file_path: str, args: list = None, timeout: int = EXEC_TIMEOUT) -> dict:
    """Jalankan file .py yang sudah ada dengan argumen opsional."""
    if not os.path.isfile(file_path):
        return {"stdout": "", "stderr": f"File tidak ditemukan: {file_path}", "exit_code": -1, "success": False}
    
    ok, python_bin = _ensure_venv()
    if not ok:
        return {"stdout": "", "stderr": python_bin, "exit_code": -1, "success": False}

    cmd = [python_bin, file_path] + (args or [])
    start = time.time()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=os.path.dirname(file_path))
        elapsed = round(time.time() - start, 3)
        return {
            "stdout": result.stdout[:OUTPUT_CAP],
            "stderr": result.stderr[:OUTPUT_CAP],
            "exit_code": result.returncode,
            "execution_time": elapsed,
            "success": result.returncode == 0
        }
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": f"Timeout: {timeout}s terlampaui.", "exit_code": -1, "success": False}
    except Exception as e:
        return {"stdout": "", "stderr": str(e), "exit_code": -1, "success": False}


# ─── Tool 3: install_package ─────────────────────────────────────────────────
def install_package(package_name: str) -> dict:
    """Install paket pip ke dalam venv ORCHID."""
    ok, python_bin = _ensure_venv()
    if not ok:
        return {"success": False, "message": python_bin}
    
    try:
        result = subprocess.run(
            [python_bin, "-m", "pip", "install", package_name, "--quiet"],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode == 0:
            return {"success": True, "message": f"'{package_name}' berhasil diinstal."}
        else:
            return {"success": False, "message": result.stderr[:2000]}
    except subprocess.TimeoutExpired:
        return {"success": False, "message": "Timeout saat instalasi paket."}
    except Exception as e:
        return {"success": False, "message": str(e)}


# ─── Persistent REPL Session ─────────────────────────────────────────────────
class _ReplSession:
    """
    Sesi Python REPL persisten yang berjalan di background subprocess.
    Berkomunikasi via stdin/stdout dengan sentinel untuk mendeteksi akhir output.
    """
    SENTINEL = "__ORCHID_REPL_DONE__"

    def __init__(self):
        ok, python_bin = _ensure_venv()
        if not ok:
            raise RuntimeError(python_bin)

        self._proc = subprocess.Popen(
            [python_bin, "-i", "-u"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=0
        )
        self._lock = threading.Lock()
        self._alive = True
        # Flush banner
        self._read_until_sentinel(init=True)

    def _read_until_sentinel(self, init=False) -> str:
        """Baca output hingga sentinel terdeteksi atau timeout."""
        if init:
            # Kirim sentinel pertama untuk flush banner
            self._proc.stdin.write(f'print("{self.SENTINEL}")\n')
            self._proc.stdin.flush()

        output_lines = []
        deadline = time.time() + 10
        while time.time() < deadline:
            line = self._proc.stdout.readline()
            if not line:
                break
            stripped = line.rstrip("\n")
            if stripped == self.SENTINEL:
                break
            output_lines.append(stripped)
        return "\n".join(output_lines)

    def send(self, code: str) -> dict:
        """Kirim kode ke REPL dan tangkap hasilnya."""
        if not self._alive:
            return {"output": "", "error": "Sesi REPL sudah ditutup.", "success": False}

        with self._lock:
            try:
                wrapped = f"{code}\nprint('{self.SENTINEL}')\n"
                self._proc.stdin.write(wrapped)
                self._proc.stdin.flush()
                output = self._read_until_sentinel()
                return {"output": output[:OUTPUT_CAP], "success": True}
            except Exception as e:
                self._alive = False
                return {"output": "", "error": str(e), "success": False}

    def stop(self):
        if self._alive:
            try:
                self._proc.stdin.write("exit()\n")
                self._proc.stdin.flush()
                self._proc.terminate()
            except Exception:
                pass
            self._alive = False


# Singleton REPL session
_active_repl: Optional[_ReplSession] = None


# ─── Tool 4: start_repl_session ──────────────────────────────────────────────
def start_repl_session() -> dict:
    """Mulai sesi Python REPL persisten. Variabel akan diingat antar pemanggilan repl_send."""
    global _active_repl
    if _active_repl and _active_repl._alive:
        return {"success": True, "message": "Sesi REPL sudah aktif."}
    try:
        _active_repl = _ReplSession()
        return {"success": True, "message": "Sesi REPL Python berhasil dimulai. Variabel akan diingat antar pemanggilan."}
    except Exception as e:
        return {"success": False, "message": str(e)}


# ─── Tool 5: repl_send ───────────────────────────────────────────────────────
def repl_send(code: str) -> dict:
    """Kirim kode ke sesi REPL aktif dan kembalikan output. Variabel sebelumnya masih tersedia."""
    global _active_repl
    if not _active_repl or not _active_repl._alive:
        # Auto-start jika belum ada
        result = start_repl_session()
        if not result["success"]:
            return result
    return _active_repl.send(code)


# ─── Tool 6: repl_stop ───────────────────────────────────────────────────────
def repl_stop() -> dict:
    """Hentikan sesi REPL aktif dan bebaskan memori."""
    global _active_repl
    if _active_repl and _active_repl._alive:
        _active_repl.stop()
        _active_repl = None
        return {"success": True, "message": "Sesi REPL dihentikan. Semua variabel dihapus dari memori."}
    return {"success": True, "message": "Tidak ada sesi REPL yang aktif."}


# ─── Tool 7: check_venv_status ───────────────────────────────────────────────
def check_venv_status() -> dict:
    """Periksa status venv ORCHID: apakah sudah ada dan paket apa yang terinstal."""
    python_bin = _get_python_bin()
    if not os.path.exists(python_bin):
        return {"exists": False, "message": "venv belum dibuat. Jalankan kode pertama untuk membuat otomatis.", "packages": []}
    
    result = subprocess.run(
        [python_bin, "-m", "pip", "list", "--format=columns"],
        capture_output=True, text=True, timeout=15
    )
    packages = result.stdout.strip().split("\n")[2:] if result.returncode == 0 else []
    return {
        "exists": True,
        "python_bin": python_bin,
        "venv_path": VENV_DIR,
        "packages": packages[:50],
        "package_count": len(packages)
    }
