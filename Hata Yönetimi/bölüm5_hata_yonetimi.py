# bölüm5_hata_yonetimi.py

def process_command(data):
    """
    Gelen veriyi işler, hatalıysa uyarı verir, program asla çökmez.
    """
    try:
        parts = data.strip().split(",")
        if len(parts) < 4:
            print("Format hatası! Atlanıyor.")
            return
        direction = parts[0]
        dx = int(parts[1])
        dy = int(parts[2])
        locked = int(parts[3])
        print(f"OK: {direction},{dx},{dy},{locked}")
    except Exception as e:
        print("Veri işleme hatası:", e)

# Test:
test_komutlar = [
    "left,30,10,1",
    "right,abc,10,1",
    "center,0,0",
    "",
    "forward,12,3,1"
]

for cmd in test_komutlar:
    print("\nGelen komut:", repr(cmd))
    process_command(cmd)
