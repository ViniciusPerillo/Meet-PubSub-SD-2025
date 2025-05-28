import customtkinter as ctk
import zmq
import threading
import queue 
from datetime import datetime
import time
from user_local import User

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("O Whatsapp 3")
        self.geometry("600x500")

        self.user_instance: User = None
        self.message_queue = queue.Queue()

        # Tela de Conexão  
        self.connection = ctk.CTkFrame(self)
        self.connection.pack(pady=20, padx=20, fill="both", expand=True)

        self.username_label = ctk.CTkLabel(self.connection, text="Nome de Usuário")
        self.username_label.pack(pady=(10,0))
        self.username_entry = ctk.CTkEntry(self.connection, placeholder_text="Seu nome")
        self.username_entry.pack(pady=5)

        #Proteger a sala com senha(pra entrar precisa do código de convite + senha)
        #Conferir 
        self.password_label = ctk.CTkLabel(self.connection, text="Senha da Sala")
        self.password_label.pack(pady=(10,0))
        self.password_entry = ctk.CTkEntry(self.connection)
        self.password_entry.pack(pady=5)

        self.create_room_button = ctk.CTkButton(self.connection, text="Criar Sala", command=self.create_room_action)
        self.create_room_button.pack(pady=10)

        self.invite_code_label = ctk.CTkLabel(self.connection, text="Código de Convite")
        self.invite_code_label.pack(pady=(10,0))
        self.invite_code_entry = ctk.CTkEntry(self.connection)
        self.invite_code_entry.pack(pady=5)

        self.join_room_button = ctk.CTkButton(self.connection, text="Entrar na Sala", command=self.join_room_action)
        self.join_room_button.pack(pady=10)

        self.status_connection = ctk.CTkLabel(self.connection, text="")
        self.status_connection.pack(pady=10)

        #Tela da Sala
        self.room = ctk.CTkFrame(self)

        self.room_info = ctk.CTkLabel(self.room, text="")
        self.room_info.pack(pady=5)

        self.chat_display = ctk.CTkTextbox(self.room, width=550, height=300, state="disabled")
        self.chat_display.pack(pady=10, padx=10)

        self.message_entry = ctk.CTkEntry(self.room, placeholder_text="Digite sua mensagem...", width=450)
        self.message_entry.pack(side=ctk.LEFT, pady=10, padx=(10,0))
        self.message_entry.bind("<Return>", self.send_message)

        self.send_button = ctk.CTkButton(self.room, text="Enviar", command=self.send_message, width=80)
        self.send_button.pack(side=ctk.LEFT, pady=10, padx=10)
        
        self.exit_button = ctk.CTkButton(self.room, text="Sair da Sala", command=self.exit_room)
        self.exit_button.pack(pady=10)

        self.process_message_queue()
        self.protocol("WM_DELETE_WINDOW", self.closing_all)

    def create_room_action(self):
            username = self.username_entry.get()
            password = self.password_entry.get()

            if not username or not password:
                self.status_connection.configure(text="Por favor, insira um nome de usuário e senha.")
                return
            
            self.user_instance = User(username)
            self.user_instance.createRoom(password=password)

            self.status_connection.configure(text="")
            self.show_room()
            self.display_on_chat(f"Você criou a sala. Convite: {self.user_instance.invite} | Senha: {self.user_instance.password}", is_status=True)
            self.start_user_listeners()

    def join_room_action(self):
            username = self.username_entry.get()
            password = self.password_entry.get()
            invite_code = self.invite_code_entry.get()

            if not username or not invite_code or not password:
                self.status_connection.configure(text="Nome de usuário, senha e código de convite são obrigatórios.")
                return

            self.user_instance = User(username)
            try:
                self.user_instance.joinRoom(invite_code, password=password)

                if self.user_instance.on_room:
                    self.status_connection.configure(text="")
                    self.show_room()
                    self.room_info.configure(text="")
                    self.display_on_chat(f"Você entrou na sala: {self.user_instance.room} | Senha: {self.user_instance.password}", is_status=True)
                    self.start_user_listeners()
                else:
                    self.status_connection.configure(text="Falha ao entrar na sala. Verifique o código/senha.")
                    self.user_instance = None
            except Exception as e: 
                self.status_connection.configure(text=f"Erro: {str(e)}")
                self.user_instance = None

    def exit_room(self):

        if self.user_instance and self.user_instance.on_room:
            self.user_instance.exitRoom()
        self.display_on_chat("Você saiu da sala.", is_status=True) 
        self.show_connection()
        self.user_instance = None 

    def show_connection(self):
        self.room.pack_forget()
        self.connection.pack(pady=20, padx=20, fill="both", expand=True)

        if self.user_instance:
             self.status_connection.configure(text="Você saiu da sala.")

    def show_room(self):
        self.connection.pack_forget() 
        self.room.pack(pady=20, padx=20, fill="both", expand=True) 

    def display_on_chat(self, message: str, is_status=False):
        self.chat_display.configure(state="normal")

        if is_status:
            self.chat_display.insert(ctk.END, f"{message}\n", "status_tag")
        else:
            self.chat_display.insert(ctk.END, f"{message}\n")

        self.chat_display.configure(state="disabled")
        self.chat_display.see(ctk.END) 

    def send_message(self, event=None): 
        if self.user_instance and self.user_instance.on_room:
            message = self.message_entry.get()
            if message:
                self.user_instance.send_text_message(message) 
                timestamp = datetime.now().strftime("%H:%M:%S")
                self.message_queue.put(f"{timestamp} - Você: {message}")
                self.message_entry.delete(0, ctk.END)

    def start_user_listeners(self):      
        return 

    def process_message_queue(self):
        try:
            while not self.message_queue.empty():
                message = self.message_queue.get_nowait()
                self.display_on_chat(message, is_status="STATUS:" in message or "ERRO:" in message)
        finally:
            self.after(100, self.process_message_queue) # 100ms

    #Fechar
    def closing_all(self):
        if self.user_instance and self.user_instance.on_room:
            self.user_instance.exitRoom()
        self.destroy()
    


