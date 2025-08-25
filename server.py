import socket
import threading

# --- Cấu hình server ---
HOST = '127.0.0.1'  # Chấp nhận kết nối từ mọi địa chỉ. 
                   # Nếu chơi trên cùng máy, dùng '127.0.0.1'.
                   # Nếu chơi qua mạng LAN, dùng địa chỉ IP của máy chủ (ví dụ: '192.168.1.10')
PORT = 65432       # Port để lắng nghe

clients = []
players = {}
lock = threading.Lock()

def broadcast(message, sender_conn):
    """Gửi tin nhắn tới tất cả client ngoại trừ người gửi."""
    with lock:
        for client_conn in clients:
            if client_conn != sender_conn:
                try:
                    client_conn.sendall(message)
                except socket.error:
                    print(f"Lỗi: Không thể gửi tin nhắn. Client có thể đã ngắt kết nối.")
                    clients.remove(client_conn)


def handle_client(conn, addr):
    """Xử lý kết nối từ một client."""
    print(f"[KẾT NỐI MỚI] {addr} đã kết nối.")
    
    player_symbol = ''
    with lock:
        clients.append(conn)
        # Gán vai trò cho người chơi
        if len(clients) == 1:
            player_symbol = 'X'
            players[conn] = 'X'
            conn.sendall(b"ROLE|X")
            print(f"Gán vai trò 'X' cho {addr}")
        elif len(clients) == 2:
            player_symbol = 'O'
            players[conn] = 'O'
            conn.sendall(b"ROLE|O")
            print(f"Gán vai trò 'O' cho {addr}")
            
            # Thông báo cho người chơi đầu tiên rằng game bắt đầu
            clients[0].sendall(b"START|X") # Bắt đầu với lượt của X
            clients[1].sendall(b"START|X")

    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break # Client ngắt kết nối
            
            print(f"Nhận từ {players.get(conn, 'Unknown')}: {data.decode('utf-8')}")
            broadcast(data, conn)

    except ConnectionResetError:
        print(f"[NGẮT KẾT NỐI] {addr} đã ngắt kết nối đột ngột.")
    except Exception as e:
        print(f"[LỖI] {e}")
    finally:
        print(f"[NGẮT KẾT NỐI] {addr} đã ngắt kết nối.")
        with lock:
            if conn in clients:
                clients.remove(conn)
            if conn in players:
                del players[conn]
        
        # Thông báo cho client còn lại
        if len(clients) > 0:
            broadcast("INFO|Đối thủ đã thoát!".encode('utf-8'), conn)        
            conn.close()


def start_server():
    """Khởi động server và lắng nghe kết nối."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(2) # Chỉ cho phép tối đa 2 kết nối chờ
    print(f"[ĐANG LẮNG NGHE] Server đang lắng nghe trên {HOST}:{PORT}")

    while True:
        try:
            conn, addr = server_socket.accept()
            if len(clients) >= 2:
                print(f"[TỪ CHỐI] Đã đủ 2 người chơi, từ chối kết nối từ {addr}")
                conn.sendall("INFO|Phòng đã đầy!".encode('utf-8'))
                conn.close()
                continue

            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.daemon = True
            thread.start()
        except KeyboardInterrupt:
            print("\n[DỪNG SERVER] Đang đóng server...")
            server_socket.close()
            break

if __name__ == "__main__":
    start_server()