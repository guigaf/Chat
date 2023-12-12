import tkinter as tk
from plyer import notification

class App:
    def __init__(self, root):
        self.root = root
        root.title("Janela Piscante")
        root.geometry("300x200")

        # Cria um botão que ao ser clicado faz a janela piscar
        btn_blink = tk.Button(root, text="Piscar", command=self.blink_window)
        btn_blink.pack(pady=20)

    def blink_window(self):
        # Chama a função para exibir uma notificação
        self.show_notification()

    def show_notification(self):
        # Exibe uma notificação usando a biblioteca plyer
        notification.notify(
            title='Atenção!',
            message='Sua janela está piscando.',
            app_name='Janela Piscante',
        )

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()