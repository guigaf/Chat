import socket
import tkinter as tk
from tkinter import scrolledtext, simpledialog
from datetime import datetime
import threading
from queue import Queue
import os
import getpass
from plyer import notification
#plyer.platforms.win.notification

###################################################################################################################################################
# Função para obter o nome de usuário
def get_username():
    try:
        username = getpass.getuser()
    except Exception as e:
        username = "Guest"  # Caso não seja possível obter o nome de usuário
    return username

def send_message(event=None):
    global eMessage
    global client_socket

    message = eMessage.get()
    nickname = get_username()
    if message and nickname:
        full_message = f"{nickname}: {message}"

        client_socket.sendall(full_message.encode('utf-8'))
        eMessage.delete(0, tk.END)

def send_entry_message():
    global client_socket

    entry_message = f"{get_username()} entrou no chat."
    client_socket.sendall(entry_message.encode('utf-8'))

def send_warning_message():
    global client_socket

    warning_message = f"{get_username()}: --ATENÇÃO--"
    client_socket.sendall(warning_message.encode('utf-8'))

def send_exit_message():
    global client_socket

    exit_message = f"{get_username()} saiu do chat."
    client_socket.sendall(exit_message.encode('utf-8'))

def apply_tags(message):
    # Se a mensagem indica saída, aplica a tag "exit_message"
    if "saiu do chat" in message and ":" not in message:
        return message, "exit_message"
    elif "entrou no chat" in message and ":" not in message:
        return message, "entry_message"
    elif "--ATENÇÃO--" in message:
        return message, "warning_message"
    else:
        return message, None

def update_chat_box():
    global jChatInterno
    global stChatBox
    global messages

    # Ao atualizar o ChatBox ainda esta ocorrendo um bug, 
    # caso uma UNICA mensagem tenha um tamanho horizontal maior que o tamanho do ChatBox, 
    # ela fica "andando" sozinha na tela, isso se deve ao fato de ela se perder nos calulos de posição,
    # pois para a ChatBox, virtualmente, ela sempre ocupa uma linha 
    currentPositionInicio = stChatBox.yview()[0] # Grava a posição inicial do ChatBox
    currentPositionFim = stChatBox.yview()[1] # Grava a posição final do ChatBox

    stChatBox.config(state=tk.NORMAL) # Coloca ChartBox em edição
    stChatBox.delete(1.0, tk.END) # Deleta o conteudo do ChatBox
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
    # Verifica o posicionamento da janela
    if currentPositionFim == 1.0:
        stChatBox.yview(tk.END)
    else:
        stChatBox.yview(tk.MOVETO, currentPositionInicio)
    stChatBox.config(state=tk.DISABLED)

def windows_notification(message):
    global jChatInterno

    particao = message.split(":", 1)
    msgNickname = particao[0].strip()
    myNickname = get_username()
    if jChatInterno.windowsNotification and myNickname not in msgNickname:
        try:
            if "--ATENÇÃO--" in message:
                notification.notify(title='Atenção!', message=f'{msgNickname} esta chamando sua atenção.', app_name='ATENÇÃO!', timeout=1, )
        except Exception as e:
            print(f'Erro de notificação do Windows: {e}')
            pass

def receive_messages():
    global messages
    global client_socket

    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if not message:
                break
            
            with lock:
                message, tag = apply_tags(message)
                messages.append((message, tag))
                windows_notification(message)

            print(f"Received message: {message}")

        except Exception as e:
            print(f"Error receiving message: {e}")
            break
        
        finally:
            jChatInterno.after(200, update_chat_box)

def load_messages_from_file():
    global current_date
    global client_socket

    file_name = f"chat_log_{current_date}.txt"
    try:
        with open(file_name, "r") as file:
            content = file.read()
            contentSplitLines = content.splitlines()
            result = []
            for verifyContent in contentSplitLines:
                verifyContentOK, tag = apply_tags(verifyContent)
                result.append((verifyContentOK, tag))
            return result
    except FileNotFoundError:
        return []
    except Exception as e:
        print(f"Error loading messages from file: {e}")
        return []

    # Envia mensagem
    entry_message = f"{get_username()} entrou no chat."
    client_socket.sendall(entry_message.encode('utf-8'))

    # Recebe resposta do server

def on_closing():
    global jChatInterno

    send_exit_message()
    jChatInterno.destroy()

def windows_notification_true():
    global jChatInterno
    global menuOpcoesNotificacoes

    jChatInterno.windowsNotification = True
    menuOpcoesNotificacoes.entryconfig("Habilitar notificações", state='disabled')
    menuOpcoesNotificacoes.entryconfig("Desabilitar notificações", state='active')

def windows_notification_false():
    global jChatInterno
    global menuOpcoesNotificacoes

    jChatInterno.windowsNotification = False
    menuOpcoesNotificacoes.entryconfig("Habilitar notificações", state='active')
    menuOpcoesNotificacoes.entryconfig("Desabilitar notificações", state='disabled')

def thread_received_message():
    # Thread para receber mensagens
    receive_thread = threading.Thread(target=receive_messages, daemon=True)
    receive_thread.start()

# Função para abrir a caixa de diálogo e obter um novo endereço IP
def new_ip_selector():
    global client_socket
    global eMessage
    global bAtencao
    global oldIp

    while True:
        #newIp = open_new_window()
        newIp = simpledialog.askstring("Novo Endereço IP", "Digite o novo endereço IP:")
        if newIp:
            try:
                # Seleciona o endereço de IP que vai se conectar
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.connect((newIp, 5555))
                jChatInterno.title(f'Bem Vindo! - {nickname} - STATUS: CONECTADO -> {newIp}')
                #192.168.0.90 - marcos

                oldIp = newIp
                bAtencao.config(state=tk.NORMAL)
                eMessage.config(state=tk.NORMAL)
                break
            except Exception as e:
                jChatInterno.title(f'Bem Vindo! - {nickname} - STATUS: DESCONECTADO')
                bAtencao.config(state=tk.DISABLED)
                eMessage.config(state=tk.DISABLED)
                print(f'Erro no new_ip_selector: {e}')
                continue
        elif oldIp != None:
            try:
                # Seleciona o endereço de IP que vai se conectar
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.connect((oldIp, 5555))
                jChatInterno.title(f'Bem Vindo! - {nickname} - STATUS: CONECTADO -> {oldIp}')
                #192.168.0.90 - marcos

                bAtencao.config(state=tk.NORMAL)
                eMessage.config(state=tk.NORMAL)
                break
            except Exception as e:
                jChatInterno.title(f'Bem Vindo! - {nickname} - STATUS: DESCONECTADO')
                bAtencao.config(state=tk.DISABLED)
                eMessage.config(state=tk.DISABLED)
                print(f'Erro no new_ip_selector: {e}')
                continue
        else:
            continue

###################################################################################################################################################
def interface_grafica():
    # Inicializações
    global current_date
    global jChatInterno
    global menuOpcoesNotificacoes
    global eMessage
    global stChatBox
    global messages
    global bAtencao

    # Verifica a data atual
    current_date = datetime.now().strftime("%d-%m-%Y")

    # Cria janela do chat
    jChatInterno = tk.Tk()

    # Coloca um titulo na janela do chat
    jChatInterno.title(f'Bem Vindo! - {nickname} - STATUS: DESCONECTADO')

    # Adiciona um script ao botão de fechar padrão da janela
    jChatInterno.protocol("WM_DELETE_WINDOW", on_closing)

    # Adiciona e configura um ScrolledText a janela
    stChatBox = scrolledtext.ScrolledText(jChatInterno, wrap=tk.WORD, width=60, height=10)
    stChatBox.grid(row=0, column=0, columnspan=3, padx=10, pady=10, sticky='nsew')
    stChatBox.tag_config("exit_message", foreground="#FF0000")
    stChatBox.tag_config("entry_message", foreground="#0000FF")
    stChatBox.tag_config("warning_message", foreground="#006600")
    stChatBox.config(state=tk.DISABLED)

    # Adiciona um campo apra digitar mensagem
    eMessage = tk.Entry(jChatInterno, width=60)
    eMessage.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky='ew')
    eMessage.config(state=tk.DISABLED)

    # vincula o campo de mensagem ao botão "Enter" e a função send_message
    eMessage.bind("<Return>", send_message)

    # Adiciona um campo para chamar a atenção do usuario
    bAtencao = tk.Button(jChatInterno, text="ATENÇÃO", command=send_warning_message)
    bAtencao.grid(row=1, column=2, padx=10, pady=10, sticky='e')
    bAtencao.config(state=tk.DISABLED)

    # Configuração do peso da linha e coluna
    jChatInterno.grid_rowconfigure(0, weight=1)
    jChatInterno.grid_rowconfigure(1, weight=0)
    jChatInterno.grid_columnconfigure(0, weight=1)
    jChatInterno.grid_columnconfigure(1, weight=1)
    jChatInterno.grid_columnconfigure(2, weight=0)

    # Inicializa variavel global para verificar se o usuario quer receber notificação, se inicia em "True"
    jChatInterno.windowsNotification = True

    ###################################################################################################################################################

    menuBar = tk.Menu(jChatInterno)

    # Criar o menu "Arquivo" com alguns itens
    menuArquivo = tk.Menu(menuBar, tearoff=0)
    menuArquivo.add_command(label="Sair", command=on_closing)

    # Criar o menu "Opções" com alguns itens
    menuOpcoes = tk.Menu(menuBar, tearoff=0)

    # Criar o menu "Notificacoes" com alguns itens
    menuOpcoesNotificacoes = tk.Menu(menuBar, tearoff=0)
    menuOpcoesNotificacoes.add_command(label="Habilitar notificações", command=windows_notification_true, state='disabled')
    menuOpcoesNotificacoes.add_command(label="Desabilitar notificações", command=windows_notification_false, state='active')

    # Adicionar o menu "Arquivo" à barra de menu
    menuBar.add_cascade(label="Arquivo", menu=menuArquivo)

    # Adicionar o menu "Opções" à barra de menu
    menuBar.add_cascade(label="Opções", menu=menuOpcoes)

    # Adicionar o menu "Notificações" e "Alterar Servidor" à barra de "Opções"
    menuOpcoes.add_command(label="Alterar Servidor", command=new_ip_selector)
    menuOpcoes.add_separator()
    menuOpcoes.add_cascade(label="Notificações", menu=menuOpcoesNotificacoes)

    # Adicionar a barra de menu à janela
    jChatInterno.config(menu=menuBar)

###################################################################################################################################################

    jChatInterno.iconify()

    new_ip_selector()

    jChatInterno.deiconify()
    
    thread_received_message()

    # Carrega uma vez a lista de mensagens presentes no LOG
    messages = load_messages_from_file()

    send_entry_message()

    # Atualiza a caixa de chat
    jChatInterno.after(200, update_chat_box)

    # mainLoop da janela principal
    jChatInterno.mainloop()

###################################################################################################################################################

# Memorias globais
lock = threading.Lock()
nickname = get_username()
oldIp = None

###################################################################################################################################################

if __name__ == "__main__":
    # Inicia a interface gráfica
    interface_grafica()