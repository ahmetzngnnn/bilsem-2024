import socket
import time
from dronekit import connect, VehicleMode, mavutil
import math
from gpiozero import Servo
import time

SERVO_PIN = 17  # BCM numarası, örneğin GPIO17
servo = Servo(SERVO_PIN, min_pulse_width=0.0005, max_pulse_width=0.0025) # MG90S için geniş aralık


TCP_IP = "0.0.0.0"
TCP_PORT = 5000

MISSION_PLANNER_IP = "192.168.10.2"
MISSION_PLANNER_PORT = 5762

COOLDOWN = 10  # Saniye yük bırakma tekrar süresi
last_drop_time = 0

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi/2.0)**2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2.0)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def direction_text(dx, dy):
    if abs(dx) > abs(dy):
        return "sağa" if dx > 0 else "sola"
    else:
        return "ileri" if dy > 0 else "geri"

def degree_to_value(degree):
    # 0-180 dereceyi -1.0/+1.0 aralığına çevir
    return (degree / 90.0) - 1.0

def drop_load():
    global last_drop_time
    servo = Servo(SERVO_PIN, min_pulse_width=0.0005, max_pulse_width=0.0025)
    if time.time() - last_drop_time > COOLDOWN:
        print("Ateş merkeze alındı, YÜK BIRAKILIYOR!")
        angle = 30
        value = degree_to_value(angle)
        servo.value = value  # Örneğin 30 dereceye döndür
        time.sleep(1.5)
        servo.detach()  # Servo titremesin
        last_drop_time = time.time()
    else:
        print("Yük bırakma cooldown’da, tekrar bekleniyor.")
def send_ned_velocity(vehicle, vx, vy, vz):
    msg = vehicle.message_factory.set_position_target_local_ned_encode(
        0, 0, 0, mavutil.mavlink.MAV_FRAME_BODY_NED,
        0b0000111111000111, 0, 0, 0, vx, vy, vz, 0, 0, 0, 0, 0
    )
    vehicle.send_mavlink(msg)
    vehicle.flush()

def stable_move(vehicle, dx, dy, threshold=30, max_speed=0.4, min_speed=0.08):
    if abs(dx) <= threshold and abs(dy) <= threshold:
        send_ned_velocity(vehicle, 0, 0, 0)
        print("HEDEF MERKEZDE - HAREKET DURDU")
        return
    scale = lambda err: min(max_speed, max(min_speed, abs(err) * 0.005))
    vx = scale(dy) * (-1 if dy > 0 else 1) if abs(dy) > threshold else 0
    vy = scale(dx) * (1 if dx > 0 else -1) if abs(dx) > threshold else 0
    send_ned_velocity(vehicle, vx, vy, 0)
    print(f"→ Düzeltme komutu: vx={vx:.2f}, vy={vy:.2f} (dx={dx}, dy={dy})")

def print_vehicle_status(vehicle):
    try:
        batt = vehicle.battery
        print(f"Pil: {batt.level if batt.level else '?'}%, Volt: {batt.voltage if batt.voltage else '?'}V")
        print(f"Konum: Lat {vehicle.location.global_relative_frame.lat:.6f}, Lon {vehicle.location.global_relative_frame.lon:.6f}, Alt {vehicle.location.global_relative_frame.alt:.2f}m")
    except Exception as e:
        print("Araç durumu okunamıyor:", e)

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((TCP_IP, TCP_PORT))
    server.listen(1)
    print(f"TCP sunucu başlatıldı {TCP_IP}:{TCP_PORT}, istemci bekleniyor...")
    client, addr = server.accept()
    print('Bağlanan istemci:', addr)

    print(f"Araç bağlantısı kuruluyor → tcp:{MISSION_PLANNER_IP}:{MISSION_PLANNER_PORT}")
    vehicle = connect(f"tcp:{MISSION_PLANNER_IP}:{MISSION_PLANNER_PORT}", wait_ready=True)
    #vehicle = connect('/dev/ttyACM0', wait_ready=True, baud=57600)
    print("Araç bağlantısı tamamlandı.")

    # Kalkış hazırlığı
    target_altitude = 15
    print_vehicle_status(vehicle)
    if not vehicle.is_armable:
        print("Araç arm edilemiyor, hazır hale gelmesi bekleniyor...")
        while not vehicle.is_armable:
            time.sleep(1)
    vehicle.mode = VehicleMode("GUIDED")
    vehicle.armed = True
    while not vehicle.armed:
        print("Arming bekleniyor...")
        time.sleep(1)
    vehicle.simple_takeoff(target_altitude)
    print("Kalkış başlatıldı...")
    while vehicle.location.global_relative_frame.alt < target_altitude * 0.95:
        print(f"Yükseklik: {vehicle.location.global_relative_frame.alt:.2f}m")
        time.sleep(1)
    print("→ Hedef yüksekliğe ulaşıldı.")

    start_location = vehicle.location.global_relative_frame
    last_location = start_location
    total_distance = 0.0

    print("Komutlar bekleniyor...")
    client.settimeout(0.1)

    try:
        while True:
            try:
                data = client.recv(1024).decode().strip()
                if not data:
                    continue
                lines = data.splitlines()
                if not lines:
                    continue
                last_line = lines[-1]
                print("→ Gelen veri:", last_line)
                parts = last_line.split(",")
                if len(parts) < 4:
                    continue
                direction = parts[0]
                dx, dy, locked = int(parts[1]), int(parts[2]), int(parts[3])

                # Konum ve hareket analizi
                current_location = vehicle.location.global_relative_frame
                delta_meter = haversine(
                    last_location.lat, last_location.lon,
                    current_location.lat, current_location.lon
                )
                if delta_meter > 0.08:  # 8 cm üstü hareketlerde yazdır
                    yön = direction_text(dx, dy)
                    print(f"Yaklaşık {delta_meter:.2f} metre {yön} gidildi!")
                    last_location = current_location
                    total_distance += delta_meter

                if direction == "center" and locked == 1:
                    #drop_load(vehicle)
                    print("RTL başlatılıyor...")
                    vehicle.mode = VehicleMode("RTL")
                    while vehicle.armed:
                        print("→ Araç inişte...")
                        time.sleep(2)
                    print("→ Araç disarm oldu. Görev tamamlandı.")
                    break
                else:
                    stable_move(vehicle, dx, dy, threshold=30, max_speed=0.35, min_speed=0.06)

                # Anlık pil durumu, telemetri isteğe bağlı:
                # print_vehicle_status(vehicle)

            except socket.timeout:
                pass
            except Exception as e:
                print("Beklenmedik hata:", e)

    except KeyboardInterrupt:
        print("Kapatılıyor...")

    finally:
        # Toplam rota özeti
        end_location = vehicle.location.global_relative_frame
        straight_dist = haversine(
            start_location.lat, start_location.lon,
            end_location.lat, end_location.lon
        )
        print(f"\nMisyon özeti:")
        print(f"Başlangıç: Lat {start_location.lat:.6f}, Lon {start_location.lon:.6f}")
        print(f"Bitiş:     Lat {end_location.lat:.6f}, Lon {end_location.lon:.6f}")
        print(f"Toplam hareketli yol: {total_distance:.1f} m, Doğrudan mesafe: {straight_dist:.1f} m\n")
        print("Temizlik yapılıyor...")
        vehicle.close()
        client.close()
        server.close()

if __name__ == "__main__":
    main()
