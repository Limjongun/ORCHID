"""
code_assistant/__init__.py
Mengekspor semua CODE_TOOLS dan CODE_TOOL_MAP untuk didaftarkan ke llm_engine.
"""
from plugins.code_assistant.executor import (
    run_python_code, run_python_file, install_package,
    start_repl_session, repl_send, repl_stop, check_venv_status
)
from plugins.code_assistant.analyzer import (
    analyze_python_file, find_function, lint_file,
    count_code_metrics, detect_imports, find_all_todos, check_syntax
)
from plugins.code_assistant.context_engine import (
    index_project, search_codebase, get_file_summary,
    find_usages, get_project_structure, get_dependency_graph
)
from plugins.code_assistant.diff_engine import (
    create_diff, apply_patch, replace_function,
    insert_code_at_line, backup_file, restore_file, list_backups
)
from plugins.code_assistant.test_runner import (
    run_pytest, run_single_test, generate_test_template, get_coverage_report
)

# ─── Tool Map ────────────────────────────────────────────────────────────────
CODE_TOOL_MAP = {
    # Executor
    "run_python_code":      run_python_code,
    "run_python_file":      run_python_file,
    "install_package":      install_package,
    "start_repl_session":   start_repl_session,
    "repl_send":            repl_send,
    "repl_stop":            repl_stop,
    "check_venv_status":    check_venv_status,
    # Analyzer
    "analyze_python_file":  analyze_python_file,
    "find_function":        find_function,
    "lint_file":            lint_file,
    "count_code_metrics":   count_code_metrics,
    "detect_imports":       detect_imports,
    "find_all_todos":       find_all_todos,
    "check_syntax":         check_syntax,
    # Context Engine
    "index_project":        index_project,
    "search_codebase":      search_codebase,
    "get_file_summary":     get_file_summary,
    "find_usages":          find_usages,
    "get_project_structure": get_project_structure,
    "get_dependency_graph": get_dependency_graph,
    # Diff Engine
    "create_diff":          create_diff,
    "apply_patch":          apply_patch,
    "replace_function":     replace_function,
    "insert_code_at_line":  insert_code_at_line,
    "backup_file":          backup_file,
    "restore_file":         restore_file,
    "list_backups":         list_backups,
    # Test Runner
    "run_pytest":           run_pytest,
    "run_single_test":      run_single_test,
    "generate_test_template": generate_test_template,
    "get_coverage_report":  get_coverage_report,
}

# ─── Tool Schemas (OpenAI Function Calling Format) ────────────────────────────
CODE_TOOLS = [
    # ── Executor ──
    {
        "type": "function",
        "function": {
            "name": "run_python_code",
            "description": "Jalankan kode Python di subprocess terisolasi (venv). Kembalikan stdout, stderr, exit_code, dan waktu eksekusi. Gunakan ini untuk testing cepat, debugging, atau menjalankan snippet kode.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Kode Python yang akan dijalankan"},
                    "timeout": {"type": "integer", "description": "Batas waktu dalam detik (default: 30)", "default": 30}
                },
                "required": ["code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_python_file",
            "description": "Jalankan file .py yang sudah ada pada disk dengan argumen opsional.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path absolut ke file Python"},
                    "args": {"type": "array", "items": {"type": "string"}, "description": "Argumen command line (opsional)", "default": []}
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "install_package",
            "description": "Install paket Python menggunakan pip ke dalam venv terisolasi ORCHID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "package_name": {"type": "string", "description": "Nama paket pip (misal: 'requests', 'numpy==1.24.0')"}
                },
                "required": ["package_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "start_repl_session",
            "description": "Mulai sesi Python REPL persisten. Variabel yang dibuat akan diingat antar pemanggilan repl_send — mirip seperti sesi Jupyter Notebook.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "repl_send",
            "description": "Kirim kode ke sesi REPL aktif dan tangkap output. Variabel dari pemanggilan sebelumnya tetap tersedia di memori sesi.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Kode Python yang dikirim ke REPL"}
                },
                "required": ["code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "repl_stop",
            "description": "Hentikan sesi REPL aktif dan bebaskan semua variabel dari memori.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_venv_status",
            "description": "Periksa status venv ORCHID: apakah sudah ada, path Python-nya, dan daftar paket yang terinstal.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    # ── Analyzer ──
    {
        "type": "function",
        "function": {
            "name": "analyze_python_file",
            "description": "Analisis struktur AST file Python. Kembalikan semua fungsi (dengan kompleksitas siklomatik), kelas, impor, dan variabel global. Gunakan ini sebelum memodifikasi file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path absolut ke file Python"}
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_function",
            "description": "Temukan deklarasi fungsi atau kelas spesifik dalam file, beserta nomor baris dan snippet kodenya.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path ke file Python"},
                    "func_name": {"type": "string", "description": "Nama fungsi atau kelas yang dicari"}
                },
                "required": ["file_path", "func_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "lint_file",
            "description": "Jalankan linting (pyflakes + cek sintaks AST) pada file Python dan kembalikan daftar error dan peringatan terstruktur.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path ke file Python"}
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "count_code_metrics",
            "description": "Kembalikan metrik kode: jumlah baris total/kode/komentar/kosong, jumlah fungsi, kelas, dan rata-rata kompleksitas siklomatik.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path ke file Python"}
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "detect_imports",
            "description": "Ekstrak semua impor dalam file dan kategorikan menjadi stdlib, third-party, atau internal (relatif).",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path ke file Python"}
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_all_todos",
            "description": "Cari semua komentar TODO, FIXME, HACK di seluruh file Python dalam sebuah direktori proyek secara rekursif.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "Path direktori proyek"}
                },
                "required": ["directory"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_syntax",
            "description": "Validasi sintaks kode Python tanpa menjalankannya. Kembalikan detail error jika ada.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code_string": {"type": "string", "description": "String kode Python yang akan divalidasi"}
                },
                "required": ["code_string"]
            }
        }
    },
    # ── Context Engine ──
    {
        "type": "function",
        "function": {
            "name": "index_project",
            "description": "Scan seluruh proyek secara rekursif dan buat peta proyek JSON (fungsi, kelas, impor per file). Gunakan ini pertama kali untuk memahami struktur proyek besar.",
            "parameters": {
                "type": "object",
                "properties": {
                    "root_path": {"type": "string", "description": "Path root direktori proyek"}
                },
                "required": ["root_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_codebase",
            "description": "Cari string atau pola regex di seluruh file kode dalam proyek. Kembalikan file, nomor baris, dan konteks sekitarnya. Mirip 'grep -n' tapi terstruktur.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "String atau pola regex yang dicari"},
                    "root_path": {"type": "string", "description": "Path root direktori proyek"},
                    "use_regex": {"type": "boolean", "description": "Gunakan regex (true) atau string literal (false)", "default": False},
                    "file_ext": {"type": "string", "description": "Ekstensi file yang dicari (default: .py)", "default": ".py"}
                },
                "required": ["query", "root_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_file_summary",
            "description": "Kembalikan ringkasan singkat sebuah file: tujuan, daftar fungsi publik, dan dependensinya.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path ke file"}
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_usages",
            "description": "Temukan semua lokasi di mana sebuah fungsi, kelas, atau variabel digunakan di seluruh proyek.",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol_name": {"type": "string", "description": "Nama fungsi, kelas, atau variabel yang dicari"},
                    "root_path": {"type": "string", "description": "Path root direktori proyek"}
                },
                "required": ["symbol_name", "root_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_project_structure",
            "description": "Tampilkan pohon direktori proyek secara visual terformat, dengan jumlah LOC per file kode.",
            "parameters": {
                "type": "object",
                "properties": {
                    "root_path": {"type": "string", "description": "Path root direktori proyek"},
                    "max_depth": {"type": "integer", "description": "Kedalaman pohon maksimal (default: 4)", "default": 4}
                },
                "required": ["root_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_dependency_graph",
            "description": "Buat graf dependensi impor antar file Python dalam proyek — tampilkan siapa mengimpor siapa.",
            "parameters": {
                "type": "object",
                "properties": {
                    "root_path": {"type": "string", "description": "Path root direktori proyek"}
                },
                "required": ["root_path"]
            }
        }
    },
    # ── Diff Engine ──
    {
        "type": "function",
        "function": {
            "name": "create_diff",
            "description": "Buat unified diff antara isi file asli dan konten baru yang diajukan. Gunakan untuk preview perubahan sebelum diterapkan.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path ke file asli"},
                    "new_content": {"type": "string", "description": "Konten baru yang akan dibandingkan"}
                },
                "required": ["file_path", "new_content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "apply_patch",
            "description": "Terapkan konten baru ke sebuah file. Secara default membuat backup otomatis terlebih dahulu. Gunakan ini untuk memodifikasi file secara keseluruhan.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path ke file yang akan dimodifikasi"},
                    "new_content": {"type": "string", "description": "Konten lengkap baru untuk file tersebut"},
                    "backup": {"type": "boolean", "description": "Buat backup otomatis (default: true)", "default": True}
                },
                "required": ["file_path", "new_content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "replace_function",
            "description": "Ganti implementasi sebuah fungsi atau kelas spesifik di dalam file TANPA menyentuh kode lainnya. Operasi bedah presisi — LEBIH AMAN daripada apply_patch untuk perubahan kecil.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path ke file Python"},
                    "func_name": {"type": "string", "description": "Nama fungsi atau kelas yang akan diganti"},
                    "new_code": {"type": "string", "description": "Kode baru untuk menggantikan fungsi/kelas tersebut"}
                },
                "required": ["file_path", "func_name", "new_code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "insert_code_at_line",
            "description": "Sisipkan blok kode pada nomor baris tertentu. Kode yang ada di bawah baris tersebut akan bergeser ke bawah.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path ke file"},
                    "line_number": {"type": "integer", "description": "Nomor baris tempat sisipan (1-based)"},
                    "code": {"type": "string", "description": "Kode yang akan disisipkan"}
                },
                "required": ["file_path", "line_number", "code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "backup_file",
            "description": "Simpan salinan cadangan file ke data/backups/ dengan timestamp. WAJIB dipanggil sebelum modifikasi kode penting.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path ke file yang akan di-backup"}
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "restore_file",
            "description": "Kembalikan file ke versi backup terakhir. Digunakan saat terjadi kesalahan modifikasi.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path ke file yang akan di-restore"}
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_backups",
            "description": "Tampilkan daftar semua file backup yang tersimpan di data/backups/.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Filter backup untuk file tertentu (opsional, kosongkan untuk semua backup)"}
                },
                "required": []
            }
        }
    },
    # ── Test Runner ──
    {
        "type": "function",
        "function": {
            "name": "run_pytest",
            "description": "Jalankan pytest pada direktori atau file test. Parse output menjadi struktur terformat: passed, failed, error, beserta traceback tiap kegagalan.",
            "parameters": {
                "type": "object",
                "properties": {
                    "test_path": {"type": "string", "description": "Path file atau direktori test"},
                    "verbose": {"type": "boolean", "description": "Tampilkan output verbose (default: true)", "default": True}
                },
                "required": ["test_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_single_test",
            "description": "Jalankan satu test case spesifik menggunakan pytest -k.",
            "parameters": {
                "type": "object",
                "properties": {
                    "test_file": {"type": "string", "description": "Path ke file test"},
                    "test_name": {"type": "string", "description": "Nama fungsi test (digunakan sebagai filter -k)"}
                },
                "required": ["test_file", "test_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_test_template",
            "description": "Analisis fungsi publik dalam sebuah file Python dan buat kerangka file test (test_<filename>.py) dengan stub test untuk tiap fungsi.",
            "parameters": {
                "type": "object",
                "properties": {
                    "source_file": {"type": "string", "description": "Path ke file Python yang akan dibuatkan test-nya"}
                },
                "required": ["source_file"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_coverage_report",
            "description": "Jalankan pytest dengan coverage dan kembalikan laporan code coverage per file. Membutuhkan paket pytest-cov.",
            "parameters": {
                "type": "object",
                "properties": {
                    "source_path": {"type": "string", "description": "Path source code yang ingin diukur coverage-nya"},
                    "test_path": {"type": "string", "description": "Path direktori test (opsional, default mencari di seluruh proyek)"}
                },
                "required": ["source_path"]
            }
        }
    },
]
