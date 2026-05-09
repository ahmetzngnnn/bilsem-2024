# istemci.py
import socket

TCP_IP = "127.0.0.1"
TCP_PORT = 5002

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((TCP_IP, TCP_PORT))

while True:
    msg = input("Komut gir (exit çıkış): ")
    client.send(msg.encode())
    if msg == "exit":
        break
    data = client.recv(1024).decode()
    print("Sunucudan cevap:", data)

client.close()
