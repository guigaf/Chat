import socket
import threading
from datetime import datetime
import tkinter as tk
from tkinter import scrolledtext

clients = []
messages = []
lock = threading.Lock()
running = True
server_password = None

def handle_client(client_socket, address):
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if not message:
                break
            
            if server_password in message:
                
                pass
            print(f"Received message from {address}: {message}")

            # Salvar a mensagem no arquivo do histórico
            save_message_to_file(message)

            # Envie a mensagem para todos os clientes (se necessário)
            with lock:
                broadcast(message, address)

        except Exception as e:
            print(f"Error handling client {address}: {e}")
            break

    client_socket.close()

def save_message_to_file(message):
    global current_date
    
    file_name = f"chat_log_{current_date}.txt"
    try:
        with open(file_name, "a") as file:
            file.write(message + "\n")
    except Exception as e:
        pass 

def verify_log_existence():
    global current_date

    file_name = f"chat_log_{current_date}.txt"
    try:
        with open(file_name, "r") as file:
            print("LidoComSucesso")
            content = file.read()
    except FileNotFoundError:
        print("FileNotFoundError")
        with open(file_name, "w") as file:
            file.write(f"Ola, bem vindo ao chat, hoje é dia {current_date}" + "\n") 

def broadcast(message, sender_addr):
    to_remove = []

    for client in clients:
        try:
            # Verifica se o cliente ainda está na lista e é um objeto de soquete
            #if client in clients and isinstance(client, socket.socket):
            client.sendall(message.encode('utf-8'))
        except Exception as e:
            print(f"Error broadcasting message to client: {e}")
            to_remove.append(client)

    # Remove os clientes que causaram erros
    for client in to_remove:
        clients.remove(client)

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', 5555))
    server.listen(5)
    print("Server listening on port 5555...")
    global running

    while running:
        try:
            client, addr = server.accept() # Codigo fica "travado" nessa parte esperando um cliente novo se conectar
            with lock:
                clients.append(client)

            client_handler = threading.Thread(target=handle_client, args=(client, addr))
            client_handler.start()

        except KeyboardInterrupt:
            print("Server is shutting down.")
            running = False
        
        try:
            print("CLIENTS: ", clients)
            for client in clients:
                print("client: ", client)
        except Exception as e:
            pass

    # Fechar todos os sockets
    server.close()
    with lock:
        for client in clients:
            client.close()

def thread_start_server():
    # Thread para receber mensagens
    receive_thread = threading.Thread(target=start_server, daemon=True)
    receive_thread.start()

def on_closing():
    global jInterfaceServer

    jInterfaceServer.destroy()

###################################################################################################################################################
    
def interface_grafica():
    global current_date
    global jInterfaceServer

    current_date = datetime.now().strftime("%d-%m-%Y") # Verifica a data atual
    verify_log_existence() # Verifica se ja existe o arquivo de log, caso não exista, ele cria um novo com a dtaa atual

    # Cria janela do chat
    jInterfaceServer = tk.Tk()

    # Coloca um titulo na janela do chat
    jInterfaceServer.title(f'CPSM - Server')

    # Adiciona um script ao botão de fechar padrão da janela
    jInterfaceServer.protocol("WM_DELETE_WINDOW", on_closing)

    stClientesConectados = scrolledtext.ScrolledText(jInterfaceServer, wrap=tk.WORD, width=60, height=10)
    stClientesConectados.grid(row=0, column=0, columnspan=3, padx=10, pady=10, sticky='nsew')
    stClientesConectados.config(state=tk.DISABLED)

    lPassword = tk.Label(jInterfaceServer, text="Senha server:")
    lPassword.grid(row=1, column=0, columnspan=1, padx=10, pady=10, sticky='w')

    # Adiciona um campo apra digitar mensagem
    ePassword = tk.Entry(jInterfaceServer, width=40)
    ePassword.grid(row=1, column=1, columnspan=2, padx=10, pady=10, sticky='ew')
    
    # Configuração do peso da linha e coluna
    jInterfaceServer.grid_rowconfigure(0, weight=1)
    jInterfaceServer.grid_rowconfigure(1, weight=0)
    jInterfaceServer.grid_columnconfigure(0, weight=0)
    jInterfaceServer.grid_columnconfigure(1, weight=1)
    jInterfaceServer.grid_columnconfigure(2, weight=1)

    thread_start_server()

    # mainLoop da janela principal
    jInterfaceServer.mainloop()

###################################################################################################################################################

if __name__ == "__main__":
    interface_grafica()