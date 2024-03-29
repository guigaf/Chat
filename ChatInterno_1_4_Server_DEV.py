import socket
import threading
from datetime import datetime
import tkinter as tk
from tkinter import scrolledtext
import sqlite3
import json
import time

clients = []
messages = []
lock = threading.Lock()
running = True
fileName = f"chat_log.db"

def handle_client(client_socket, address):
    global messages
    global clients

    to_remove = []

    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if not message:
                break

            print(f"Received message from {address}: {message}")

            if "load_messages_from_server;" in message:
                particao = message.split(";")

                messageLoad = particao[0]
                messageData = particao[1]

                messages = load_message_from_sqlite(messageData)

                #jsonMessages = json.dumps(messages)

                # Envie a mensagem para todos os clientes (se necessário)
                with lock:
                    for individualMessage in messages:
                        broadcast(individualMessage, address, messageLoad)
            else:
                # Salvar a mensagem no banco de dados SQLite
                save_message_to_sqlite(message)

                mensagemDataHora, mensagemRemetente, mensagemConteudo, mensagemTipo = separa_mensagem(message)

                if mensagemTipo == "saida":
                    for client in clients:
                        laddr = client.getsockname()
                        if laddr[0] == address[0]:
                            print(f"O cliente {mensagemRemetente} do IP {address[0]} saiu")
                            clients.remove(client)

                # Envie a mensagem para todos os clientes (se necessário)
                with lock:
                    messageLoad = "send_messages_to_client"
                    broadcast(message, address, messageLoad)

        except Exception as e:
            print(f"Error handling client {address}: {e}")
            break

    client_socket.close()

def save_message_to_sqlite(message):
    global fileName
    
    try:
        mensagemDataHora, mensagemRemetente, mensagemConteudo, mensagemTipo = separa_mensagem(message)

    except Exception as e:
        pass

    try:
        with sqlite3.connect(fileName) as conexao:
            cursor = conexao.cursor()
            cursor.execute('INSERT INTO mensagens (data_hora, remetente, conteudo, tipo) VALUES (?, ?, ?, ?)', 
                           (mensagemDataHora, mensagemRemetente, mensagemConteudo, mensagemTipo))
    except Exception as e:
        pass

def separa_mensagem(message):
    messageSplited = message.split(';')

    mensagemDataHora = messageSplited[0]
    mensagemRemetente = messageSplited[1]
    mensagemConteudo = messageSplited[2]
    mensagemTipo = messageSplited[3]

    return mensagemDataHora, mensagemRemetente, mensagemConteudo, mensagemTipo

def load_message_from_sqlite(mensagemData):
    global fileName

    try:
        with sqlite3.connect(fileName) as conexao:
            cursor = conexao.cursor()
            cursor.execute("SELECT * FROM mensagens WHERE data_hora >= ?", (f"{mensagemData} 00:00:00",))
            mensagens_do_dia = cursor.fetchall()
            result = []
            for mensagem in mensagens_do_dia:
                mensagem_str = ';'.join(map(str, mensagem))
                result.append(mensagem_str)
            return result
    except Exception as e:
        pass


def verify_sqlite_existence():
    # Verifica se ja existe o SQLite, caso não exista, ele cria um novo
    global fileName

    try:
        with sqlite3.connect(fileName) as conexao:
            cursor = conexao.cursor()

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS mensagens (
                data_hora TEXT NOT NULL,
                remetente TEXT NOT NULL,
                conteudo TEXT NOT NULL,
                tipo TEXT NOT NULL
            )
        ''')
    except Exception as e:
        pass

def broadcast(message, address, messageLoad):
    global clients
    to_remove = []

    for client in clients:
        try:
            laddr = client.getsockname()
            raddr = client.getpeername() 
        
            # Envia apenas para o cliente que requisitou
            if "load_messages_from_server" in messageLoad:
                if address in (laddr, raddr):
                    try:
                        #Envia mensagem para o cliente
                        time.sleep(0.001) #Delay de 1ms
                        client.sendall(message.encode('utf-8'))
                        print("Send load_messages_from_server:", message)
                    except Exception as e:
                        print(f"Error load_messages_from_server: {e}")
                        to_remove.append(client)

            # Envia para todos os clientes conectados
            elif "send_messages_to_client" in messageLoad:
                try:
                    #Envia mensagem para o cliente
                    client.sendall(message.encode('utf-8'))
                    print("Send send_messages_to_client:", message)
                except Exception as e:
                    print(f"Error send_messages_to_client: {e}")
                    to_remove.append(client)

        except Exception as e:
            print(f"Error broadcasting message to client: {e}")
            to_remove.append(client)

    # Remove os clientes que causaram erros
    for client in to_remove:
        clients.remove(client)

def start_server():
    global clients
    global running

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', 5555))
    server.listen(5)
    print("Server listening on port 5555...")


    while running:
        try:
            client, addr = server.accept() # Codigo fica "travado" nessa parte esperando um cliente novo se conectar
            with lock:
                clients.append(client)

            client_handler = threading.Thread(target=handle_client, args=(client, addr))
            client_handler.start()

        except KeyboardInterrupt:
            on_closing()
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
    global clients
    
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

    print("O server está sendo desligado...")
    jInterfaceServer.destroy()

def update_date_time():
    global currentDate
    global currentTime

    while True:
        currentDate = datetime.now().strftime("%d-%m-%Y")
        currentTime = datetime.now().strftime("%H:%M:%S")
    
        #print("currentDate: ", currentDate)
        #print("currentTime: ", currentTime)
        
        time.sleep(1)

def thread_update_date_time():
    # Thread atualizar a data e hora atual
    updateDateTimeThread = threading.Thread(target=update_date_time, daemon=True)
    updateDateTimeThread.start()

###################################################################################################################################################
    
def interface_grafica():
    global currentDate
    global jInterfaceServer
    global stClientesConectados

    thread_update_date_time()
    
    verify_sqlite_existence()

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