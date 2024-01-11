import socket
import threading
from datetime import datetime
import tkinter as tk
from tkinter import scrolledtext
import sqlite3

clients = []
messages = []
lock = threading.Lock()
running = True
file_name = f"chat_log.db"

def handle_client(client_socket, address):
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if not message:
                break

            print(f"Received message from {address}: {message}")

            # Salvar a mensagem no banco de dados SQLite
            save_message_to_sqlite(message)

            # Envie a mensagem para todos os clientes (se necessário)
            with lock:
                broadcast(message, address)

        except Exception as e:
            print(f"Error handling client {address}: {e}")
            break

    client_socket.close()

def save_message_to_sqlite(message):
    global file_name
    
    try:
        messageSplited = message.split(';')
    
        mensagemData = messageSplited[0]
        mensagemHora = messageSplited[1]
        mensagemRemetente = messageSplited[2]
        mensagemConteudo = messageSplited[3]
        mensagemTipo = messageSplited[4]

        mensagemDataHora = f"{mensagemData} {mensagemHora}"
    except Exception as e:
        pass

    try:
        with sqlite3.connect(file_name) as conexao:
            cursor = conexao.cursor()
            cursor.execute('INSERT INTO mensagens (data_hora, remetente, conteudo, tipo) VALUES (?, ?, ?, ?)', 
                           (mensagemDataHora, mensagemRemetente, mensagemConteudo, mensagemTipo))
    except Exception as e:
        pass

def verify_sqlite_existence():
    global file_name

    try:
        with sqlite3.connect(file_name) as conexao:
            cursor = conexao.cursor()

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS mensagens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_hora TEXT NOT NULL,
                remetente TEXT NOT NULL,
                conteudo TEXT NOT NULL,
                tipo TEXT NOT NULL
            )
        ''')
    except Exception as e:
        pass

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

    # Fechar todos os sockets
    server.close()
    with lock:
        for client in clients:
            client.close()

def thread_start_server():
    # Thread para receber mensagens
    receive_thread = threading.Thread(target=start_server, daemon=True)
    receive_thread.start()

def update_connected_clients():
    try:
        with lock:
            stClientesConectados.config(state=tk.NORMAL)
            stClientesConectados.delete(1.0, tk.END)  # Limpa o conteúdo atual

            stClientesConectados.insert(tk.END, "Clientes Conectados:\n")
            print(clients)
            for client_socket in clients:
                try:
                    # Obtenha informações sobre o cliente
                    client_info = client_socket.getpeername()
                    stClientesConectados.insert(tk.END, f"Endereço do Cliente: {client_info}\n")
                except Exception as e:
                    stClientesConectados.insert(tk.END, f"Erro ao obter informações do cliente: {e}\n")

            stClientesConectados.config(state=tk.DISABLED)
            stClientesConectados.see(tk.END)  # Role para o final do texto
    except Exception as e:
        print(f'Erro no update_connected_clients: {e}')
        pass
    finally:
        jInterfaceServer.after(200, update_connected_clients)

def thread_update_connected_clients():
    # Thread para receber mensagens
    receive_thread = threading.Thread(target=update_connected_clients, daemon=True)
    receive_thread.start()

def on_closing():
    global jInterfaceServer

    jInterfaceServer.destroy()

###################################################################################################################################################
    
def interface_grafica():
    global current_date
    global jInterfaceServer
    global stClientesConectados

    current_date = datetime.now().strftime("%d-%m-%Y") # Verifica a data atual
    verify_sqlite_existence() # Verifica se ja existe o SQLite, caso não exista, ele cria um novo

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

    #thread_update_connected_clients()

    # mainLoop da janela principal
    jInterfaceServer.mainloop()

###################################################################################################################################################

if __name__ == "__main__":
    interface_grafica()