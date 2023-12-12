import socket
import tkinter as tk
from tkinter import scrolledtext
from datetime import datetime
import threading
from queue import Queue
import os
import getpass

###################################################################################################################################################

# Função para obter o nome de usuário
def get_username():
    try:
        username = getpass.getuser()
    except Exception as e:
        username = "Guest"  # Caso não seja possível obter o nome de usuário
    return username

def send_message(event=None):
    message = eMessage.get()
    #nickname = eNickname.get()
    nickname = get_username()
    if message and nickname:
        full_message = f"{nickname}: {message}"

        client_socket.sendall(full_message.encode('utf-8'))
        eMessage.delete(0, tk.END)

def apply_tags(message):
    # Se a mensagem indica saída, aplica a tag "exit_message"
    if "saiu do chat" in message:
        return message, "exit_message"
    elif "entrou no chat" in message:
        return message, "entry_message"
    else:
        return message, None

def send_entry_message():
    entry_message = f"{get_username()} entrou no chat."
    client_socket.sendall(entry_message.encode('utf-8'))

def update_chat_box():
    currentPositionInicio = stChatBox.yview()[0]
    currentPositionFim = stChatBox.yview()[1]

    stChatBox.config(state=tk.NORMAL)
    stChatBox.delete(1.0, tk.END)

    with lock:
        for item in messages:
            if len(item) == 2:
                message, tag = item
                if tag:
                    stChatBox.insert(tk.END, message + "\n", tag)
                else:
                    stChatBox.insert(tk.END, message + "\n")
            else:
                stChatBox.insert(tk.END, str(item) + "\n")

    if currentPositionFim == 1.0:
        stChatBox.yview(tk.END)
    else:
        stChatBox.yview(tk.MOVETO, currentPositionInicio)

    stChatBox.config(state=tk.DISABLED)
    jChatInterno.after(1000, update_chat_box)

def receive_messages():
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if not message:
                break

            with lock:
                message, tag = apply_tags(message)
                messages.append((message, tag))

            print(f"Received message: {message}")

        except Exception as e:
            print(f"Error receiving message: {e}")
            break

def load_messages_from_file():
    file_name = f"chat_log_{current_date}.txt"
    try:
        with open(file_name, "r") as file:
            content = file.read()
            contentSplitLines = content.splitlines()
            result = []
            for verifyContent in contentSplitLines:
                verifyContentOK, tag = apply_tags(verifyContent)
                result.append((verifyContentOK, tag))
            return result#content.splitlines()
    except FileNotFoundError:
        return []
    except Exception as e:
        print(f"Error loading messages from file: {e}")
        return []

def send_exit_message():
    exit_message = f"{get_username()} saiu do chat."
    client_socket.sendall(exit_message.encode('utf-8'))

def on_closing():
    send_exit_message()
    jChatInterno.destroy()

###################################################################################################################################################

# Inicializações
current_date = datetime.now().strftime("%d-%m-%Y")
lock = threading.Lock()
messages = load_messages_from_file()
nickname = get_username()

# Seleciona o endereço de IP que vai se conectar, esse valor deve ser alterado quando mudar o endereço do servidor
# Verificar uma forma melhor de selecionar o servidor
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('192.168.0.90', 5555))
send_entry_message()

jChatInterno = tk.Tk()
jChatInterno.title(f'Bem Vindo! - {nickname}')
jChatInterno.protocol("WM_DELETE_WINDOW", on_closing)

#lNickname = tk.Label(jChatInterno, text="Nome:", width=20)
#lNickname.place(x=0, y=10)
#
#eNickname = tk.Entry(jChatInterno, width=20)
#eNickname.grid(row=1, column=0, rowspan=1, columnspan=1, padx=[10, 0], pady=0, sticky='w')

stChatBox = scrolledtext.ScrolledText(jChatInterno, wrap=tk.WORD, width=60, height=10)
stChatBox.grid(row=0, column=0, columnspan=3, padx=10, pady=10, sticky='nsew')
stChatBox.tag_config("exit_message", foreground="red")
stChatBox.tag_config("entry_message", foreground="blue")
stChatBox.config(state=tk.DISABLED)

eMessage = tk.Entry(jChatInterno, width=60)
eMessage.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky='ew')
eMessage.bind("<Return>", send_message)

bSend = tk.Button(jChatInterno, text="Enviar", command=send_message)
bSend.grid(row=1, column=2, padx=10, pady=10, sticky='e')

# Configuração do peso da linha e coluna
jChatInterno.grid_rowconfigure(0, weight=1)
jChatInterno.grid_rowconfigure(1, weight=0)
jChatInterno.grid_columnconfigure(0, weight=1)
jChatInterno.grid_columnconfigure(1, weight=1)
jChatInterno.grid_columnconfigure(2, weight=0)

###################################################################################################################################################

# Thread para receber mensagens
receive_thread = threading.Thread(target=receive_messages, daemon=True)
receive_thread.start()

# Atualiza a caixa de chat
jChatInterno.after(1000, update_chat_box)

# Inicia a GUI
jChatInterno.mainloop()

###################################################################################################################################################
