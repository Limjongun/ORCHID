import os
import shutil
import zipfile

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
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read(5000)
            if len(f.read(1)) > 0:
                content += "\n\n... (file terpotong karena terlalu panjang)"
            return content
    except Exception as e:
        return f"Gagal membaca file: {e}"

def search_files(query, directory_path="."):
    """Mencari file berdasarkan nama."""
    try:
        if not os.path.exists(directory_path):
            return f"Error: Direktori '{directory_path}' tidak ditemukan."
            
        results = []
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                if query.lower() in file.lower():
                    results.append(os.path.join(root, file))
                if len(results) >= 50:
                    break
            if len(results) >= 50:
                break
                
        if not results:
            return f"Tidak ditemukan file dengan nama mengandung '{query}'."
            
        return f"Ditemukan {len(results)} file:\n" + "\n".join(results)
    except Exception as e:
        return f"Gagal mencari file: {e}"

def write_file(file_path, content):
    """Membuat file baru atau menimpa file yang sudah ada."""
    try:
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Sukses menulis konten ke '{file_path}'."
    except Exception as e:
        return f"Gagal menulis ke file: {e}"

def create_directory(dir_path):
    """Membuat direktori baru."""
    try:
        os.makedirs(dir_path, exist_ok=True)
        return f"Sukses membuat direktori '{dir_path}'."
    except Exception as e:
        return f"Gagal membuat direktori: {e}"

def delete_file_or_folder(path):
    """Menghapus file atau folder."""
    try:
        if not os.path.exists(path):
            return f"Error: '{path}' tidak ditemukan."
        if os.path.isdir(path):
            shutil.rmtree(path)
            return f"Sukses menghapus folder '{path}' beserta isinya."
        else:
            os.remove(path)
            return f"Sukses menghapus file '{path}'."
    except Exception as e:
        return f"Gagal menghapus '{path}': {e}"

def move_rename_item(src, dest):
    """Memindahkan atau mengubah nama file/folder."""
    try:
        if not os.path.exists(src):
            return f"Error: Sumber '{src}' tidak ditemukan."
        shutil.move(src, dest)
        return f"Sukses memindahkan/mengubah nama dari '{src}' ke '{dest}'."
    except Exception as e:
        return f"Gagal memindahkan/mengubah nama: {e}"

def compress_to_zip(folder_path, output_zip):
    """Mengompresi direktori ke dalam file .zip."""
    try:
        if not os.path.exists(folder_path):
            return f"Error: Folder '{folder_path}' tidak ditemukan."
        
        if not output_zip.endswith('.zip'):
            output_zip += '.zip'
            
        with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, folder_path)
                    zipf.write(file_path, arcname)
        return f"Sukses mengompresi '{folder_path}' menjadi '{output_zip}'."
    except Exception as e:
        return f"Gagal mengompresi ke zip: {e}"

FILE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "Menampilkan daftar file dan folder di dalam sebuah direktori.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory_path": {"type": "string", "description": "Path direktori yang ingin dilihat isinya."}
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
                    "file_path": {"type": "string", "description": "Path file yang ingin dibaca."}
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_files",
            "description": "Mencari file berdasarkan nama di dalam sebuah direktori.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Kata kunci pencarian."},
                    "directory_path": {"type": "string", "description": "Direktori tempat pencarian."}
                },
                "required": ["query", "directory_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Membuat file teks baru atau menimpa isi file teks yang ada.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path absolut file yang akan dibuat/ditulis."},
                    "content": {"type": "string", "description": "Isi teks yang akan dituliskan ke dalam file."}
                },
                "required": ["file_path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_directory",
            "description": "Membuat direktori/folder baru.",
            "parameters": {
                "type": "object",
                "properties": {
                    "dir_path": {"type": "string", "description": "Path direktori yang akan dibuat."}
                },
                "required": ["dir_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_file_or_folder",
            "description": "Menghapus file atau folder beserta isinya.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path file atau folder yang akan dihapus."}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "move_rename_item",
            "description": "Memindahkan atau mengubah nama file/folder.",
            "parameters": {
                "type": "object",
                "properties": {
                    "src": {"type": "string", "description": "Path file/folder sumber asal."},
                    "dest": {"type": "string", "description": "Path tujuan atau nama baru."}
                },
                "required": ["src", "dest"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "compress_to_zip",
            "description": "Mengompresi sebuah folder menjadi file .zip.",
            "parameters": {
                "type": "object",
                "properties": {
                    "folder_path": {"type": "string", "description": "Folder sumber yang akan dikompresi."},
                    "output_zip": {"type": "string", "description": "Nama file output .zip (misal: 'backup.zip')."}
                },
                "required": ["folder_path", "output_zip"]
            }
        }
    }
]

FILE_TOOL_MAP = {
    "list_directory": list_directory,
    "read_file": read_file,
    "search_files": search_files,
    "write_file": write_file,
    "create_directory": create_directory,
    "delete_file_or_folder": delete_file_or_folder,
    "move_rename_item": move_rename_item,
    "compress_to_zip": compress_to_zip
}
