"""
diff_engine.py — Precise Code Modification Engine
Memodifikasi kode secara presisi: ganti fungsi, sisipkan baris, backup & restore.
Mirip cara Antigravity mengedit kode tanpa menimpa seluruh file.
"""
import ast
import difflib
import os
import shutil
import time
from datetime import datetime

ROOT_DIR    = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BACKUP_DIR  = os.path.join(ROOT_DIR, "data", "backups")


def _read_file(path: str) -> tuple[bool, str]:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return True, f.read()
    except Exception as e:
        return False, str(e)


def _write_file(path: str, content: str) -> tuple[bool, str]:
    try:
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        return True, "OK"
    except Exception as e:
        return False, str(e)


# ─── Tool 1: create_diff ─────────────────────────────────────────────────────
def create_diff(file_path: str, new_content: str) -> dict:
    """
    Buat unified diff antara konten file asli dan konten baru yang diajukan.
    Berguna untuk melihat perubahan sebelum menerapkannya.
    """
    if not os.path.isfile(file_path):
        return {"error": f"File tidak ditemukan: {file_path}"}

    ok, original = _read_file(file_path)
    if not ok:
        return {"error": original}

    orig_lines = original.splitlines(keepends=True)
    new_lines  = new_content.splitlines(keepends=True)

    diff = list(difflib.unified_diff(
        orig_lines, new_lines,
        fromfile=f"a/{os.path.basename(file_path)}",
        tofile=f"b/{os.path.basename(file_path)}",
        lineterm=""
    ))

    added   = sum(1 for l in diff if l.startswith("+") and not l.startswith("+++"))
    removed = sum(1 for l in diff if l.startswith("-") and not l.startswith("---"))

    return {
        "file": file_path,
        "diff": "\n".join(diff),
        "lines_added": added,
        "lines_removed": removed,
        "has_changes": len(diff) > 0
    }


# ─── Tool 2: apply_patch ──────────────────────────────────────────────────────
def apply_patch(file_path: str, new_content: str, backup: bool = True) -> dict:
    """
    Terapkan konten baru ke sebuah file. Secara default, buat backup otomatis dulu.
    Ini adalah cara terpilih untuk memodifikasi file kode secara programatik.
    """
    if not os.path.isfile(file_path):
        return {"error": f"File tidak ditemukan: {file_path}"}

    if backup:
        backup_result = backup_file(file_path)
        if not backup_result["success"]:
            return {"error": f"Gagal membuat backup: {backup_result['message']}"}

    ok, msg = _write_file(file_path, new_content)
    if not ok:
        return {"error": f"Gagal menulis file: {msg}"}

    return {
        "success": True,
        "file": file_path,
        "message": f"File berhasil diperbarui.",
        "backup_created": backup
    }


# ─── Tool 3: replace_function ────────────────────────────────────────────────
def replace_function(file_path: str, func_name: str, new_code: str) -> dict:
    """
    Ganti implementasi sebuah fungsi/kelas spesifik di dalam file
    tanpa menyentuh bagian kode lain. Ini adalah operasi bedah presisi.
    """
    if not os.path.isfile(file_path):
        return {"error": f"File tidak ditemukan: {file_path}"}

    ok, source = _read_file(file_path)
    if not ok:
        return {"error": source}

    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return {"error": f"Syntax error di file asli: {e}"}

    # Validasi kode baru
    try:
        ast.parse(new_code)
    except SyntaxError as e:
        return {"error": f"Syntax error di kode baru: {e}"}

    # Cari fungsi/kelas target
    target_node = None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name == func_name:
                target_node = node
                break

    if target_node is None:
        return {"error": f"Fungsi/kelas '{func_name}' tidak ditemukan di {file_path}"}

    # Buat backup
    backup_file(file_path)

    # Ganti baris target_node.lineno hingga target_node.end_lineno (1-indexed)
    lines = source.splitlines(keepends=True)
    start_idx = target_node.lineno - 1      # 0-indexed
    end_idx   = target_node.end_lineno      # exclusive

    # Preservasi indentasi dari baris pertama yang lama
    original_indent = ""
    if lines[start_idx]:
        original_indent = lines[start_idx][: len(lines[start_idx]) - len(lines[start_idx].lstrip())]

    # Tambahkan newline di akhir kode baru jika belum ada
    new_code_normalized = new_code.rstrip("\n") + "\n"

    new_lines = lines[:start_idx] + [new_code_normalized] + lines[end_idx:]
    new_source = "".join(new_lines)

    ok, msg = _write_file(file_path, new_source)
    if not ok:
        return {"error": f"Gagal menulis file: {msg}"}

    return {
        "success": True,
        "file": file_path,
        "replaced": func_name,
        "original_lines": f"{target_node.lineno}-{target_node.end_lineno}",
        "message": f"'{func_name}' berhasil diganti. Backup dibuat otomatis."
    }


# ─── Tool 4: insert_code_at_line ──────────────────────────────────────────────
def insert_code_at_line(file_path: str, line_number: int, code: str) -> dict:
    """
    Sisipkan blok kode pada baris tertentu (kode lama bergeser ke bawah).
    line_number menggunakan indeks 1-based (sama seperti editor teks).
    """
    if not os.path.isfile(file_path):
        return {"error": f"File tidak ditemukan: {file_path}"}

    ok, source = _read_file(file_path)
    if not ok:
        return {"error": source}

    lines = source.splitlines(keepends=True)
    if line_number < 1 or line_number > len(lines) + 1:
        return {"error": f"Nomor baris {line_number} di luar jangkauan (1-{len(lines)+1})."}

    backup_file(file_path)

    insert_block = code.rstrip("\n") + "\n"
    new_lines = lines[:line_number - 1] + [insert_block] + lines[line_number - 1:]
    new_source = "".join(new_lines)

    ok, msg = _write_file(file_path, new_source)
    if not ok:
        return {"error": f"Gagal menulis file: {msg}"}

    return {
        "success": True,
        "file": file_path,
        "inserted_at_line": line_number,
        "message": f"Kode berhasil disisipkan pada baris {line_number}."
    }


# ─── Tool 5: backup_file ─────────────────────────────────────────────────────
def backup_file(file_path: str) -> dict:
    """
    Simpan salinan cadangan file ke data/backups/ sebelum modifikasi.
    Format nama: <filename>.<timestamp>.bak
    """
    if not os.path.isfile(file_path):
        return {"success": False, "message": f"File tidak ditemukan: {file_path}"}

    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    basename  = os.path.basename(file_path)
    backup_path = os.path.join(BACKUP_DIR, f"{basename}.{timestamp}.bak")

    try:
        shutil.copy2(file_path, backup_path)
        return {
            "success": True,
            "original": file_path,
            "backup_path": backup_path,
            "message": f"Backup dibuat: {backup_path}"
        }
    except Exception as e:
        return {"success": False, "message": str(e)}


# ─── Tool 6: restore_file ────────────────────────────────────────────────────
def restore_file(file_path: str) -> dict:
    """
    Kembalikan file ke versi backup terakhir yang tersimpan di data/backups/.
    """
    basename = os.path.basename(file_path)
    if not os.path.isdir(BACKUP_DIR):
        return {"success": False, "message": "Direktori backup tidak ditemukan."}

    # Cari backup terbaru untuk file ini
    backups = sorted(
        [
            f for f in os.listdir(BACKUP_DIR)
            if f.startswith(basename + ".") and f.endswith(".bak")
        ],
        reverse=True  # terbaru di atas
    )

    if not backups:
        return {"success": False, "message": f"Tidak ada backup ditemukan untuk '{basename}'."}

    latest_backup = os.path.join(BACKUP_DIR, backups[0])
    try:
        shutil.copy2(latest_backup, file_path)
        return {
            "success": True,
            "restored_from": latest_backup,
            "file": file_path,
            "message": f"File berhasil dikembalikan dari backup: {backups[0]}"
        }
    except Exception as e:
        return {"success": False, "message": str(e)}


# ─── Tool 7: list_backups ────────────────────────────────────────────────────
def list_backups(file_path: str = None) -> dict:
    """Tampilkan daftar semua file backup yang tersedia."""
    if not os.path.isdir(BACKUP_DIR):
        return {"backups": [], "count": 0, "message": "Belum ada backup."}

    all_backups = []
    for fname in sorted(os.listdir(BACKUP_DIR), reverse=True):
        if not fname.endswith(".bak"):
            continue
        if file_path and not fname.startswith(os.path.basename(file_path)):
            continue
        fpath = os.path.join(BACKUP_DIR, fname)
        stat  = os.stat(fpath)
        all_backups.append({
            "name": fname,
            "path": fpath,
            "size_bytes": stat.st_size,
            "created": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        })

    return {"backups": all_backups[:30], "count": len(all_backups)}
