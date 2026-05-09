# sunucu.py
import socket

TCP_IP = "0.0.0.0"
TCP_PORT = 5002

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((TCP_IP, TCP_PORT))
server.listen(1)
print(f"Sunucu başlatıldı. {TCP_PORT} portunda bekliyor...")

client, addr = server.accept()
print("Bağlantı alındı:", addr)

while True:
    data = client.recv(1024).decode().strip()
    if not data:
        continue
    print("Gelen veri:", data)
    if data == "exit":
        print("Çıkılıyor...")
        break
    client.send(f"Alındı: {data}\n".encode())

client.close()
server.close()
