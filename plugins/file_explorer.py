import os

def list_directory(directory_path="."):
    """Mengembalikan daftar file dan folder di dalam direktori."""
    try:
        if not os.path.exists(directory_path):
            return f"Error: Direktori '{directory_path}' tidak ditemukan."
            
        items = os.listdir(directory_path)
        if not items:
            return f"Direktori '{directory_path}' kosong."
            
        result = []
        for item in items:
            full_path = os.path.join(directory_path, item)
            item_type = "📁" if os.path.isdir(full_path) else "📄"
            result.append(f"{item_type} {item}")
            
        return f"Isi direktori '{directory_path}':\n" + "\n".join(result)
    except Exception as e:
        return f"Gagal membaca direktori: {e}"

def read_file(file_path):
    """Membaca isi file teks."""
    try:
        if not os.path.exists(file_path):
            return f"Error: File '{file_path}' tidak ditemukan."
        if not os.path.isfile(file_path):
            return f"Error: '{file_path}' bukan sebuah file."
            
        # Membaca maksimal 5000 karakter agar tidak memenuhi konteks token
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read(5000)
            if len(f.read(1)) > 0:
                content += "\n\n... (file terpotong karena terlalu panjang)"
            return content
    except Exception as e:
        return f"Gagal membaca file (mungkin file biner atau tidak dapat diakses): {e}"

def search_files(query, directory_path="."):
    """Mencari file berdasarkan nama di dalam direktori dan subdirektori (maksimal kedalaman dangkal)."""
    try:
        if not os.path.exists(directory_path):
            return f"Error: Direktori '{directory_path}' tidak ditemukan."
            
        results = []
        # Batasi rekursi dan jumlah hasil agar tidak berat
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                if query.lower() in file.lower():
                    results.append(os.path.join(root, file))
                    
                if len(results) >= 50: # Limit hasil
                    break
            if len(results) >= 50:
                break
                
        if not results:
            return f"Tidak ditemukan file dengan nama mengandung '{query}' di '{directory_path}'."
            
        return f"Ditemukan {len(results)} file:\n" + "\n".join(results)
    except Exception as e:
        return f"Gagal mencari file: {e}"

FILE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "Menampilkan daftar file dan folder di dalam sebuah direktori.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory_path": {
                        "type": "string",
                        "description": "Path absolut atau relatif dari direktori yang ingin dilihat isinya. Contoh: '.', 'C:\\Users\\ALIM\\Downloads'."
                    }
                },
                "required": ["directory_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Membaca isi sebuah file teks (.py, .txt, .json, .md, dll).",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path lengkap ke file yang ingin dibaca."
                    }
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_files",
            "description": "Mencari file berdasarkan nama atau sebagian nama di dalam sebuah direktori.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Kata kunci pencarian nama file."
                    },
                    "directory_path": {
                        "type": "string",
                        "description": "Direktori tempat pencarian dilakukan."
                    }
                },
                "required": ["query", "directory_path"]
            }
        }
    }
]

FILE_TOOL_MAP = {
    "list_directory": list_directory,
    "read_file": read_file,
    "search_files": search_files
}
