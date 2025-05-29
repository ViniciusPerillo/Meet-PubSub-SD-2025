import customtkinter as ctk
import zmq
import threading
import queue 
from datetime import datetime
import time

from peer import *
from video_manager import VideoManager

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("O Whatsapp 3")
        self.geometry("1920x1080")

        self.user_instance: Peer = None
        self.message_queue = queue.Queue()

        # Tela de Conexão  
        self.connection = ctk.CTkFrame(self)
        self.connection.pack(pady=20, padx=20, fill="both", expand=True)

        self.username_label = ctk.CTkLabel(self.connection, text="Nome de Usuário")
        self.username_label.pack(pady=(10,0))
        self.username_entry = ctk.CTkEntry(self.connection, placeholder_text="Seu nome")
        self.username_entry.pack(pady=5)

        #Input da lista de IPs 
        self.ips_label = ctk.CTkLabel(self.connection, text="Endereços IPs(separados por vírgula)")
        self.ips_label.pack(pady=(10,0))

        self.ips_entry = ctk.CTkEntry(self.connection, width=350)
        self.ips_entry.pack(pady=5)
        # self.ips_entry.insert(0, "::1") #teste 

        self.create_room_button = ctk.CTkButton(self.connection, text="Conectar", command=self.connection_action)
        self.create_room_button.pack(pady=10)

        self.status_connection = ctk.CTkLabel(self.connection, text="")
        self.status_connection.pack(pady=10)

        #Tela da Sala
        self.room = ctk.CTkFrame(self)

        #Chat
        self.room_chat = ctk.CTkFrame(self.room, width=400)
        self.room_chat.pack(side="right", fill="y")

        self.room_info = ctk.CTkLabel(self.room_chat, text="")
        self.room_info.pack(pady=5)

        self.chat_display = ctk.CTkTextbox(self.room_chat, width=350, height=300, state="disabled")
        self.chat_display.pack(pady=10, padx=10)

        self.message_entry = ctk.CTkEntry(self.room_chat, placeholder_text="Digite sua mensagem...", width=250)
        self.message_entry.pack(side=ctk.LEFT, pady=10, padx=(10,0))
        #self.message_entry.bind("<Return>", self.send_message)

        self.send_button = ctk.CTkButton(self.room_chat, text="Enviar", command=self.send_message, width=80)
        self.send_button.pack(side=ctk.LEFT, pady=10, padx=10)

        #Vídeo
        self.video_widgets = {}
        self.video_display = ctk.CTkFrame(self.room)
        self.video_display.pack(side="left", fill="both", expand=True)


        self.exit_button = ctk.CTkButton(self.room, text="Sair da Sala", command=self.exit_room)
        self.exit_button.pack(pady=10)

        self.process_message_queue()
        self.protocol("WM_DELETE_WINDOW", self.closing_all)

    def connection_action(self):
        username = self.username_entry.get()
        ips = self.ips_entry.get()
        list_ips = []

        if not username or not ips:
            self.status_connection.configure(text="Preencha todos os campos")
            return
        
        try:
            list_ips = [ip.strip() for ip in ips.split(",") if ip.strip()]
            self.user_instance = Peer(username)
            self.user_instance.connectByIPs(list_ips)

            self.status_connection.configure(text="")
            self.show_room()
            self.room_info.configure(text=f"Conectado como: {username} | IP: {self.user_instance.ipv6}") 
            self.display_on_chat(f"Conectado ao grupo com IPs: {list_ips}", is_status=True)
            self.start_user_listeners()
            
        except Exception as e:
            self.status_connection.configure(text=f"Erro : {str(e)}")
            self.user_instance = None

    def exit_room(self):
        self.user_instance.exitRoom()
        self.show_connection()
        self.user_instance = None 

        self.display_on_chat("Você saiu da sala.", is_status=True)

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
        def listeners():
            while self.user_instance and self.user_instance.on_room:
                try:
                    topic, username_bytes, msg = self.user_instance.subscriber.recv_multipart(flags=zmq.NOBLOCK) 
                            
                    timestamp = datetime.now().strftime("%H:%M")
                    username = username_bytes.decode('utf-8')
                            
                    if topic == b'text':
                        message = msg.decode('utf-8')

                        if username != self.user_instance.username:
                            self.message_queue.put(f"{timestamp} - {username}: {message}")
                    elif topic == b'status':
                            status_val = bool(int(msg[-1]))
                            ip_affected = msg[:-1].decode('utf-8')
                            status_msg = f"{username} {'entrou na' if status_val else 'saiu da'} sala."

                            if ip_affected != self.user_instance.ipv6: 
                                self.message_queue.put(f"STATUS: {status_msg}")
                    elif topic == b'video':
                            self.user_instance.video_manager.recieve_video(username, msg)

                            
                except zmq.Again: 
                    time.sleep(0.05)
                    continue
                except Exception as e:
                    if self.user_instance and self.user_instance.on_room: 
                        self.message_queue.put(f"ERRO DE REDE: {e}")
                    break

        threading.Thread(target=listeners, daemon=True).start()

    def process_message_queue(self):
        try:
            while not self.message_queue.empty():
                message = self.message_queue.get_nowait()
                self.display_on_chat(message, is_status="STATUS:" in message or "ERRO:" in message)
        finally:
            self.after(100, self.process_message_queue) # 100ms

    #Fechar CONCERTAR ISSO AQUI
    def closing_all(self):
        if self.user_instance and self.user_instance.on_room:
            self.disconnectByIPs(self.user_instance.connected_ips)
        self.destroy()
    


"""    def send_text_message(self, message: str):
        if self.on_room:
            self.publisher.send_multipart([b'text', self.username.encode('utf-8'), message.encode('utf-8')]) 
"""