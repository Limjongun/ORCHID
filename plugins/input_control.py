"""
Plugin: input_control.py
Memberikan agen AI kemampuan untuk mengontrol mouse dan keyboard
layaknya operator komputer manusia (RPA - Robotic Process Automation).
"""
import time

try:
    import pyautogui
    # Nonaktifkan fail-safe bawaan pyautogui yang kadang mengganggu agen
    # (menggerakkan mouse ke sudut kiri atas akan memicu FailSafeException)
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.1  # Jeda kecil antar aksi agar lebih natural
    HAS_PYAUTOGUI = True
except ImportError:
    HAS_PYAUTOGUI = False

def _check() -> bool:
    if not HAS_PYAUTOGUI:
        return False, "Library 'pyautogui' belum diinstal. Jalankan: pip install pyautogui"
    return True, None

# ── Mouse Tools ───────────────────────────────────────────────────────────────

def mouse_move(x: int, y: int) -> str:
    """Gerakkan kursor mouse ke koordinat layar (x, y)."""
    ok, err = _check()
    if not ok: return err
    try:
        pyautogui.moveTo(x, y, duration=0.3)
        return f"Kursor berhasil dipindahkan ke koordinat ({x}, {y})."
    except Exception as e:
        return f"Gagal menggerakkan mouse: {e}"

def mouse_click(x: int, y: int, button: str = "left") -> str:
    """Klik mouse pada koordinat (x, y). Button: 'left', 'right', atau 'middle'."""
    ok, err = _check()
    if not ok: return err
    try:
        pyautogui.click(x, y, button=button)
        return f"Klik '{button}' berhasil pada koordinat ({x}, {y})."
    except Exception as e:
        return f"Gagal mengklik: {e}"

def mouse_double_click(x: int, y: int) -> str:
    """Klik dua kali (double click) pada koordinat (x, y)."""
    ok, err = _check()
    if not ok: return err
    try:
        pyautogui.doubleClick(x, y)
        return f"Double-click berhasil pada koordinat ({x}, {y})."
    except Exception as e:
        return f"Gagal double-click: {e}"

def mouse_right_click(x: int, y: int) -> str:
    """Klik kanan (right click) pada koordinat (x, y) untuk membuka context menu."""
    ok, err = _check()
    if not ok: return err
    try:
        pyautogui.rightClick(x, y)
        return f"Klik kanan berhasil pada ({x}, {y})."
    except Exception as e:
        return f"Gagal klik kanan: {e}"

def mouse_drag(from_x: int, from_y: int, to_x: int, to_y: int) -> str:
    """Klik tahan dan seret (drag) dari satu koordinat ke koordinat lain."""
    ok, err = _check()
    if not ok: return err
    try:
        pyautogui.drag(from_x - to_x, from_y - to_y, duration=0.5, button='left',
                       startX=from_x, startY=from_y)
        return f"Drag berhasil dari ({from_x}, {from_y}) ke ({to_x}, {to_y})."
    except Exception as e:
        return f"Gagal drag: {e}"

def scroll(x: int, y: int, amount: int) -> str:
    """Scroll di posisi (x, y). amount positif = scroll ke atas, negatif = ke bawah."""
    ok, err = _check()
    if not ok: return err
    try:
        pyautogui.scroll(amount, x=x, y=y)
        direction = "atas" if amount > 0 else "bawah"
        return f"Scroll ke {direction} sebanyak {abs(amount)} unit pada ({x}, {y})."
    except Exception as e:
        return f"Gagal scroll: {e}"

def get_mouse_position() -> str:
    """Mendapatkan posisi kursor mouse saat ini."""
    ok, err = _check()
    if not ok: return err
    try:
        pos = pyautogui.position()
        return f"Posisi kursor mouse saat ini: x={pos.x}, y={pos.y}"
    except Exception as e:
        return f"Gagal membaca posisi mouse: {e}"

# ── Keyboard Tools ────────────────────────────────────────────────────────────

def keyboard_type(text: str, interval: float = 0.05) -> str:
    """Mengetikkan teks seolah-olah diketik dari keyboard."""
    ok, err = _check()
    if not ok: return err
    try:
        pyautogui.typewrite(text, interval=interval)
        return f"Teks berhasil diketik: '{text[:50]}{'...' if len(text) > 50 else ''}'"
    except Exception as e:
        # Fallback untuk karakter Unicode (typewrite tidak support non-ASCII)
        try:
            import pyperclip
            pyperclip.copy(text)
            pyautogui.hotkey('ctrl', 'v')
            return f"Teks berhasil ditempelkan via clipboard: '{text[:50]}...'"
        except Exception as e2:
            return f"Gagal mengetik teks: {e} | Fallback gagal: {e2}"

def keyboard_hotkey(*keys: str) -> str:
    """
    Menekan kombinasi tombol keyboard secara bersamaan.
    Contoh: keyboard_hotkey('ctrl', 's') untuk Ctrl+S (Save).
    Contoh: keyboard_hotkey('alt', 'f4') untuk menutup jendela.
    Contoh: keyboard_hotkey('win', 'd') untuk minimize semua.
    """
    ok, err = _check()
    if not ok: return err
    try:
        pyautogui.hotkey(*keys)
        return f"Hotkey '{' + '.join(keys)}' berhasil ditekan."
    except Exception as e:
        return f"Gagal menekan hotkey: {e}"

def keyboard_press(key: str) -> str:
    """
    Menekan satu tombol keyboard.
    Contoh key: 'enter', 'escape', 'tab', 'backspace', 'delete',
    'f5', 'up', 'down', 'left', 'right', 'home', 'end', 'pageup', 'pagedown'.
    """
    ok, err = _check()
    if not ok: return err
    try:
        pyautogui.press(key)
        return f"Tombol '{key}' berhasil ditekan."
    except Exception as e:
        return f"Gagal menekan tombol: {e}"

def keyboard_write_and_enter(text: str) -> str:
    """Mengetikkan teks lalu langsung menekan Enter. Berguna untuk mengisi form atau search bar."""
    ok, err = _check()
    if not ok: return err
    try:
        keyboard_type(text)
        time.sleep(0.1)
        pyautogui.press('enter')
        return f"Teks '{text}' berhasil diketik dan Enter ditekan."
    except Exception as e:
        return f"Gagal mengetik dan enter: {e}"

# ── Tool Definitions ──────────────────────────────────────────────────────────

INPUT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "mouse_move",
            "description": "Menggerakkan kursor mouse ke koordinat (x, y) pada layar.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "Koordinat horizontal layar (pixel)."},
                    "y": {"type": "integer", "description": "Koordinat vertikal layar (pixel)."}
                },
                "required": ["x", "y"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mouse_click",
            "description": "Mengklik mouse pada koordinat (x, y). Gunakan ini untuk menekan tombol, memilih item, dll.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "Koordinat horizontal."},
                    "y": {"type": "integer", "description": "Koordinat vertikal."},
                    "button": {"type": "string", "description": "Tombol mouse: 'left' (default), 'right', atau 'middle'."}
                },
                "required": ["x", "y"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mouse_double_click",
            "description": "Double-click pada koordinat (x, y). Berguna untuk membuka file atau folder.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "Koordinat horizontal."},
                    "y": {"type": "integer", "description": "Koordinat vertikal."}
                },
                "required": ["x", "y"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mouse_right_click",
            "description": "Klik kanan pada koordinat (x, y) untuk membuka context menu.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "Koordinat horizontal."},
                    "y": {"type": "integer", "description": "Koordinat vertikal."}
                },
                "required": ["x", "y"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mouse_drag",
            "description": "Klik tahan dan seret (drag & drop) dari satu titik ke titik lain di layar.",
            "parameters": {
                "type": "object",
                "properties": {
                    "from_x": {"type": "integer", "description": "Koordinat X titik asal."},
                    "from_y": {"type": "integer", "description": "Koordinat Y titik asal."},
                    "to_x": {"type": "integer", "description": "Koordinat X titik tujuan."},
                    "to_y": {"type": "integer", "description": "Koordinat Y titik tujuan."}
                },
                "required": ["from_x", "from_y", "to_x", "to_y"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "scroll",
            "description": "Scroll (gulir) halaman/area di posisi tertentu. Nilai positif scroll ke atas, negatif scroll ke bawah.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "Koordinat X lokasi scroll."},
                    "y": {"type": "integer", "description": "Koordinat Y lokasi scroll."},
                    "amount": {"type": "integer", "description": "Jumlah scroll. Positif = ke atas, negatif = ke bawah. Contoh: 3 atau -5."}
                },
                "required": ["x", "y", "amount"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_mouse_position",
            "description": "Mendapatkan posisi kursor mouse saat ini dalam koordinat layar. Berguna sebelum melakukan klik."
        }
    },
    {
        "type": "function",
        "function": {
            "name": "keyboard_type",
            "description": "Mengetikkan teks ke aplikasi yang sedang aktif/fokus, persis seperti diketik dari keyboard.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Teks yang ingin diketikkan."}
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "keyboard_hotkey",
            "description": "Menekan kombinasi tombol keyboard. Contoh: Ctrl+C='ctrl','c' | Ctrl+S='ctrl','s' | Alt+F4='alt','f4' | Win+D='win','d' | Ctrl+Alt+Del (jangan gunakan) | Ctrl+Z='ctrl','z'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "keys": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List tombol yang ditekan bersamaan. Contoh: ['ctrl', 's'] atau ['alt', 'tab']."
                    }
                },
                "required": ["keys"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "keyboard_press",
            "description": "Menekan satu tombol keyboard. Contoh: 'enter', 'escape', 'tab', 'backspace', 'f5', 'up', 'down'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Nama tombol yang ditekan."}
                },
                "required": ["key"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "keyboard_write_and_enter",
            "description": "Mengetikkan teks lalu langsung menekan Enter. Berguna untuk search bar, run dialog (Win+R), atau form.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Teks yang diketik sebelum Enter ditekan."}
                },
                "required": ["text"]
            }
        }
    }
]

# Tambahan: wrapper untuk hotkey agar bisa dipanggil dengan list
def keyboard_hotkey_wrapper(keys: list) -> str:
    return keyboard_hotkey(*keys)

INPUT_TOOL_MAP = {
    "mouse_move": mouse_move,
    "mouse_click": mouse_click,
    "mouse_double_click": mouse_double_click,
    "mouse_right_click": mouse_right_click,
    "mouse_drag": mouse_drag,
    "scroll": scroll,
    "get_mouse_position": get_mouse_position,
    "keyboard_type": keyboard_type,
    "keyboard_hotkey": keyboard_hotkey_wrapper,
    "keyboard_press": keyboard_press,
    "keyboard_write_and_enter": keyboard_write_and_enter,
}
