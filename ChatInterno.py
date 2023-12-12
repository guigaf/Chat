import tkinter as tk
from tkinter import scrolledtext
from datetime import datetime

def send_message(event=None):
    stChatBox.config(state=tk.NORMAL)
    message = eMessage.get()
    nickname = eNickname.get()
    if message:
        full_message = f"{nickname}: {message}"
        with open(f"chat_log_{current_date}.txt", "a") as file:
            file.write(full_message + "\n")
        stChatBox.insert(tk.END, full_message + "\n")
        eMessage.delete(0, tk.END)
    stChatBox.yview(tk.END)
    stChatBox.config(state=tk.DISABLED)

def update_chat_box():

    currentPositionInicio = stChatBox.yview()[0]
    currentPositionFim = stChatBox.yview()[1]

    stChatBox.config(state=tk.NORMAL)
    stChatBox.delete(1.0, tk.END)
    file_name = f"chat_log_{current_date}.txt"
    try:
        with open(file_name, "r") as file:
            content = file.read()
            stChatBox.insert(tk.END, content)
    except FileNotFoundError:
        with open(file_name, "w") as file:
            file.write(f"Ola, bem vindo ao chat, hoje é dia {current_date}" + "\n")
            pass

    if currentPositionFim == 1.0:
        stChatBox.yview(tk.END)
    else:
        stChatBox.yview(tk.MOVETO, currentPositionInicio)

    stChatBox.config(state=tk.DISABLED)
    jChatInterno.after(1000, update_chat_box)

current_date = datetime.now().strftime("%d-%m-%Y")
    
################################################################################################################################################################

jChatInterno = tk.Tk()
jChatInterno.title("Chat Interno")

# label
lNickname = tk.Label(jChatInterno, text="Nome:", width=20)
lNickname.place(x=0, y=10)

# entry
eNickname = tk.Entry(jChatInterno, width=20)
eNickname.grid(row=1, column=0, rowspan=1, columnspan=1, padx=[10, 0], pady=0, sticky='w')

# chat
stChatBox = scrolledtext.ScrolledText(jChatInterno, wrap=tk.WORD, width=60, height=10)
stChatBox.grid(row=0, column=1, rowspan=5, columnspan=2, padx=10, pady=10, sticky='e')
stChatBox.config(state=tk.DISABLED)

# entry
eMessage = tk.Entry(jChatInterno, width=60)
eMessage.grid(row=5, column=1, rowspan=1, columnspan=1, padx=10, pady=10, sticky='w')
eMessage.bind("<Return>", send_message)

# button
bSend = tk.Button(jChatInterno, text="Enviar", command=send_message)
bSend.grid(row=5, column=2, rowspan=1, columnspan=1, padx=10, pady=10, sticky='e')

################################################################################################################################################################
update_chat_box()

jChatInterno.mainloop()
