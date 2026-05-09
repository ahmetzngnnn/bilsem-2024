# bölüm3_ned_velocity_sim.py

def send_ned_velocity_sim(vx, vy, vz):
    """
    Drone olmadan, hız vektörünün doğru hesaplandığını ekrana basar.
    """
    print(f"NED hız vektörü: vx={vx:.2f}, vy={vy:.2f}, vz={vz:.2f}")

def handle_command_sim(direction, dx, dy):
    """
    Yön komutunu alır, uygun hız vektörünü simüle eder.
    """
    velocity = 0.7  # Sabit hız
    if direction == 'left':
        send_ned_velocity_sim(0, -velocity, 0)
    elif direction == 'right':
        send_ned_velocity_sim(0, velocity, 0)
    elif direction == 'forward':
        send_ned_velocity_sim(velocity, 0, 0)
    elif direction == 'backward':
        send_ned_velocity_sim(-velocity, 0, 0)
    elif direction == 'center':
        print("→ Hedef merkezde, hareket yok.")
    else:
        print("→ Bilinmeyen yön:", direction)

# Test:
testler = [
    ("left", 20, 10),
    ("forward", 0, 0),
    ("center", 0, 0),
    ("right", 0, 0),
    ("abc", 5, 5)
]

for komut in testler:
    print("\nKomut:", komut)
    handle_command_sim(*komut)
