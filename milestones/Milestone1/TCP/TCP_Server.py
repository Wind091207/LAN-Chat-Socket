import socket

HOST = '127.0.0.1'
PORT = 65431

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen(1)

while True:
    conn, addr = s.accept()
    try:
        print("Connected by: ", addr)
        while True:
            data = conn.recv(1024)
            
            if data == "b''":
                break
            
            data_str = data.decode("utf8")
            
            if data_str == "quit":
                break
            
            print(f"Client: {data_str}")
            conn.sendall(bytes(data_str, "utf8"))
    finally:
        conn.close()
s.close()
            
            