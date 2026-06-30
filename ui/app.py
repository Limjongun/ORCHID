import customtkinter as ctk
import threading
import sys
import os

# Menambahkan parent path agar import dari core bisa berfungsi dengan baik
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.llm_engine import ChatEngine

class OrchidApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("ORCHID - AI Assistant")
        self.geometry("1280x720") # 16:9 ratio
        
        # Grid layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        self.msg_row = 0 # Track rows in the chat frame
        
        # Inisialisasi AI Engine
        try:
            self.chat_engine = ChatEngine()
        except Exception as e:
            self.chat_engine = None
            self.startup_error = str(e)

        self._build_sidebar()
        self._build_main_frame()
        
    def _build_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(6, weight=1)
        
        # Logo
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="ORCHID", font=ctk.CTkFont(size=28, weight="bold"), text_color="#87CEEB")
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 40))
        
        # Buttons
        self.btn_chat = ctk.CTkButton(self.sidebar_frame, text="Chat", fg_color="#87CEEB", text_color="black", hover_color="#5F9EA0", anchor="w")
        self.btn_chat.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        self.btn_tools = ctk.CTkButton(self.sidebar_frame, text="Tools & Plugins", fg_color="transparent", text_color="gray90", hover_color="gray30", anchor="w")
        self.btn_tools.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        
        self.btn_sandbox = ctk.CTkButton(self.sidebar_frame, text="Security Sandbox", fg_color="transparent", text_color="gray90", hover_color="gray30", anchor="w")
        self.btn_sandbox.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        
        self.btn_monitoring = ctk.CTkButton(self.sidebar_frame, text="Monitoring", fg_color="transparent", text_color="gray90", hover_color="gray30", anchor="w")
        self.btn_monitoring.grid(row=4, column=0, padx=20, pady=10, sticky="ew")
        
        self.btn_settings = ctk.CTkButton(self.sidebar_frame, text="Settings", fg_color="transparent", text_color="gray90", hover_color="gray30", anchor="w")
        self.btn_settings.grid(row=5, column=0, padx=20, pady=10, sticky="ew")
        
        # Model Switcher
        self.model_combo = ctk.CTkComboBox(
            self.sidebar_frame,
            values=["🤖 Ollama (qwen2.5 Lokal)", "☁️ GPT-4o (Akun 1)", "☁️ GPT-4o (Akun 2)"],
            command=self.switch_model
        )
        self.model_combo.set("🤖 Ollama (qwen2.5 Lokal)")
        self.model_combo.grid(row=6, column=0, padx=20, pady=(20, 10), sticky="ew")
        
        # Style Switcher
        self.style_combo = ctk.CTkComboBox(self.sidebar_frame, values=["Normal", "Singkat & Padat", "Panjang & Detail"], command=self.switch_style)
        self.style_combo.grid(row=7, column=0, padx=20, pady=(10, 20), sticky="ew")
        
    def switch_model(self, choice):
        if not getattr(self, "chat_engine", None):
            return
        
        if "Ollama" in choice:
            account_index = 1
        elif "Akun 1" in choice:
            account_index = 2
        elif "Akun 2" in choice:
            account_index = 3
        else:
            account_index = 1
            
        success = self.chat_engine.switch_account(account_index)
        if success:
            self.append_chat("SYSTEM", f"✅ Berhasil berganti ke {choice}.")
        else:
            self.append_chat("SYSTEM", f"❌ Gagal berganti ke {choice}. Pastikan token tersedia di file .env.")
            
    def switch_style(self, choice):
        if not getattr(self, "chat_engine", None):
            return
            
        self.chat_engine.set_speaking_style(choice)
        self.append_chat("SYSTEM", f"Gaya bicara AI diubah ke mode: {choice}.")

    def _build_main_frame(self):
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)
        
        # Chat History Scrollable Frame (Chat Bubbles)
        self.chat_frame = ctk.CTkScrollableFrame(self.main_frame, fg_color="transparent")
        self.chat_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="nsew")
        self.chat_frame.grid_columnconfigure(0, weight=1)
        
        if getattr(self, "chat_engine", None):
            model_name = getattr(self.chat_engine, 'model', 'AI')
            self.append_chat("ORCHID", f"Halo! Saya ORCHID, asisten AI desktop lokal Anda. Saat ini saya berjalan dengan model **{model_name}** via Ollama. Ada yang bisa saya bantu?")
        else:
            self.append_chat("SYSTEM", f"Gagal memuat AI Engine: {getattr(self, 'startup_error', 'Unknown')}")
            
        # Input Area
        self.input_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.input_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)
        
        self.entry_msg = ctk.CTkEntry(self.input_frame, placeholder_text="Type your message here...", height=40)
        self.entry_msg.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        
        self.btn_send = ctk.CTkButton(self.input_frame, text="Send", width=80, height=40, fg_color="#87CEEB", text_color="black", hover_color="#5F9EA0")
        self.btn_send.grid(row=0, column=1)
        
        # BINDING EVENTS
        self.btn_send.configure(command=self.send_message_event)
        self.entry_msg.bind("<Return>", self.send_message_event)
        
    def append_chat(self, sender, text):
        # Create a container frame for the bubble to handle alignment
        msg_container = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        msg_container.grid(row=self.msg_row, column=0, sticky="ew", pady=5)
        msg_container.grid_columnconfigure(0, weight=1)
        
        self.msg_row += 1
        
        if sender == "You":
            # User bubble on the right (DodgerBlue)
            bubble = ctk.CTkFrame(msg_container, fg_color="#1E90FF", corner_radius=15)
            bubble.pack(side="right", padx=10, pady=2)
            msg_label = ctk.CTkLabel(bubble, text=text, text_color="white", justify="left", wraplength=700, font=ctk.CTkFont(size=14))
        else:
            # AI bubble on the left (Dark Gray)
            bubble = ctk.CTkFrame(msg_container, fg_color=("gray80", "gray20"), corner_radius=15)
            bubble.pack(side="left", padx=10, pady=2)
            msg_label = ctk.CTkLabel(bubble, text=text, text_color=("black", "white"), justify="left", wraplength=700, font=ctk.CTkFont(size=14))
            
        msg_label.pack(padx=15, pady=10)
        
        # Scroll to bottom smoothly
        self.chat_frame.update_idletasks()
        self.chat_frame._parent_canvas.yview_moveto(1.0)
        
    def show_loading(self):
        self.loading_container = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        self.loading_container.grid(row=self.msg_row, column=0, sticky="ew", pady=5)
        self.loading_container.grid_columnconfigure(0, weight=1)
        self.msg_row += 1

        bubble = ctk.CTkFrame(self.loading_container, fg_color=("gray78", "gray18"), corner_radius=15)
        bubble.pack(side="left", padx=10, pady=2)
        self.loading_label = ctk.CTkLabel(
            bubble, text="Sedang berpikir...",
            text_color=("black", "#87CEEB"),
            font=ctk.CTkFont(size=14, slant="italic")
        )
        self.loading_label.pack(padx=15, pady=10)

        self.chat_frame.update_idletasks()
        self.chat_frame._parent_canvas.yview_moveto(1.0)

        self.is_loading = True
        self.loading_dots = 0
        self._current_loading_base = "Sedang berpikir"
        self._animate_loading()

    def _animate_loading(self):
        if getattr(self, 'is_loading', False) and hasattr(self, 'loading_label'):
            self.loading_dots = (self.loading_dots + 1) % 4
            dots = "." * self.loading_dots
            base = getattr(self, '_current_loading_base', 'Sedang berpikir')
            try:
                self.loading_label.configure(text=f"{base}{dots}")
                self.after(400, self._animate_loading)
            except:
                pass

    def update_loading_status(self, tool_name, args):
        """Dipanggil tiap kali AI mengeksekusi satu tool — update teks bubble loading."""
        TOOL_LABELS = {
            "create_directory":      "📁 Membuat folder",
            "write_file":            "✍️  Menulis file",
            "read_file":             "📖 Membaca file",
            "delete_file_or_folder": "🗑️  Menghapus item",
            "move_rename_item":      "✂️  Memindahkan item",
            "compress_to_zip":       "🗜️  Mengompresi",
            "open_application":      "🚀 Membuka aplikasi",
            "close_application":     "❌ Menutup aplikasi",
            "take_screenshot":       "📸 Screenshot",
            "search_duckduckgo":     "🔍 Mencari di internet",
            "open_website":          "🌐 Membuka website",
            "execute_powershell":    "⚡ Menjalankan perintah",
            "execute_git_command":   "🔧 Git command",
            "mouse_click":           "🖱️  Klik mouse",
            "keyboard_type":         "⌨️  Mengetik",
            "read_pdf":              "📄 Membaca PDF",
            "read_docx":             "📝 Membaca Word",
            "read_excel":            "📊 Membaca Excel",
            "get_system_info":       "💻 Cek sistem",
        }
        label = TOOL_LABELS.get(tool_name, f"🔧 {tool_name}")
        first_val = next(iter(args.values()), "") if args else ""
        if isinstance(first_val, str) and len(first_val) > 35:
            first_val = "..." + first_val[-30:]
        self._current_loading_base = f"{label}: {first_val}" if first_val else label

    def hide_loading(self):
        self.is_loading = False
        self._current_loading_base = "Sedang berpikir"
        if hasattr(self, 'loading_container') and self.loading_container:
            self.loading_container.destroy()
            self.loading_container = None
        
    def send_message_event(self, event=None):
        user_text = self.entry_msg.get().strip()
        if not user_text:
            return
            
        # Clear input and append user bubble
        self.entry_msg.delete(0, 'end')
        self.append_chat("You", user_text)
        
        if self.chat_engine:
            self.btn_send.configure(state="disabled")
            self.entry_msg.configure(state="disabled")
            
            # Tampilkan animasi loading
            self.show_loading()
            
            # Run AI call in background thread
            thread = threading.Thread(target=self._process_ai_response, args=(user_text,))
            thread.daemon = True
            thread.start()
        else:
            self.append_chat("ORCHID", "[System Error] Chat engine is not initialized.")
            
    def _process_ai_response(self, user_text):
        def on_tool_call(tool_name, args):
            # Update status loading bubble dari thread background (thread-safe via after)
            self.after(0, self.update_loading_status, tool_name, args)
        reply = self.chat_engine.generate_response(user_text, on_tool_call=on_tool_call)
        self.after(0, self._update_chat_with_reply, reply)
        
    def _update_chat_with_reply(self, reply):
        self.hide_loading()
        self.append_chat("ORCHID", reply)
        self.btn_send.configure(state="normal")
        self.entry_msg.configure(state="normal")
        self.entry_msg.focus()
