import tkinter as tk
from tkinter import messagebox, simpledialog, scrolledtext
import socket
import threading

# --- Cấu hình game ---
BOARD_SIZE = 20
CELL_SIZE = 30
WIN_CONDITION = 5

class CaroClient:
    def __init__(self, master):
        self.master = master
        
        # --- Biến trạng thái game và mạng ---
        self.client_socket = None
        self.my_symbol = ''
        self.current_player = ''
        self.game_over = True
        self.board = [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

        # --- Giao diện ---
        self.setup_ui()
        
        # --- Kết nối tới server ---
        self.connect_to_server()

    def setup_ui(self):
        """Thiết lập toàn bộ giao diện người dùng."""
        self.master.title("Cờ Caro Online")
        self.master.resizable(False, False)

        # Frame chính
        main_frame = tk.Frame(self.master)
        main_frame.pack(padx=10, pady=10)
        
        # Frame bàn cờ
        game_frame = tk.Frame(main_frame)
        game_frame.pack(side=tk.LEFT)

        self.status_label = tk.Label(game_frame, text="Chào mừng!", font=("Arial", 14))
        self.status_label.pack(pady=5)

        canvas_size = BOARD_SIZE * CELL_SIZE
        self.canvas = tk.Canvas(game_frame, width=canvas_size, height=canvas_size, bg='lightyellow')
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.handle_click)

        # Frame chat và điều khiển
        control_frame = tk.Frame(main_frame, width=200, padx=10)
        control_frame.pack(side=tk.RIGHT, fill=tk.Y)

        tk.Label(control_frame, text="Chat", font=("Arial", 14)).pack()
        
        self.chat_box = scrolledtext.ScrolledText(control_frame, width=30, height=22, state=tk.DISABLED)
        self.chat_box.pack(pady=5)
        
        self.chat_entry = tk.Entry(control_frame, width=25, font=("Arial", 12))
        self.chat_entry.pack(pady=5)
        self.chat_entry.bind("<Return>", self.send_chat_message)
        
        send_button = tk.Button(control_frame, text="Gửi", command=self.send_chat_message)
        send_button.pack()

        reset_button = tk.Button(control_frame, text="Chơi Lại", command=self.request_reset)
        reset_button.pack(pady=20)
        
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.draw_grid()

    def connect_to_server(self):
        """Hỏi IP và kết nối tới server."""
        server_ip = simpledialog.askstring("Kết nối Server", "Nhập địa chỉ IP của Server:", initialvalue='127.0.0.1')
        if not server_ip:
            self.master.destroy()
            return

        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((server_ip, 65432))
            
            # Bắt đầu luồng nhận dữ liệu từ server
            receive_thread = threading.Thread(target=self.receive_data)
            receive_thread.daemon = True
            receive_thread.start()

            self.update_chat_box("Đã kết nối tới server. Đang chờ người chơi khác...")
        except Exception as e:
            messagebox.showerror("Lỗi kết nối", f"Không thể kết nối tới server: {e}")
            self.master.destroy()

    def receive_data(self):
        """Luồng chạy nền để liên tục nhận dữ liệu từ server."""
        while True:
            try:
                data = self.client_socket.recv(1024).decode('utf-8')
                if not data:
                    break
                self.process_server_message(data)
            except Exception:
                self.update_chat_box("Mất kết nối với server.")
                break

    def process_server_message(self, message):
        """Xử lý các tin nhắn nhận được từ server."""
        parts = message.split('|')
        command = parts[0]
        
        if command == "ROLE":
            self.my_symbol = parts[1]
            self.master.title(f"Cờ Caro Online - Bạn là quân {self.my_symbol}")
        elif command == "START":
            self.reset_game_state()
            self.current_player = parts[1]
            self.status_label.config(text=f"Lượt của: {self.current_player}")
            self.update_chat_box("Trò chơi bắt đầu! Lượt của X.")
        elif command == "MOVE":
            row, col, player = int(parts[1]), int(parts[2]), parts[3]
            self.board[row][col] = 1 if player == 'X' else 2
            self.draw_move(row, col, player)
            if self.check_win(row, col, player):
                self.game_over = True
                self.status_label.config(text=f"Người chơi {player} thắng!")
                messagebox.showinfo("Kết thúc", f"Người chơi {player} đã thắng!")
            elif self.check_draw():
                self.game_over = True
                self.status_label.config(text="Hòa!")
                messagebox.showinfo("Kết thúc", "Ván cờ hòa!")
            else:
                self.current_player = 'O' if player == 'X' else 'X'
                self.status_label.config(text=f"Lượt của: {self.current_player}")
        elif command == "CHAT":
            sender_name = "Đối thủ"
            chat_msg = parts[1]
            self.update_chat_box(f"{sender_name}: {chat_msg}")
        elif command == "RESET":
             self.reset_game_state()
             self.current_player = 'X'
             self.status_label.config(text="Bắt đầu ván mới! Lượt của X.")
             self.update_chat_box("Ván mới đã bắt đầu theo yêu cầu của đối thủ.")
        elif command == "INFO":
            self.update_chat_box(f"[SERVER]: {parts[1]}")
    
    def send_message(self, message):
        """Gửi một tin nhắn tới server."""
        try:
            if self.client_socket:
                self.client_socket.sendall(message.encode('utf-8'))
        except socket.error:
            self.update_chat_box("Lỗi gửi tin nhắn. Có thể đã mất kết nối.")

    def handle_click(self, event):
        """Xử lý khi click chuột lên bàn cờ."""
        if self.game_over or self.my_symbol != self.current_player:
            return

        col = event.x // CELL_SIZE
        row = event.y // CELL_SIZE
        
        if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE and self.board[row][col] == 0:
            # Gửi nước đi tới server
            self.send_message(f"MOVE|{row}|{col}|{self.my_symbol}")

    def send_chat_message(self, event=None):
        """Gửi tin nhắn chat."""
        message = self.chat_entry.get()
        if message:
            self.update_chat_box(f"Bạn: {message}")
            self.send_message(f"CHAT|{message}")
            self.chat_entry.delete(0, tk.END)

    def request_reset(self):
        """Gửi yêu cầu chơi lại tới server."""
        if messagebox.askyesno("Chơi lại", "Bạn có muốn bắt đầu ván mới không?"):
            self.send_message("RESET|")
            self.reset_game_state()
            self.current_player = 'X'
            self.status_label.config(text="Bắt đầu ván mới! Lượt của X.")
            self.update_chat_box("Bạn đã yêu cầu một ván mới.")

    def reset_game_state(self):
        """Reset lại trạng thái bàn cờ ở phía client."""
        self.board = [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.game_over = False
        self.canvas.delete("all")
        self.draw_grid()

    def update_chat_box(self, message):
        """Thêm một tin nhắn vào hộp chat."""
        self.chat_box.config(state=tk.NORMAL)
        self.chat_box.insert(tk.END, message + "\n")
        self.chat_box.config(state=tk.DISABLED)
        self.chat_box.see(tk.END)

    def draw_grid(self):
        for i in range(BOARD_SIZE + 1):
            self.canvas.create_line(i * CELL_SIZE, 0, i * CELL_SIZE, BOARD_SIZE * CELL_SIZE, fill="gray")
            self.canvas.create_line(0, i * CELL_SIZE, BOARD_SIZE * CELL_SIZE, i * CELL_SIZE, fill="gray")

    def draw_move(self, row, col, player):
        x0, y0 = col * CELL_SIZE + 5, row * CELL_SIZE + 5
        x1, y1 = (col + 1) * CELL_SIZE - 5, (row + 1) * CELL_SIZE - 5
        if player == 'X':
            self.canvas.create_line(x0, y0, x1, y1, width=3, fill='blue')
            self.canvas.create_line(x0, y1, x1, y0, width=3, fill='blue')
        else:
            self.canvas.create_oval(x0, y0, x1, y1, width=3, outline='red')

    def check_win(self, row, col, player):
        player_value = 1 if player == 'X' else 2
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for dr, dc in directions:
            count = 1
            for i in range(1, WIN_CONDITION):
                r, c = row + i * dr, col + i * dc
                if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and self.board[r][c] == player_value:
                    count += 1
                else: break
            for i in range(1, WIN_CONDITION):
                r, c = row - i * dr, col - i * dc
                if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and self.board[r][c] == player_value:
                    count += 1
                else: break
            if count >= WIN_CONDITION: return True
        return False
        
    def check_draw(self):
        return all(self.board[r][c] != 0 for r in range(BOARD_SIZE) for c in range(BOARD_SIZE))

    def on_closing(self):
        """Xử lý khi người dùng đóng cửa sổ."""
        if self.client_socket:
            self.client_socket.close()
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = CaroClient(root)
    root.mainloop()