from flask import Flask
from dash import Dash, html, dcc, Input, Output, State
import socketio
import getpass

# Configuração do Flask
app = Flask(__name__)
sio = socketio.Server()

# Função para obter o nome de usuário
def get_username():
    try:
        username = getpass.getuser()
    except Exception as e:
        username = "Guest"  # Caso não seja possível obter o nome de usuário
    return username

# Configuração do Dash
dash_app = Dash(__name__, server=app, url_base_pathname='/dashboard/')

# Lista para armazenar as mensagens
messages = []

# Layout do Dash
dash_app.layout = html.Div([
    dcc.Textarea(id='textarea', value='', placeholder='Digite sua mensagem...'),
    html.Button('Enviar', id='button'),
    html.Ul(id='message-list', children=[]),
    dcc.Input(id='hidden-input', type='text', style={'display': 'none'})  # Componente oculto para capturar o evento 'enter'
])

# Callback do Dash para atualizar a lista de mensagens e limpar o textarea
@dash_app.callback([Output('message-list', 'children'),
                   Output('textarea', 'value')],
                   [Input('button', 'n_clicks'),
                    Input('hidden-input', 'n_submit')],
                   [State('textarea', 'value')])  # 'textarea' é um State agora
def update_messages(n_clicks, n_submit, value):
    # Se o botão foi clicado ou a tecla Enter foi pressionada
    if (n_clicks is not None and n_clicks > 0) or (n_submit is not None and n_submit > 0):
        # Adiciona a nova mensagem à lista de mensagens com o nome de usuário
        username = get_username()
        messages.append(f"{username}: {value}")

    # Limpa o valor da textarea após o envio da mensagem
    return [html.Li(msg) for msg in messages], ''

# Evento do Socket.IO para lidar com mensagens recebidas
@sio.event
def message(sid, data):
    # Adiciona a mensagem recebida à lista de mensagens
    username = get_username()
    messages.append(f"{username}: {data}")
    sio.emit('message', data)

if __name__ == '__main__':
    socketio.WSGIApp(sio, app)
    dash_app.run_server(debug=True, host='0.0.0.0')
