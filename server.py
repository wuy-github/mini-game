import socket
import threading
import sys

HOST = '127.0.0.1'
PORT = 65432

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen()

print(f"Server dang lang nghe tren {HOST}:{PORT}")

clients = []
rooms = {}

def input_listener():
    while True:
        cmd = input()
        if cmd.strip().lower() == "exit":
            print("Dang dong server...")
            server_socket.close()
            sys.exit()

threading.Thread(target=input_listener, daemon=True).start()


def handle_client(conn1, conn2, room_id):
    try:
        conn1.sendall(b"Ban la nguoi choi 1. Cho doi nguoi choi 2...\n")
        conn2.sendall(b"Ban la nguoi choi 2. Tro choi bat dau!\n")
        
        choice1 = conn1.recv(1024).decode()
        print(f"Nguoi choi 1 chon: {choice1}")
        choice2 = conn2.recv(1024).decode()
        print(f"Nguoi choi 2 chon: {choice2}")
        
        result = determine_winner(choice1, choice2)
        
        if result =="Hoa":
            conn1.sendall(f"Ket qua: Hoa! doi phuong cung chon {choice2}".encode())
            conn2.sendall(f"Ket qua: Hoa! doi phuong cung chon {choice1}".encode())
            
        elif result == "P1":
            conn1.sendall(f'Ket qua: Ban thang! Doi phuong chon {choice2}'.encode())
            conn2.sendall(f'Ket qua: Ban thua! Doi phuong chon {choice1}'.encode())
        
        else:
            conn1.sendall(f'Ket qua: Ban thua! Doi phuong chon {choice2}'.encode())
            conn2.sendall(f'Ket qua: Ban thang! Doi phuong chon {choice1}'.encode())
            
    except Exception as e:
        print(f"Loi xay ra: {e}")
        
    finally:
        print(f"Dong ket noi trong phong {room_id}")
        conn1.close()
        conn2.close()
        del rooms[room_id]
        
        
def determine_winner(choice1, choice2):
    # Ham xac dinh nguoi thang cuoc
    if choice1 == choice2:
        return "Hoa"
    rules = {
        "keo": "bao",  # Kéo thắng Bao
        "bao": "bua",  # Bao thắng Búa
        "bua": "keo"   # Búa thắng Kéo
    }
    if rules[choice1] == choice2:
        return "P1"
    return "P2"

room_counter = 0 
while True:
    conn, addr = server_socket.accept()
    print(f'[*] Ket noi tu {addr}')

    clients.append(conn)
    
    if len(clients) >= 2:
        room_counter += 1
        player1 = clients.pop(0)
        player2 = clients.pop(0)
        
        rooms[room_counter] = (player1, player2)
        
        thread = threading.Thread(target=handle_client, args=(player1, player2, room_counter))
        thread.start()
        print(f'[*]Da tao phong {room_counter} voi 2 nguoi choi')
        
