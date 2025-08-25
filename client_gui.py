import socket
import threading
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk  

HOST = '127.0.0.1'
PORT = 65432

class GameClient:
    def __init__(self, master):
        self.master = master
        master.title("Keo Bua Bao Client")
        master.geometry("400x300")
        master.resizable(False, False)

        self.label = tk.Label(master, text="Chọn kéo, búa, bao:", font=("Arial", 14))
        self.label.pack(pady=10)

        self.choice_var = tk.StringVar()
        self.choice_var.set("keo")

        # Load images
        self.img_keo = ImageTk.PhotoImage(Image.open("keo.png").resize((60,60)))
        self.img_bua = ImageTk.PhotoImage(Image.open("bua.png").resize((60,60)))
        self.img_bao = ImageTk.PhotoImage(Image.open("bao.png").resize((60,60)))

        # Frame cho các lựa chọn
        frame = tk.Frame(master)
        frame.pack(pady=10)

        self.keo_btn = tk.Radiobutton(frame, image=self.img_keo, variable=self.choice_var, value="keo")
        self.keo_btn.grid(row=0, column=0, padx=15)
        tk.Label(frame, text="Kéo", font=("Arial", 12)).grid(row=1, column=0)

        self.bua_btn = tk.Radiobutton(frame, image=self.img_bua, variable=self.choice_var, value="bua")
        self.bua_btn.grid(row=0, column=1, padx=15)
        tk.Label(frame, text="Búa", font=("Arial", 12)).grid(row=1, column=1)

        self.bao_btn = tk.Radiobutton(frame, image=self.img_bao, variable=self.choice_var, value="bao")
        self.bao_btn.grid(row=0, column=2, padx=15)
        tk.Label(frame, text="Bao", font=("Arial", 12)).grid(row=1, column=2)

        self.send_btn = tk.Button(master, text="Gửi lựa chọn", font=("Arial", 12), command=self.send_choice, bg="#4CAF50", fg="white")
        self.send_btn.pack(pady=15)

        self.result_label = tk.Label(master, text="", font=("Arial", 13), fg="#333")
        self.result_label.pack(pady=10)

        self.client = None
        self.connect_to_server()

    def connect_to_server(self):
        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect((HOST, PORT))
            welcome = self.client.recv(1024).decode()
            self.result_label.config(text=f"Server: {welcome}")
        except Exception as e:
            messagebox.showerror("Lỗi kết nối", f"Không thể kết nối đến server: {e}")
            self.master.destroy()

    def send_choice(self):
        choice = self.choice_var.get()
        try:
            self.client.sendall(choice.encode())
            self.result_label.config(text="Đang chờ kết quả...")
            threading.Thread(target=self.receive_result, daemon=True).start()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi gửi lựa chọn: {e}")
            self.master.destroy()

    def receive_result(self):
        try:
            result = self.client.recv(1024).decode()
            self.result_label.config(text=f"Server: {result}")
            self.client.close()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi nhận kết quả: {e}")
            self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = GameClient(root)
    root.mainloop()