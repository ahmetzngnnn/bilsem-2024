# bölüm2_komut_dogrulama.py

def komut_coz(data):
    """
    Komutu parçalar ve kontrol eder. Hatalı/eksikse uyarı verir.
    """
    lines = data.strip().splitlines()
    if not lines:
        print("Veri yok!")
        return
    last_line = lines[-1]
    print("İşlenen komut satırı:", last_line)
    parts = last_line.split(",")
    if len(parts) < 4:
        print("Eksik veya hatalı format!")
        return
    direction = parts[0]
    try:
        dx = int(parts[1])
        dy = int(parts[2])
        locked = int(parts[3])
    except:
        print("Tip hatası! int bekleniyordu.")
        return
    print(f"Yön: {direction}, dx: {dx}, dy: {dy}, kilit: {locked}")

# Testler:
test_komutlar = [
    "right,20,-15,1\n",
    "center,0,0,1",
    "sol,abc,5,0",  # Tip hatası
    "forward,10",   # Eksik veri
    ""              # Hiç veri yok
]

for cmd in test_komutlar:
    print("\n--- Yeni Komut ---")
    komut_coz(cmd)
