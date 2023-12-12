import socket
import threading
from datetime import datetime

clients = []
messages = []
lock = threading.Lock()
running = True
def handle_client(client_socket, address):
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if not message:
                break

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
    file_name = f"chat_log_{current_date}.txt"
    try:
        with open(file_name, "a") as file:
            file.write(message + "\n")
    except Exception as e:
        pass 

def verify_log_existence():
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
            client, addr = server.accept()
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

current_date = datetime.now().strftime("%d-%m-%Y")
verify_log_existence()

if __name__ == "__main__":
    start_server()
