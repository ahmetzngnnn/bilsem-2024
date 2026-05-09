# bölüm4_temizlik_sim.py

class DummyVehicle:
    def __init__(self):
        self.armed = True
        self.mode = "GUIDED"
    def close(self):
        print("Araç bağlantısı KAPANDI.")

class DummyConn:
    def close(self):
        print("Socket bağlantısı KAPANDI.")

def safe_shutdown(vehicle, client, server):
    print("Görev tamamlandı, araç eve dönüyor ve iniş başlıyor...")
    vehicle.mode = "RTL"
    # Simülasyon için hemen iniş ve disarm
    while vehicle.armed:
        print("→ Araç inişte...")
        vehicle.armed = False  # Simülasyonda beklemeden bitiriyoruz
    print("→ Araç disarm oldu. Görev tamamlandı.")
    print("TEMİZLİK başlatılıyor...")
    vehicle.close()
    client.close()
    server.close()

# Test:
safe_shutdown(DummyVehicle(), DummyConn(), DummyConn())
