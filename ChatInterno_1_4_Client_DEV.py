import socket
import tkinter as tk
from tkinter import scrolledtext, simpledialog, Toplevel
from tkcalendar import Calendar
from datetime import datetime
import threading
from queue import Queue
import getpass
from plyer import notification
import time
#plyer.platforms.win.notification

messages = []

filtroData = False
filtroHora = True

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
    global dataAtual
    global horaAtual

    message = eMessage.get()
    nickname = get_username()
    mensagemTipo = "mensagem"
    if message and nickname:
        full_message = f"{dataAtual} {horaAtual};{nickname};{message};{mensagemTipo}"

        client_socket.sendall(full_message.encode('utf-8'))
        eMessage.delete(0, tk.END)

def send_entry_message():
    global client_socket
    global dataAtual
    global horaAtual

    message = f"entrou no chat."
    nickname = get_username()
    mensagemTipo = "entrada"
    full_message = f"{dataAtual} {horaAtual};{nickname};{message};{mensagemTipo}"
    client_socket.sendall(full_message.encode('utf-8'))

def send_warning_message():
    global client_socket
    global dataAtual
    global horaAtual

    message = f"--ATENÇÃO--"
    nickname = get_username()
    mensagemTipo = "atencao"
    full_message = f"{dataAtual} {horaAtual};{nickname};{message};{mensagemTipo}"
    client_socket.sendall(full_message.encode('utf-8'))

def send_exit_message():
    global client_socket
    global dataAtual
    global horaAtual

    message = f"saiu do chat."
    nickname = get_username()
    mensagemTipo = "saida"
    full_message = f"{dataAtual} {horaAtual};{nickname};{message};{mensagemTipo}"
    client_socket.sendall(full_message.encode('utf-8'))

def apply_tags_and_filter(message):
    global filtroData
    global filtroHora

    filtroRemetente = True
    filtroConteudo = True
    filtroTipo = False

    particao = message.split(";")

    dataHora = particao[0]
    dataHoraSplited = dataHora.split(" ")
    data = dataHoraSplited[0]
    hora = dataHoraSplited[1]

    remetente = particao[1]
    conteudo = particao[2]
    tipo = particao[3]

    mensagemFormatada = ''

    # Verifica qual filtro aplicar a mensagem a depender das configuraçõs do Client
    if filtroData:
        if filtroHora:
            mensagemFormatada = f'({data}'
        else:
            mensagemFormatada = f'({data})'
    if filtroHora:
        if mensagemFormatada == '':
            mensagemFormatada = f'({hora})'
        else:
            mensagemFormatada = f'{mensagemFormatada} {hora})'
    if filtroRemetente:
        if mensagemFormatada == '':
            mensagemFormatada = f'{remetente}'
        else:
            mensagemFormatada = f'{mensagemFormatada}{remetente}'
    if filtroConteudo:
        if mensagemFormatada == '':
            mensagemFormatada = f'{conteudo}'
        else:
            mensagemFormatada = f'{mensagemFormatada}:{conteudo}'
    if filtroTipo:
        if mensagemFormatada == '':
            mensagemFormatada = f'{tipo}'
        else:
            mensagemFormatada = f'{mensagemFormatada} - {tipo}'

    # Se a mensagem indica saída, aplica a tag "exit_message"
    if "saida" in tipo:
        return mensagemFormatada, "exit_message"
    
    # Se a mensagem indica entrada, aplica a tag "entry_message"
    elif "entrada" in tipo:
        return mensagemFormatada, "entry_message"
    
    # Se a mensagem indica atenção, aplica a tag "warning_message"
    elif "atencao" in tipo:
        return mensagemFormatada, "warning_message"
    
    # Se a mensagem indica mensagem, não aplica tag
    elif "mensagem" in tipo:
        return mensagemFormatada, None
    
    # Se a mensagem não indica nada, não aplica tag
    else:
        return mensagemFormatada, None

def update_chat_box():
    global stChatBox
    global messages

    #thread_update_date_time()

    # Ao atualizar o ChatBox ainda esta ocorrendo um bug, 
    # caso uma UNICA mensagem tenha um tamanho horizontal maior que o tamanho do ChatBox, 
    # ela fica "andando" sozinha na tela, isso se deve ao fato de ela se perder nos calulos de posição,
    # pois para a ChatBox, virtualmente, ela sempre ocupa uma linha 
    currentPositionInicio = stChatBox.yview()[0] # Grava a posição inicial do ChatBox
    currentPositionFim = stChatBox.yview()[1] # Grava a posição final do ChatBox

    stChatBox.config(state=tk.NORMAL) # Coloca ChartBox em edição
    stChatBox.delete(1.0, tk.END) # Deleta o conteudo do ChatBox
    try:
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
    except Exception as e:
        pass
    stChatBox.config(state=tk.DISABLED)

def windows_notification(message):
    global jChatPrincipal

    particao = message.split(";")

    dataHora = particao[0]
    remetente = particao[1]
    conteudo = particao[2]
    tipo = particao[3]
    
    msgNickname = remetente
    myNickname = get_username()
    try:
        if jChatPrincipal.windowsNotification and myNickname not in msgNickname and tipo == "atencao":
                notification.notify(title='Atenção!', message=f'{msgNickname} esta chamando sua atenção.', app_name='ATENÇÃO!', timeout=1, )
    except Exception as e:
        print(f'Erro de notificação do Windows: {e}')
        pass

def receive_messages():
    global messages
    global client_socket
    global jChatPrincipal

    while True:
        try:
            #thread_update_date_time()
            message = client_socket.recv(1024).decode('utf-8')
            if not message:
                break

            with lock:
                conteudo_ok, tag = apply_tags_and_filter(message)
                messages.append((conteudo_ok, tag))
                windows_notification(message)
            print(f"Received message: {message}")

        except Exception as e:
            print(f"Error receiving message: {e}")
            break
        
        finally:
            jChatPrincipal.after(200, update_chat_box)
    
def load_messages_from_server(buscaData):
    global client_socket

    message = f"load_messages_from_server;{buscaData}"
    client_socket.sendall(message.encode('utf-8'))

def update_date_time():
    global dataAtual
    global horaAtual

    while True:
        dataAtual = datetime.now().strftime("%d-%m-%Y")
        horaAtual = datetime.now().strftime("%H:%M:%S")

        #print("dataAtual: ", dataAtual)
        #print("horaAtual: ", horaAtual)

        time.sleep(1)
    
def on_closing():
    global jChatPrincipal
    global client_socket

    if newIp != None:
        send_exit_message()

        client_socket.close()

    jChatPrincipal.destroy()

def windows_notification_true():
    global jChatPrincipal
    global menuOpcoesNotificacoes

    jChatPrincipal.windowsNotification = True
    menuOpcoesNotificacoes.entryconfig("Habilitar notificações", state='disabled')
    menuOpcoesNotificacoes.entryconfig("Desabilitar notificações", state='active')

def windows_notification_false():
    global jChatPrincipal
    global menuOpcoesNotificacoes

    jChatPrincipal.windowsNotification = False
    menuOpcoesNotificacoes.entryconfig("Habilitar notificações", state='active')
    menuOpcoesNotificacoes.entryconfig("Desabilitar notificações", state='disabled')

def thread_received_message():
    # Thread para receber mensagens
    receive_thread = threading.Thread(name="thread_received_message", target=receive_messages, daemon=True)
    receive_thread.start()

def thread_update_date_time():
    # Thread atualizar a data e hora atual
    update_date_time_thread = threading.Thread(target=update_date_time, daemon=True)
    update_date_time_thread.start()

# Função para abrir a caixa de diálogo e obter um novo endereço IP
def new_ip_selector():
    global client_socket
    global eMessage
    global bAtencao
    global oldIp
    global newIp
    global jChatPrincipal

    while True:
        newIp = simpledialog.askstring("Novo Endereço IP", "Digite o novo endereço IP:")
        if newIp:
            try:
                # Seleciona o endereço de IP que vai se conectar
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.connect((newIp, 5555))
                jChatPrincipal.title(f'Bem Vindo! - {nickname} - STATUS: CONECTADO -> {newIp}')

                oldIp = newIp
                bAtencao.config(state=tk.NORMAL)
                eMessage.config(state=tk.NORMAL)
                break
            except Exception as e:
                jChatPrincipal.title(f'Bem Vindo! - {nickname} - STATUS: DESCONECTADO')
                bAtencao.config(state=tk.DISABLED)
                eMessage.config(state=tk.DISABLED)
                print(f'Erro no new_ip_selector: {e}')
                continue
        elif oldIp != None:
            try:
                # Seleciona o endereço de IP que vai se conectar
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.connect((oldIp, 5555))
                jChatPrincipal.title(f'Bem Vindo! - {nickname} - STATUS: CONECTADO -> {oldIp}')

                bAtencao.config(state=tk.NORMAL)
                eMessage.config(state=tk.NORMAL)
                break
            except Exception as e:
                jChatPrincipal.title(f'Bem Vindo! - {nickname} - STATUS: DESCONECTADO')
                bAtencao.config(state=tk.DISABLED)
                eMessage.config(state=tk.DISABLED)
                print(f'Erro no new_ip_selector: {e}')
                continue
        elif newIp == None:
            on_closing()
            break

###################################################################################################################################################
def janela_principal():
    # Inicializações
    global dataAtual
    global jChatPrincipal
    global menuOpcoesNotificacoes
    global eMessage
    global stChatBox
    global messages
    global bAtencao
    global cbCurrentDateVar
    global cbCurrentTimeVar
    global dataSelecionadaFormatada

    # Verifica a data atual
    thread_update_date_time()

    # Cria janela do chat
    jChatPrincipal = tk.Tk()

    # Coloca um titulo na janela do chat
    jChatPrincipal.title(f'Bem Vindo! - {nickname} - STATUS: DESCONECTADO')

    # Adiciona um script ao botão de fechar padrão da janela
    jChatPrincipal.protocol("WM_DELETE_WINDOW", on_closing)

    # Adiciona e configura um ScrolledText a janela
    stChatBox = scrolledtext.ScrolledText(jChatPrincipal, wrap=tk.WORD, width=60, height=10)
    stChatBox.grid(row=0, column=0, columnspan=3, padx=10, pady=10, sticky='nsew')
    stChatBox.tag_config("exit_message", foreground="#FF0000")
    stChatBox.tag_config("entry_message", foreground="#0000FF")
    stChatBox.tag_config("warning_message", foreground="#006600")
    stChatBox.config(state=tk.DISABLED)

    # Adiciona um campo apra digitar mensagem
    eMessage = tk.Entry(jChatPrincipal, width=60)
    eMessage.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky='ew')
    eMessage.config(state=tk.DISABLED)

    # vincula o campo de mensagem ao botão "Enter" e a função send_message
    eMessage.bind("<Return>", send_message)

    # Adiciona um campo para chamar a atenção do usuario
    bAtencao = tk.Button(jChatPrincipal, text="ATENÇÃO", command=send_warning_message)
    bAtencao.grid(row=1, column=2, padx=10, pady=10, sticky='e')
    bAtencao.config(state=tk.DISABLED)

    # Configuração do peso da linha e coluna
    jChatPrincipal.grid_rowconfigure(0, weight=1)
    jChatPrincipal.grid_rowconfigure(1, weight=0)
    jChatPrincipal.grid_columnconfigure(0, weight=1)
    jChatPrincipal.grid_columnconfigure(1, weight=1)
    jChatPrincipal.grid_columnconfigure(2, weight=0)

    # Inicializa variavel global para verificar se o usuario quer receber notificação, se inicia em "True"
    jChatPrincipal.windowsNotification = True

###################################################################################################################################################

    menuBar = tk.Menu(jChatPrincipal)

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
    menuOpcoes.add_command(label="Histórico", command=janela_opcoes)

    # Adicionar a barra de menu à janela
    jChatPrincipal.config(menu=menuBar)

###################################################################################################################################################

    jChatPrincipal.iconify()

    # Variável para armazenar o estado do checkbox
    cbCurrentDateVar = tk.BooleanVar()
    cbCurrentDateVar.set(filtroData)
    
    cbCurrentTimeVar = tk.BooleanVar()
    cbCurrentTimeVar.set(filtroHora)

    new_ip_selector()
    if newIp != None:
        jChatPrincipal.deiconify()
        
        # Carrega uma vez a lista de mensagens presentes no LOG
        load_messages_from_server(dataAtual)

        thread_received_message()

        send_entry_message()

        # mainLoop da janela principal
        jChatPrincipal.mainloop()

###################################################################################################################################################

def recarregar_mensagens():
    global jChatOpcoes
    global stChatBox
    global messages
    global dataSelecionadaFormatada

    stChatBox.config(state=tk.NORMAL) # Habilita o ChatBox para edição

    stChatBox.delete(1.0, tk.END) # Limpa o ChatBox
    messages.clear() # Limpa a lista de mensagens
    load_messages_from_server(dataSelecionadaFormatada) # Faz uma requisição ao servidor para retornar todas as mensagens do banco
    
    stChatBox.config(state=tk.DISABLED)# desabilita o ChatBox para edição    

    jChatOpcoes.destroy()

def cbCurrentDate_command():
    global filtroData
    global cbCurrentDateVar

    filtroData = True if cbCurrentDateVar.get() else False

def cbCurrentTime_command():
    global filtroHora
    global cbCurrentTimeVar

    filtroHora = True if cbCurrentTimeVar.get() else False

def fecha_janela_opcoes():
    recarregar_mensagens()

##########################################################################################
################             SELETOR DE DATA #############################################
def selecionar_data():
    global jSeletorData
    global calSeletorData
    global lData
    global dataSelecionadaFormatada

    # Seleciona a data do calendario, ela vem no formato String
    dataSelecionadaStr = calSeletorData.get_date()

    # Altera a data do calendario do formato String para DateTime
    dataSelecionadaDateTime = datetime.strptime(dataSelecionadaStr, "%m/%d/%y")

    # Altera a data para o formato String aplicando formatação
    dataSelecionadaFormatada = dataSelecionadaDateTime.strftime("%d-%m-%Y")
    lData.config(text=dataSelecionadaFormatada)
    jSeletorData.destroy()

def abrir_seletor_data():
    global jSeletorData
    global dataAtual
    global horaAtual
    global calSeletorData

    seletorDia = datetime.now().strftime("%d")
    seletorMes = datetime.now().strftime("%m")
    seletorAno = datetime.now().strftime("%Y")    

    jSeletorData = tk.Toplevel(jChatOpcoes)
    jSeletorData.title("Seletor de Data")
    
    calSeletorData = Calendar(jSeletorData, selectmode="day", year=int(seletorAno), month=int(seletorMes), day=int(seletorDia))
    calSeletorData.pack(padx=10, pady=10)

    bSeletorData = tk.Button(jSeletorData, text="OK", command=selecionar_data)
    bSeletorData.pack(pady=10)
################             SELETOR DE DATA #############################################
##########################################################################################
    
def janela_opcoes():
    global jChatOpcoes
    global cbCurrentDateVar
    global cbCurrentTimeVar
    global lData
    global bDateSelector
    global dataAtual
    global dataSelecionadaFormatada

    dataSelecionadaFormatada = dataAtual

    jChatOpcoes = Toplevel(jChatPrincipal)
    jChatOpcoes.title("Opções")

    # Adiciona um script ao botão de fechar padrão da janela
    jChatOpcoes.protocol("WM_DELETE_WINDOW", fecha_janela_opcoes)

    cbCurrentDate = tk.Checkbutton(jChatOpcoes, text="Data", variable=cbCurrentDateVar, command=cbCurrentDate_command)
    cbCurrentDate.grid(row=0, column=0, padx=10, pady=10)

    cbCurrentTime = tk.Checkbutton(jChatOpcoes, text="Hora", variable=cbCurrentTimeVar, command=cbCurrentTime_command)
    cbCurrentTime.grid(row=0, column=1, padx=10, pady=10)

    lData = tk.Label(jChatOpcoes, text=dataAtual)
    lData.grid(row=1, column=0, padx=10, pady=10)

    # Seletor de data
    bDateSelector = tk.Button(jChatOpcoes, text="...", command=abrir_seletor_data)
    bDateSelector.grid(row=1, column=1, padx=0, pady=10)

###################################################################################################################################################

# Memorias globais
lock = threading.Lock()
nickname = get_username()
oldIp = None

###################################################################################################################################################

if __name__ == "__main__":
    # Inicia a interface gráfica
    janela_principal()