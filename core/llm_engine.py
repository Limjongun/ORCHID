import os
import json
from openai import OpenAI
from dotenv import load_dotenv

from core.sandbox import SecuritySandbox
from plugins.system_control import SYSTEM_TOOLS, SYSTEM_TOOL_MAP
from plugins.git_control import GIT_TOOLS, GIT_TOOL_MAP
from plugins.file_explorer import FILE_TOOLS, FILE_TOOL_MAP
from plugins.hardware_info import HARDWARE_TOOLS, HARDWARE_TOOL_MAP

class ChatEngine:
    def __init__(self):
        load_dotenv()
        self.token_1 = os.environ.get("GITHUB_TOKEN_1") or os.environ.get("GITHUB_TOKEN")
        self.token_2 = os.environ.get("GITHUB_TOKEN_2")
        
        if not self.token_1:
            raise ValueError("GITHUB_TOKEN_1 is not set in .env")
            
        self.client = OpenAI(
            base_url="https://models.inference.ai.azure.com",
            api_key=self.token_1,
        )
        self.model = "gpt-4o"
        self.sandbox = SecuritySandbox()
        
        self.messages = [
            {"role": "system", "content": "You are ORCHID, a highly advanced local AI desktop assistant. You have access to tools that can read system status, execute actions, and run Git commands. ALWAYS respond in Indonesian unless asked otherwise. If the user asks you to do Git operations, use the execute_git_command tool. You can string together multiple tool calls if they require sequences like (add, then commit, then push)."}
        ]
        
        # Gabungkan semua Tools dari Plugins
        self.tools = SYSTEM_TOOLS + GIT_TOOLS + FILE_TOOLS + HARDWARE_TOOLS
        self.tool_map = {**SYSTEM_TOOL_MAP, **GIT_TOOL_MAP, **FILE_TOOL_MAP, **HARDWARE_TOOL_MAP}
        
    def set_speaking_style(self, style):
        base_prompt = "You are ORCHID, a highly advanced local AI desktop assistant. You have access to tools that can read system status, execute actions, and run Git commands. ALWAYS respond in Indonesian unless asked otherwise. If the user asks you to do Git operations, use the execute_git_command tool. You can string together multiple tool calls if they require sequences like (add, then commit, then push)."
        
        if style == "Singkat & Padat":
            new_prompt = base_prompt + " Jawablah dengan SANGAT SINGKAT, PADAT, dan langsung ke intinya (to the point). Jangan bertele-tele."
        elif style == "Panjang & Detail":
            new_prompt = base_prompt + " Jawablah dengan PANJANG LEBAR, SANGAT DETAIL, komprehensif, dan berikan penjelasan mendalam untuk setiap langkahnya."
        else:
            new_prompt = base_prompt
            
        if self.messages and self.messages[0]["role"] == "system":
            self.messages[0]["content"] = new_prompt
        return True
        
    def switch_account(self, account_index):
        if account_index == 1 and self.token_1:
            self.client = OpenAI(
                base_url="https://models.inference.ai.azure.com",
                api_key=self.token_1,
            )
            self.model = "gpt-4o"
            return True
        elif account_index == 2 and self.token_2:
            self.client = OpenAI(
                base_url="https://models.inference.ai.azure.com",
                api_key=self.token_2,
            )
            self.model = "gpt-4o"
            return True
        elif account_index == 3:
            self.client = OpenAI(
                base_url="http://localhost:20128/v1",
                api_key="dummy_key_for_local_router",
            )
            self.model = "gokil"
            return True
        return False
        
    def generate_response(self, user_message):
        self.messages.append({"role": "user", "content": user_message})
        
        try:
            kwargs = {
                "model": self.model,
                "messages": self.messages,
                "temperature": 0.7,
                "max_tokens": 1024,
                "timeout": 30.0,
            }
            
            # Matikan fungsi tools untuk router lokal agar tidak menyebabkan error/hang
            if self.model != "gokil":
                kwargs["tools"] = self.tools
                
            response = self.client.chat.completions.create(**kwargs)
            
            response_message = response.choices[0].message
            self.messages.append(response_message)
            
            if response_message.tool_calls:
                for tool_call in response_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    if not self.sandbox.validate_action(function_name, **function_args):
                        function_response = f"User menolak/tidak memberikan izin untuk mengeksekusi perintah {function_name} dengan argumen {function_args}."
                    else:
                        if function_name in self.tool_map:
                            try:
                                function_to_call = self.tool_map[function_name]
                                function_response = function_to_call(**function_args)
                            except Exception as e:
                                function_response = f"Error saat mengeksekusi fungsi {function_name}: {e}"
                        else:
                            function_response = f"Fungsi {function_name} tidak ditemukan dalam sistem."
                            
                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": str(function_response),
                    })
                    
                second_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=self.messages,
                    temperature=0.7,
                    max_tokens=1024,
                )
                final_reply = second_response.choices[0].message.content
                self.messages.append({"role": "assistant", "content": final_reply})
                return final_reply
                
            else:
                if response_message.content:
                    return response_message.content
                return "Maaf, respon kosong."
                
        except Exception as e:
            self.messages.pop() 
            return f"[ERROR Sistem ORCHID] Gagal berkomunikasi dengan AI: {str(e)}"
