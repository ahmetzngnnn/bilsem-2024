# bölüm_tum_testler_birlesik.py
import socket
import threading
import time

def handle_command(direction, dx, dy):
    print(f"Komut işlendi: {direction}, dx={dx}, dy={dy}")

def server_thread():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', 5002))
    server.listen(1)
    print("Sunucu hazır, bekliyor...")
    client, addr = server.accept()
    print("Client bağlandı:", addr)
    while True:
        data = client.recv(1024).decode().strip()
        if not data:
            continue
        print("Gelen veri:", data)
        try:
            direction, dx, dy, locked = data.split(",")
            handle_command(direction, int(dx), int(dy))
        except Exception as e:
            print("Veri hatası:", e)
        if data == "exit,0,0,0":
            break
    client.close()
    server.close()
    print("Sunucu kapandı.")

def client_thread():
    time.sleep(1)  # Sunucu açılmadan bağlanmasın
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('127.0.0.1', 5002))
    for msg in ["left,10,0,1", "forward,15,3,1", "center,0,0,1", "exit,0,0,0"]:
        print("Komut gönderiliyor:", msg)
        client.send(msg.encode())
        time.sleep(0.5)
    client.close()

if __name__ == "__main__":
    t1 = threading.Thread(target=server_thread)
    t2 = threading.Thread(target=client_thread)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
