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
        
        # Inisialisasi AI Engine (belum konek backend)
        try:
            self.chat_engine = ChatEngine()
        except Exception as e:
            self.chat_engine = None
            self.startup_error = str(e)
            
        self._build_sidebar()
        self._build_main_frame()
        
        # Mulai load model secara async pada saat startup
        if self.chat_engine:
            self.after(500, lambda: self.switch_model(self.model_combo.get()))
        
    def _build_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(6, weight=1)
        
        # Logo
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="ORCHID", font=ctk.CTkFont(size=28, weight="bold"), text_color="#87CEEB")
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 40))
        
        # Buttons
        self.btn_chat = ctk.CTkButton(self.sidebar_frame, text="Chat", fg_color="#87CEEB", text_color="black", hover_color="#5F9EA0", anchor="w", command=self.show_chat_frame)
        self.btn_chat.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        self.btn_tools = ctk.CTkButton(self.sidebar_frame, text="Tools & Plugins", fg_color="transparent", text_color="gray90", hover_color="gray30", anchor="w")
        self.btn_tools.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        
        self.btn_sandbox = ctk.CTkButton(self.sidebar_frame, text="Security Sandbox", fg_color="transparent", text_color="gray90", hover_color="gray30", anchor="w")
        self.btn_sandbox.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        
        self.btn_monitoring = ctk.CTkButton(self.sidebar_frame, text="Monitoring", fg_color="transparent", text_color="gray90", hover_color="gray30", anchor="w")
        self.btn_monitoring.grid(row=4, column=0, padx=20, pady=10, sticky="ew")
        
        self.btn_settings = ctk.CTkButton(self.sidebar_frame, text="Settings", fg_color="transparent", text_color="gray90", hover_color="gray30", anchor="w", command=self.show_settings_frame)
        self.btn_settings.grid(row=5, column=0, padx=20, pady=10, sticky="ew")
        
        # Model Switcher
        self.model_combo = ctk.CTkComboBox(
            self.sidebar_frame,
            values=[
                "[Ollama] qwen3:4b",
                "[Ollama] qwen2.5:latest",
                "[Ollama] gemma4:latest",
                "[Azure] GPT-4o Akun 1",
                "[Azure] GPT-4o Akun 2",
            ],
            command=self.switch_model
        )
        self.model_combo.set("[Ollama] qwen3:4b")
        self.model_combo.grid(row=6, column=0, padx=20, pady=(20, 10), sticky="ew")
        
        # Style Switcher
        self.style_combo = ctk.CTkComboBox(self.sidebar_frame, values=["Normal", "Singkat & Padat", "Panjang & Detail"], command=self.switch_style)
        self.style_combo.grid(row=7, column=0, padx=20, pady=(10, 20), sticky="ew")
        
    def switch_model(self, choice):
        if not getattr(self, "chat_engine", None):
            return

        # Parse backend dan model tag dari string pilihan combobox
        ollama_tag = None
        if choice.startswith("[Ollama]"):
            account_index = 1
            # Ekstrak tag model: "[Ollama] qwen3:4b" -> "qwen3:4b"
            ollama_tag = choice.replace("[Ollama]", "").strip()
        elif "Akun 1" in choice or "Akun1" in choice:
            account_index = 2
        elif "Akun 2" in choice or "Akun2" in choice:
            account_index = 3
        else:
            account_index = 1

        # Kunci UI selama loading
        if hasattr(self, 'btn_send'):
            self.btn_send.configure(state="disabled")
            self.entry_msg.configure(state="disabled")

        model_label = ollama_tag or choice
        self.show_loading(custom_msg=f"Memuat {model_label} ke VRAM")

        def background_load():
            success, msg = self.chat_engine.switch_account(account_index, ollama_model_tag=ollama_tag)
            self.after(0, self._on_model_loaded, choice, success, msg)

        thread = threading.Thread(target=background_load)
        thread.daemon = True
        thread.start()

    def _on_model_loaded(self, choice, success, msg):
        self.hide_loading()
        if hasattr(self, 'btn_send'):
            self.btn_send.configure(state="normal")
            self.entry_msg.configure(state="normal")
            
        if success:
            self.append_chat("SYSTEM", f"✅ {msg}")
        else:
            self.append_chat("SYSTEM", f"❌ Gagal: {msg}")
            
    def switch_style(self, choice):
        if not getattr(self, "chat_engine", None):
            return
            
        self.chat_engine.set_speaking_style(choice)
        self.append_chat("SYSTEM", f"Gaya bicara AI diubah ke mode: {choice}.")

    def _build_main_frame(self):
        self.main_container = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew")
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)

        self.main_frame = ctk.CTkFrame(self.main_container, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)
        
        # Chat History Scrollable Frame (Chat Bubbles)
        self.chat_frame = ctk.CTkScrollableFrame(self.main_frame, fg_color="transparent")
        self.chat_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="nsew")
        self.chat_frame.grid_columnconfigure(0, weight=1)
        
        if not getattr(self, "chat_engine", None):
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
        
        self._build_settings_frame()

    def show_chat_frame(self):
        self.settings_frame.grid_forget()
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.btn_chat.configure(fg_color="#87CEEB", text_color="black")
        self.btn_settings.configure(fg_color="transparent", text_color="gray90")

    def show_settings_frame(self):
        self.main_frame.grid_forget()
        self.settings_frame.grid(row=0, column=0, sticky="nsew")
        self.btn_settings.configure(fg_color="#87CEEB", text_color="black")
        self.btn_chat.configure(fg_color="transparent", text_color="gray90")

    def _build_settings_frame(self):
        self.settings_frame = ctk.CTkFrame(self.main_container, corner_radius=0, fg_color="transparent")
        self.settings_frame.grid_columnconfigure(0, weight=1)
        
        title = ctk.CTkLabel(self.settings_frame, text="⚙️ Settings", font=ctk.CTkFont(size=24, weight="bold"))
        title.grid(row=0, column=0, padx=40, pady=(40, 20), sticky="w")
        
        scroll = ctk.CTkScrollableFrame(self.settings_frame, fg_color="transparent")
        scroll.grid(row=1, column=0, padx=40, pady=0, sticky="nsew")
        self.settings_frame.grid_rowconfigure(1, weight=1)
        
        # Temperature
        ctk.CTkLabel(scroll, text="Temperature (Kreativitas)", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10, 5))
        self.temp_slider = ctk.CTkSlider(scroll, from_=0.0, to=1.0, number_of_steps=10)
        self.temp_slider.pack(fill="x", pady=(0, 10))
        
        # Max Tokens
        ctk.CTkLabel(scroll, text="Max Tokens", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10, 5))
        self.max_tokens_combo = ctk.CTkComboBox(scroll, values=["512", "1024", "2048", "4096", "8192"])
        self.max_tokens_combo.pack(fill="x", pady=(0, 10))
        
        # System Prompt
        ctk.CTkLabel(scroll, text="System Prompt (Instruksi Dasar AI)", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(20, 5))
        self.sys_prompt_textbox = ctk.CTkTextbox(scroll, height=300, font=ctk.CTkFont(size=12))
        self.sys_prompt_textbox.pack(fill="both", expand=True, pady=(0, 20))
        
        # Save Button
        btn_save = ctk.CTkButton(scroll, text="Save Settings", font=ctk.CTkFont(weight="bold"), fg_color="#4CAF50", hover_color="#45a049", command=self.save_settings)
        btn_save.pack(anchor="w", pady=20)
        
        # Load current values
        if getattr(self, "chat_engine", None):
            mgr = self.chat_engine.settings_mgr
            self.temp_slider.set(float(mgr.get("temperature")))
            self.max_tokens_combo.set(str(mgr.get("max_tokens")))
            self.sys_prompt_textbox.insert("1.0", mgr.get("system_prompt"))
            
    def save_settings(self):
        if getattr(self, "chat_engine", None):
            new_settings = {
                "temperature": self.temp_slider.get(),
                "max_tokens": int(self.max_tokens_combo.get()),
                "theme": "Dark",
                "system_prompt": self.sys_prompt_textbox.get("1.0", "end").strip()
            }
            success, msg = self.chat_engine.settings_mgr.save_settings(new_settings)
            
            # Terapkan prompt baru ke memori jika chat sedang kosong, atau reset chat
            self.chat_engine._reset_messages()
            self.append_chat("SYSTEM", f"✅ {msg} Konteks percakapan di-reset agar aturan baru berlaku.")
            self.show_chat_frame()

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
        
    def show_loading(self, custom_msg="Sedang berpikir"):
        self.loading_container = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        self.loading_container.grid(row=self.msg_row, column=0, sticky="ew", pady=5)
        self.loading_container.grid_columnconfigure(0, weight=1)
        self.msg_row += 1

        bubble = ctk.CTkFrame(self.loading_container, fg_color=("gray78", "gray18"), corner_radius=15)
        bubble.pack(side="left", padx=10, pady=2)
        self.loading_label = ctk.CTkLabel(
            bubble, text=f"{custom_msg}...",
            text_color=("black", "#87CEEB"),
            font=ctk.CTkFont(size=14, slant="italic")
        )
        self.loading_label.pack(padx=15, pady=10)

        self.chat_frame.update_idletasks()
        self.chat_frame._parent_canvas.yview_moveto(1.0)

        self.is_loading = True
        self.loading_dots = 0
        self._current_loading_base = custom_msg
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
        
    def _clean_latex_delimiters(self, text):
        import re
        # Hapus tanda kurung khusus LaTeX
        text = re.sub(r'\\\[(.*?)\\\]', r'\1', text, flags=re.DOTALL)
        text = re.sub(r'\\\((.*?)\\\)', r'\1', text, flags=re.DOTALL)
        # Ganti beberapa perintah LaTeX yang umum dengan Unicode jika AI masih menggunakannya
        replacements = {
            r'\beta': 'β', r'\alpha': 'α', r'\epsilon': 'ε', r'\gamma': 'γ',
            r'_0': '₀', r'_1': '₁', r'_2': '₂', r'_p': 'ₚ',
            r'\hat{y}': 'ŷ'
        }
        for k, v in replacements.items():
            text = text.replace(k, v)
        return text

    def _update_chat_with_reply(self, reply):
        self.hide_loading()
        clean_reply = self._clean_latex_delimiters(reply)
        self.append_chat("ORCHID", clean_reply)
        self.btn_send.configure(state="normal")
        self.entry_msg.configure(state="normal")
        self.entry_msg.focus()
