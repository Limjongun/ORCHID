"""
analyzer.py — Static Code Analyzer
Menganalisis struktur Python menggunakan AST tanpa menjalankan kode.
"""
import ast
import os
import re
import subprocess
import sys
from typing import Any

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _read_file(file_path: str) -> tuple[bool, str]:
    """Baca file dengan aman, kembalikan (ok, konten/pesan_error)."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return True, f.read()
    except Exception as e:
        return False, str(e)


# ─── Tool 1: analyze_python_file ─────────────────────────────────────────────
def analyze_python_file(file_path: str) -> dict:
    """
    Parse AST file Python. Kembalikan daftar lengkap:
    fungsi, kelas, impor, global var, dan kompleksitas siklomatik per fungsi.
    """
    ok, source = _read_file(file_path)
    if not ok:
        return {"error": source}

    try:
        tree = ast.parse(source, filename=file_path)
    except SyntaxError as e:
        return {"error": f"Syntax error: {e}"}

    functions = []
    classes = []
    imports = []
    global_vars = []

    for node in ast.walk(tree):
        # ── Fungsi ──
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Hanya ambil fungsi top-level dan method langsung di kelas
            args = [arg.arg for arg in node.args.args]
            complexity = _cyclomatic_complexity(node)
            functions.append({
                "name": node.name,
                "line_start": node.lineno,
                "line_end": node.end_lineno,
                "args": args,
                "is_async": isinstance(node, ast.AsyncFunctionDef),
                "has_docstring": (
                    isinstance(node.body[0], ast.Expr) and
                    isinstance(node.body[0].value, ast.Constant)
                ) if node.body else False,
                "cyclomatic_complexity": complexity,
                "decorators": [ast.unparse(d) for d in node.decorator_list]
            })

        # ── Kelas ──
        elif isinstance(node, ast.ClassDef):
            methods = [
                n.name for n in node.body
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]
            classes.append({
                "name": node.name,
                "line_start": node.lineno,
                "line_end": node.end_lineno,
                "methods": methods,
                "base_classes": [ast.unparse(b) for b in node.bases],
                "decorators": [ast.unparse(d) for d in node.decorator_list]
            })

        # ── Impor ──
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imports.append({"module": alias.name, "alias": alias.asname, "type": "import"})
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                imports.append({
                    "module": module,
                    "name": alias.name,
                    "alias": alias.asname,
                    "type": "from_import"
                })

    # ── Global vars (top-level assignment) ──
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    global_vars.append({"name": target.id, "line": node.lineno})

    lines = source.splitlines()
    return {
        "file_path": file_path,
        "total_lines": len(lines),
        "functions": functions,
        "classes": classes,
        "imports": imports,
        "global_vars": global_vars,
        "function_count": len(functions),
        "class_count": len(classes),
    }


def _cyclomatic_complexity(func_node: ast.AST) -> int:
    """
    Hitung kompleksitas siklomatik (McCabe) sebuah fungsi.
    Setiap if/elif/for/while/except/and/or menambah 1.
    """
    count = 1  # basis
    branch_nodes = (
        ast.If, ast.For, ast.AsyncFor, ast.While,
        ast.ExceptHandler, ast.With, ast.AsyncWith,
        ast.Assert, ast.comprehension
    )
    for node in ast.walk(func_node):
        if isinstance(node, branch_nodes):
            count += 1
        elif isinstance(node, ast.BoolOp):
            count += len(node.values) - 1
    return count


# ─── Tool 2: find_function ────────────────────────────────────────────────────
def find_function(file_path: str, func_name: str) -> dict:
    """Temukan deklarasi fungsi/kelas spesifik beserta rentang barisnya."""
    analysis = analyze_python_file(file_path)
    if "error" in analysis:
        return analysis

    # Cari di fungsi
    for fn in analysis["functions"]:
        if fn["name"] == func_name:
            ok, source = _read_file(file_path)
            lines = source.splitlines()
            snippet = "\n".join(lines[fn["line_start"] - 1: fn["line_end"]])
            return {
                "found": True,
                "type": "function",
                "name": func_name,
                "line_start": fn["line_start"],
                "line_end": fn["line_end"],
                "snippet": snippet
            }
    # Cari di kelas
    for cls in analysis["classes"]:
        if cls["name"] == func_name:
            ok, source = _read_file(file_path)
            lines = source.splitlines()
            snippet = "\n".join(lines[cls["line_start"] - 1: cls["line_end"]])
            return {
                "found": True,
                "type": "class",
                "name": func_name,
                "line_start": cls["line_start"],
                "line_end": cls["line_end"],
                "snippet": snippet
            }
    return {"found": False, "error": f"'{func_name}' tidak ditemukan di {file_path}"}


# ─── Tool 3: lint_file ────────────────────────────────────────────────────────
def lint_file(file_path: str) -> dict:
    """Jalankan pyflakes untuk linting dan kembalikan daftar error terstruktur."""
    if not os.path.isfile(file_path):
        return {"error": f"File tidak ditemukan: {file_path}"}

    issues = []

    # ── pyflakes (via subprocess agar tidak tergantung installasi) ──
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pyflakes", file_path],
            capture_output=True, text=True, timeout=15
        )
        if result.stdout.strip():
            for line in result.stdout.strip().splitlines():
                # Format pyflakes: filepath:line: message
                match = re.match(r".+:(\d+):\d*:?\s*(.*)", line)
                if match:
                    issues.append({
                        "tool": "pyflakes",
                        "line": int(match.group(1)),
                        "message": match.group(2).strip(),
                        "severity": "warning"
                    })
                else:
                    issues.append({"tool": "pyflakes", "line": 0, "message": line, "severity": "warning"})
    except FileNotFoundError:
        issues.append({"tool": "pyflakes", "line": 0, "message": "pyflakes tidak terinstal. Jalankan: pip install pyflakes", "severity": "info"})
    except Exception as e:
        issues.append({"tool": "pyflakes", "line": 0, "message": str(e), "severity": "error"})

    # ── Cek syntax via ast ──
    ok, source = _read_file(file_path)
    if ok:
        try:
            ast.parse(source)
        except SyntaxError as e:
            issues.insert(0, {
                "tool": "syntax",
                "line": e.lineno or 0,
                "message": f"SyntaxError: {e.msg}",
                "severity": "error"
            })

    return {
        "file": file_path,
        "issue_count": len(issues),
        "issues": issues,
        "clean": len(issues) == 0
    }


# ─── Tool 4: count_code_metrics ──────────────────────────────────────────────
def count_code_metrics(file_path: str) -> dict:
    """Kembalikan metrik kode: total baris, baris kode, komentar, kosong, jumlah fungsi/kelas."""
    ok, source = _read_file(file_path)
    if not ok:
        return {"error": source}

    lines = source.splitlines()
    total = len(lines)
    blank = sum(1 for l in lines if l.strip() == "")
    comment = sum(1 for l in lines if l.strip().startswith("#"))
    code = total - blank - comment

    analysis = analyze_python_file(file_path)
    func_count = analysis.get("function_count", 0)
    class_count = analysis.get("class_count", 0)

    avg_complexity = 0
    fns = analysis.get("functions", [])
    if fns:
        avg_complexity = round(sum(f["cyclomatic_complexity"] for f in fns) / len(fns), 2)

    return {
        "file": file_path,
        "total_lines": total,
        "code_lines": code,
        "comment_lines": comment,
        "blank_lines": blank,
        "function_count": func_count,
        "class_count": class_count,
        "avg_cyclomatic_complexity": avg_complexity,
        "has_high_complexity": any(f["cyclomatic_complexity"] > 10 for f in fns)
    }


# ─── Tool 5: detect_imports ───────────────────────────────────────────────────
def detect_imports(file_path: str) -> dict:
    """
    Ekstrak semua impor dan kategorikan: stdlib, third-party, atau internal (relatif).
    """
    analysis = analyze_python_file(file_path)
    if "error" in analysis:
        return analysis

    import sys as _sys
    stdlib_modules = set(_sys.stdlib_module_names) if hasattr(_sys, "stdlib_module_names") else set()

    stdlib, third_party, internal = [], [], []

    for imp in analysis["imports"]:
        mod = imp["module"].split(".")[0]
        if imp["type"] == "from_import" and imp["module"].startswith("."):
            internal.append(imp)
        elif mod in stdlib_modules:
            stdlib.append(imp)
        else:
            third_party.append(imp)

    return {
        "file": file_path,
        "stdlib": stdlib,
        "third_party": third_party,
        "internal_relative": internal,
        "total_imports": len(analysis["imports"])
    }


# ─── Tool 6: find_all_todos ───────────────────────────────────────────────────
def find_all_todos(directory: str) -> dict:
    """
    Cari semua komentar TODO, FIXME, HACK, NOQA di seluruh file Python dalam direktori.
    """
    if not os.path.isdir(directory):
        return {"error": f"Direktori tidak ditemukan: {directory}"}

    pattern = re.compile(r"#\s*(TODO|FIXME|HACK|XXX|NOQA)[\s:]*(.*)", re.IGNORECASE)
    results = []

    for root, dirs, files in os.walk(directory):
        # Skip hidden & pycache
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]
        for fname in files:
            if not fname.endswith(".py"):
                continue
            fpath = os.path.join(root, fname)
            ok, source = _read_file(fpath)
            if not ok:
                continue
            for i, line in enumerate(source.splitlines(), 1):
                match = pattern.search(line)
                if match:
                    results.append({
                        "file": fpath,
                        "line": i,
                        "tag": match.group(1).upper(),
                        "message": match.group(2).strip(),
                        "context": line.strip()
                    })

    return {"directory": directory, "count": len(results), "todos": results}


# ─── Tool 7: check_syntax ─────────────────────────────────────────────────────
def check_syntax(code_string: str) -> dict:
    """Validasi sintaks Python tanpa menjalankan kode. Kembalikan error jika ada."""
    try:
        ast.parse(code_string)
        return {"valid": True, "message": "Sintaks valid, tidak ada error."}
    except SyntaxError as e:
        return {
            "valid": False,
            "error_type": "SyntaxError",
            "message": e.msg,
            "line": e.lineno,
            "offset": e.offset,
            "text": e.text
        }
    except Exception as e:
        return {"valid": False, "error_type": type(e).__name__, "message": str(e)}
