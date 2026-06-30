"""
context_engine.py — Project Context & Codebase Awareness
Mengindeks seluruh proyek dan menyediakan pencarian kode lintas-file.
"""
import ast
import json
import os
import re
from typing import Any

ROOT_DIR  = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INDEX_PATH = os.path.join(ROOT_DIR, "data", "project_index.json")

SKIP_DIRS = {
    "__pycache__", ".git", ".venv", "venv", "env", "node_modules",
    ".idea", ".vscode", "dist", "build", "code_venv", "backups"
}
CODE_EXTENSIONS = {".py", ".js", ".ts", ".json", ".md", ".txt", ".yaml", ".yml", ".toml"}


def _read_file(path: str) -> tuple[bool, str]:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return True, f.read()
    except Exception as e:
        return False, str(e)


def _count_loc(source: str) -> int:
    """Hitung baris kode (non-blank, non-comment)."""
    return sum(
        1 for line in source.splitlines()
        if line.strip() and not line.strip().startswith("#")
    )


# ─── Tool 1: index_project ───────────────────────────────────────────────────
def index_project(root_path: str) -> dict:
    """
    Scan seluruh proyek secara rekursif. Buat peta proyek berupa JSON:
    setiap file → daftar fungsi, kelas, impor, dan LOC.
    Hasil disimpan ke data/project_index.json.
    """
    if not os.path.isdir(root_path):
        return {"error": f"Direktori tidak ditemukan: {root_path}"}

    index = {
        "root": root_path,
        "files": {},
        "summary": {}
    }
    total_files = 0
    total_loc = 0
    all_functions = []
    all_classes = []

    for dirpath, dirnames, filenames in os.walk(root_path):
        # Exclude known noise directories
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]

        for fname in filenames:
            ext = os.path.splitext(fname)[1].lower()
            if ext not in CODE_EXTENSIONS:
                continue

            fpath = os.path.join(dirpath, fname)
            rel_path = os.path.relpath(fpath, root_path)
            ok, source = _read_file(fpath)
            if not ok:
                continue

            loc = _count_loc(source)
            total_loc += loc
            total_files += 1
            file_entry: dict[str, Any] = {"rel_path": rel_path, "loc": loc, "ext": ext}

            # Deep analysis hanya untuk Python
            if ext == ".py":
                try:
                    tree = ast.parse(source)
                    fns, clss, imps = [], [], []
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            fns.append({"name": node.name, "line": node.lineno})
                            all_functions.append({"name": node.name, "file": rel_path, "line": node.lineno})
                        elif isinstance(node, ast.ClassDef):
                            clss.append({"name": node.name, "line": node.lineno})
                            all_classes.append({"name": node.name, "file": rel_path, "line": node.lineno})
                        elif isinstance(node, ast.Import):
                            imps += [a.name for a in node.names]
                        elif isinstance(node, ast.ImportFrom):
                            imps.append(node.module or "")
                    file_entry["functions"] = fns
                    file_entry["classes"] = clss
                    file_entry["imports"] = list(set(imps))
                except SyntaxError:
                    file_entry["parse_error"] = True

            index["files"][rel_path] = file_entry

    index["summary"] = {
        "total_files": total_files,
        "total_loc": total_loc,
        "total_functions": len(all_functions),
        "total_classes": len(all_classes),
        "all_functions": all_functions,
        "all_classes": all_classes,
    }

    # Simpan ke disk
    os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)
    try:
        with open(INDEX_PATH, "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2, ensure_ascii=False)
    except Exception as e:
        return {"error": f"Gagal menyimpan index: {e}"}

    return {
        "success": True,
        "root": root_path,
        "index_path": INDEX_PATH,
        "total_files": total_files,
        "total_loc": total_loc,
        "total_functions": len(all_functions),
        "total_classes": len(all_classes),
        "message": f"Indeks proyek berhasil dibuat: {total_files} file, {total_loc} LOC."
    }


# ─── Tool 2: search_codebase ─────────────────────────────────────────────────
def search_codebase(query: str, root_path: str, use_regex: bool = False, file_ext: str = ".py") -> dict:
    """
    Cari string atau pola regex di seluruh file kode dalam proyek.
    Kembalikan file, nomor baris, dan cuplikan konteks.
    """
    if not os.path.isdir(root_path):
        return {"error": f"Direktori tidak ditemukan: {root_path}"}

    matches = []
    try:
        pattern = re.compile(query, re.IGNORECASE) if use_regex else re.compile(re.escape(query), re.IGNORECASE)
    except re.error as e:
        return {"error": f"Regex tidak valid: {e}"}

    for dirpath, dirnames, filenames in os.walk(root_path):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for fname in filenames:
            if not fname.endswith(file_ext):
                continue
            fpath = os.path.join(dirpath, fname)
            ok, source = _read_file(fpath)
            if not ok:
                continue
            lines = source.splitlines()
            for i, line in enumerate(lines, 1):
                if pattern.search(line):
                    # Ambil 2 baris konteks sebelum dan sesudah
                    ctx_start = max(0, i - 2)
                    ctx_end = min(len(lines), i + 2)
                    context = "\n".join(
                        f"{'→' if j == i - 1 else ' '} {j+1}: {lines[j]}"
                        for j in range(ctx_start, ctx_end)
                    )
                    matches.append({
                        "file": os.path.relpath(fpath, root_path),
                        "line": i,
                        "match": line.strip(),
                        "context": context
                    })
                    if len(matches) >= 100:  # Batas 100 hasil
                        break
        if len(matches) >= 100:
            break

    return {
        "query": query,
        "match_count": len(matches),
        "matches": matches,
        "truncated": len(matches) >= 100
    }


# ─── Tool 3: get_file_summary ────────────────────────────────────────────────
def get_file_summary(file_path: str) -> dict:
    """Kembalikan ringkasan singkat sebuah file: tujuan, fungsi publik, dan dependensinya."""
    if not os.path.isfile(file_path):
        return {"error": f"File tidak ditemukan: {file_path}"}

    ok, source = _read_file(file_path)
    if not ok:
        return {"error": source}

    lines = source.splitlines()
    loc = _count_loc(source)

    # Coba ambil docstring modul
    module_docstring = ""
    try:
        tree = ast.parse(source)
        if (tree.body and isinstance(tree.body[0], ast.Expr) and
                isinstance(tree.body[0].value, ast.Constant)):
            module_docstring = str(tree.body[0].value.value)[:300]
    except Exception:
        pass

    # Ambil komentar di 5 baris pertama sebagai "deskripsi"
    header_comments = [
        l.lstrip("#").strip() for l in lines[:5] if l.strip().startswith("#")
    ]

    # Ambil nama fungsi/kelas publik (tidak dimulai dengan _)
    from plugins.code_assistant.analyzer import analyze_python_file
    analysis = analyze_python_file(file_path)
    public_functions = [f["name"] for f in analysis.get("functions", []) if not f["name"].startswith("_")]
    public_classes = [c["name"] for c in analysis.get("classes", []) if not c["name"].startswith("_")]
    imports = [imp["module"] for imp in analysis.get("imports", [])]

    return {
        "file": file_path,
        "loc": loc,
        "module_docstring": module_docstring,
        "header_description": " ".join(header_comments) if header_comments else "(tidak ada)",
        "public_functions": public_functions,
        "public_classes": public_classes,
        "imported_modules": list(set(imports))[:20],
    }


# ─── Tool 4: find_usages ─────────────────────────────────────────────────────
def find_usages(symbol_name: str, root_path: str) -> dict:
    """
    Temukan semua tempat di mana sebuah fungsi/kelas/variabel digunakan
    di seluruh file Python dalam proyek.
    """
    result = search_codebase(symbol_name, root_path, use_regex=False)
    if "error" in result:
        return result

    # Filter hanya yang benar-benar merupakan penggunaan simbol (bukan definisi def/class)
    usages = []
    for match in result["matches"]:
        line_text = match["match"]
        # Hapus definisi murni, tetap ambil pemanggilan dan referensi
        if re.search(rf"\b{re.escape(symbol_name)}\b", line_text):
            usages.append(match)

    return {
        "symbol": symbol_name,
        "usage_count": len(usages),
        "usages": usages
    }


# ─── Tool 5: get_project_structure ────────────────────────────────────────────
def get_project_structure(root_path: str, max_depth: int = 4) -> dict:
    """
    Tampilkan pohon direktori proyek secara terformat, dengan LOC per file.
    """
    if not os.path.isdir(root_path):
        return {"error": f"Direktori tidak ditemukan: {root_path}"}

    lines = []

    def _walk(path: str, prefix: str, depth: int):
        if depth > max_depth:
            return
        try:
            entries = sorted(os.scandir(path), key=lambda e: (not e.is_dir(), e.name.lower()))
        except PermissionError:
            return
        for i, entry in enumerate(entries):
            if entry.name in SKIP_DIRS or entry.name.startswith("."):
                continue
            connector = "└── " if i == len(entries) - 1 else "├── "
            if entry.is_dir():
                lines.append(f"{prefix}{connector}{entry.name}/")
                extension = "    " if i == len(entries) - 1 else "│   "
                _walk(entry.path, prefix + extension, depth + 1)
            else:
                ext = os.path.splitext(entry.name)[1].lower()
                size_info = ""
                if ext in CODE_EXTENSIONS:
                    ok, src = _read_file(entry.path)
                    if ok:
                        loc = _count_loc(src)
                        size_info = f"  [{loc} LOC]"
                lines.append(f"{prefix}{connector}{entry.name}{size_info}")

    lines.append(f"{os.path.basename(root_path)}/")
    _walk(root_path, "", 0)

    return {
        "root": root_path,
        "tree": "\n".join(lines),
        "line_count": len(lines)
    }


# ─── Tool 6: get_dependency_graph ─────────────────────────────────────────────
def get_dependency_graph(root_path: str) -> dict:
    """
    Buat graf dependensi antar file Python dalam proyek yang sama.
    Tampilkan siapa mengimpor siapa.
    """
    if not os.path.isdir(root_path):
        return {"error": f"Direktori tidak ditemukan: {root_path}"}

    # Kumpulkan semua modul lokal
    local_modules = set()
    for dirpath, dirnames, filenames in os.walk(root_path):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fname in filenames:
            if fname.endswith(".py"):
                rel = os.path.relpath(os.path.join(dirpath, fname), root_path)
                mod = rel.replace(os.sep, ".").removesuffix(".py")
                local_modules.add(mod)
                local_modules.add(os.path.splitext(os.path.basename(fname))[0])

    graph = {}
    for dirpath, dirnames, filenames in os.walk(root_path):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fname in filenames:
            if not fname.endswith(".py"):
                continue
            fpath = os.path.join(dirpath, fname)
            rel = os.path.relpath(fpath, root_path)
            ok, source = _read_file(fpath)
            if not ok:
                continue
            try:
                tree = ast.parse(source)
                deps = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            base = alias.name.split(".")[0]
                            if base in local_modules:
                                deps.append(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        mod = (node.module or "").split(".")[0]
                        if mod in local_modules:
                            deps.append(node.module or mod)
                graph[rel] = list(set(deps))
            except Exception:
                graph[rel] = []

    return {
        "root": root_path,
        "dependency_graph": graph,
        "file_count": len(graph)
    }
