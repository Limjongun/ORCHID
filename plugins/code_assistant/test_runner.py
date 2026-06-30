"""
test_runner.py — Test Execution & Test Generation Engine
Menjalankan pytest dan meng-parse hasilnya menjadi struktur terformat.
"""
import ast
import os
import re
import subprocess
import sys
from typing import Any

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def _get_python() -> str:
    """Gunakan python dari venv jika tersedia, fallback ke system python."""
    venv_py_win = os.path.join(ROOT_DIR, "data", "code_venv", "Scripts", "python.exe")
    venv_py_unix = os.path.join(ROOT_DIR, "data", "code_venv", "bin", "python")
    if os.path.exists(venv_py_win):
        return venv_py_win
    if os.path.exists(venv_py_unix):
        return venv_py_unix
    return sys.executable

def _read_file(path: str) -> tuple[bool, str]:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return True, f.read()
    except Exception as e:
        return False, str(e)


# ─── Tool 1: run_pytest ──────────────────────────────────────────────────────
def run_pytest(test_path: str, verbose: bool = True, timeout: int = 120) -> dict:
    """
    Jalankan pytest pada path tertentu (file atau direktori).
    Parse output menjadi struktur terformat: total, passed, failed, error, beserta traceback.
    """
    if not os.path.exists(test_path):
        return {"error": f"Path tidak ditemukan: {test_path}"}

    python = _get_python()
    cmd = [python, "-m", "pytest", test_path, "--tb=short", "-q"]
    if verbose:
        cmd.append("-v")

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, cwd=ROOT_DIR
        )
        output = result.stdout + result.stderr

        # ── Parse ringkasan ──
        summary_match = re.search(
            r"(\d+) passed(?:,\s*(\d+) failed)?(?:,\s*(\d+) error)?(?:,\s*(\d+) warning)?",
            output
        )
        failed_match = re.search(r"(\d+) failed", output)
        error_match  = re.search(r"(\d+) error", output)

        passed  = int(summary_match.group(1)) if summary_match else 0
        failed  = int(failed_match.group(1)) if failed_match else 0
        errors  = int(error_match.group(1)) if error_match else 0
        total   = passed + failed + errors

        # ── Ekstrak traceback per test yang gagal ──
        failures = []
        fail_blocks = re.split(r"_{5,}", output)
        for block in fail_blocks:
            if "FAILED" in block or "ERROR" in block:
                test_match = re.search(r"(test_\w+(?:::\w+)?)", block)
                test_name = test_match.group(1) if test_match else "unknown"
                failures.append({
                    "test": test_name,
                    "traceback": block.strip()[:2000]
                })

        return {
            "success": result.returncode == 0,
            "exit_code": result.returncode,
            "total": total,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "failures": failures,
            "raw_output": output[:5000]
        }

    except subprocess.TimeoutExpired:
        return {"error": f"Timeout: pytest melebihi {timeout} detik."}
    except FileNotFoundError:
        return {"error": "pytest tidak ditemukan. Jalankan install_package('pytest') terlebih dahulu."}
    except Exception as e:
        return {"error": str(e)}


# ─── Tool 2: run_single_test ─────────────────────────────────────────────────
def run_single_test(test_file: str, test_name: str, timeout: int = 60) -> dict:
    """Jalankan satu test case spesifik menggunakan pytest -k."""
    if not os.path.isfile(test_file):
        return {"error": f"File tidak ditemukan: {test_file}"}

    python = _get_python()
    cmd = [python, "-m", "pytest", test_file, "-k", test_name, "-v", "--tb=long"]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, cwd=ROOT_DIR
        )
        output = result.stdout + result.stderr
        passed = "1 passed" in output
        failed = "1 failed" in output or "1 error" in output

        return {
            "test_name": test_name,
            "file": test_file,
            "passed": passed,
            "failed": failed,
            "exit_code": result.returncode,
            "output": output[:3000]
        }
    except Exception as e:
        return {"error": str(e)}


# ─── Tool 3: generate_test_template ──────────────────────────────────────────
def generate_test_template(source_file: str) -> dict:
    """
    Analisis fungsi dalam sebuah file dan buat kerangka file test
    dengan stub test untuk tiap fungsi publik yang terdeteksi.
    Simpan hasil sebagai test_<filename>.py di direktori yang sama.
    """
    if not os.path.isfile(source_file):
        return {"error": f"File tidak ditemukan: {source_file}"}

    ok, source = _read_file(source_file)
    if not ok:
        return {"error": source}

    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return {"error": f"Syntax error: {e}"}

    module_name = os.path.splitext(os.path.basename(source_file))[0]
    functions = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_"):  # hanya fungsi publik
                args = [a.arg for a in node.args.args if a.arg != "self"]
                functions.append({"name": node.name, "args": args})

    if not functions:
        return {
            "success": False,
            "message": f"Tidak ada fungsi publik ditemukan di {source_file} untuk dibuatkan test."
        }

    # ── Bangun konten file test ──
    lines = [
        f'"""',
        f'Auto-generated test template untuk: {module_name}.py',
        f'Generated oleh ORCHID Code Assistant',
        f'"""',
        f"import pytest",
        f"import sys",
        f"import os",
        f"",
        f"# Tambahkan path agar bisa mengimpor modul target",
        f"sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))",
        f"from {module_name} import {', '.join(f['name'] for f in functions)}",
        f"",
        f"",
    ]

    for fn in functions:
        arg_str = ", ".join(["None"] * len(fn["args"])) if fn["args"] else ""
        param_comment = f"  # args: {fn['args']}" if fn["args"] else ""
        lines += [
            f"class Test{fn['name'].title().replace('_', '')}:",
            f"    \"\"\"Test suite untuk fungsi '{fn['name']}'\"\"\"",
            f"",
            f"    def test_{fn['name']}_basic(self):{param_comment}",
            f"        # TODO: Ganti dengan input dan expected output yang sebenarnya",
            f"        result = {fn['name']}({arg_str})",
            f"        assert result is not None, \"Hasil tidak boleh None\"",
            f"",
            f"    def test_{fn['name']}_edge_case(self):",
            f"        # TODO: Tambahkan test untuk edge case (input kosong, None, dsb)",
            f"        pass",
            f"",
            f"",
        ]

    test_content = "\n".join(lines)

    # Simpan file test
    dir_path = os.path.dirname(source_file)
    test_file_path = os.path.join(dir_path, f"test_{module_name}.py")
    try:
        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write(test_content)
    except Exception as e:
        return {"error": f"Gagal menyimpan file test: {e}"}

    return {
        "success": True,
        "source_file": source_file,
        "test_file": test_file_path,
        "functions_covered": [f["name"] for f in functions],
        "test_count": len(functions) * 2,
        "message": f"Template test berhasil dibuat: {test_file_path} ({len(functions)*2} stub test)"
    }


# ─── Tool 4: get_coverage_report ─────────────────────────────────────────────
def get_coverage_report(source_path: str, test_path: str = None) -> dict:
    """
    Jalankan pytest dengan coverage dan kembalikan laporan per file.
    Membutuhkan: pip install pytest-cov
    """
    if not os.path.exists(source_path):
        return {"error": f"Path tidak ditemukan: {source_path}"}

    python = _get_python()
    cmd = [
        python, "-m", "pytest",
        test_path or ".",
        f"--cov={source_path}",
        "--cov-report=term-missing",
        "-q"
    ]
    if test_path:
        cmd[3] = test_path

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=180, cwd=ROOT_DIR
        )
        output = result.stdout + result.stderr

        # Parse tabel coverage (format: Name  Stmts  Miss  Cover)
        coverage_data = []
        in_table = False
        for line in output.splitlines():
            if line.startswith("Name") and "Stmts" in line:
                in_table = True
                continue
            if in_table:
                if line.startswith("-") or not line.strip():
                    continue
                if line.startswith("TOTAL"):
                    parts = line.split()
                    coverage_data.append({
                        "file": "TOTAL",
                        "stmts": parts[1] if len(parts) > 1 else "?",
                        "miss": parts[2] if len(parts) > 2 else "?",
                        "cover": parts[3] if len(parts) > 3 else "?"
                    })
                    break
                parts = line.split()
                if len(parts) >= 4:
                    coverage_data.append({
                        "file": parts[0],
                        "stmts": parts[1],
                        "miss": parts[2],
                        "cover": parts[3]
                    })

        total_line = next((c for c in coverage_data if c["file"] == "TOTAL"), None)
        return {
            "success": result.returncode == 0,
            "source_path": source_path,
            "total_coverage": total_line["cover"] if total_line else "N/A",
            "coverage_by_file": coverage_data,
            "raw_output": output[:3000]
        }

    except FileNotFoundError:
        return {"error": "pytest-cov tidak tersedia. Jalankan install_package('pytest-cov')."}
    except Exception as e:
        return {"error": str(e)}
