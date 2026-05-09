# BİLSEM 2024 — Drone Yazılımı Ders İçerikleri

**BİLSEM (Bilim ve Sanat Merkezi) 2024** kapsamında verilen drone yazılımı ve otonom sistemler eğitiminin kaynak kodları, simülasyonları ve 3D tasarım materyalleri.

---

## İçindekiler

```
bilsem/
├── TEMEL TCP Sunucu-İstemci Bağlantısı/   ← Bölüm 1: Temel ağ iletişimi
├── Komut Formatı ve Veri Doğrulama Testi/ ← Bölüm 2: Komut protokolü
├── NED Velocity Simülasyonu (Drone olmadan)/ ← Bölüm 3: Hareket simülasyonu
├── Güvenli Görev Sonu ve Temizlik Simülasyonu/ ← Bölüm 4: Görev sonu
├── Hata Yönetimi/                         ← Bölüm 5: Hata yönetimi
├── BİRLEŞİK MINI SİMÜLASYON/             ← Tüm bölümlerin birleşik testi
├── drone_bilsem/                          ← Gerçek DroneKit görev kodu
└── bilsem/                               ← SolidWorks 3D drone bileşen modelleri
```

---

## Eğitim Bölümleri

### Bölüm 1 — Temel TCP Sunucu-İstemci Bağlantısı

Drone ile yer istasyonu arasındaki iletişimin temeli: TCP soket programlama.

```
TEMEL TCP Sunucu-İstemci Bağlantısı/
├── sunucu.py    → TCP sunucu (port 5002, gelen komutları echo'lar)
└── istemci.py   → TCP istemci (komut gönderir, yanıt okur)
```

```python
# sunucu.py özeti
server.bind(("0.0.0.0", 5002))
data = client.recv(1024).decode()
client.send(f"Alındı: {data}\n".encode())
```

**Öğrenilen kavramlar:** socket, bind, listen, accept, send/recv

---

### Bölüm 2 — Komut Formatı ve Veri Doğrulama Testi

CSV formatında komut protokolü: `direction,dx,dy,locked`

```
Komut Formatı ve Veri Doğrulama Testi/
└── bölüm2_komut_dogrulama.py   → Format doğrulama + parse testi
```

```
Protokol: "direction,dx,dy,locked"
Örnek:    "left,10,0,1"
          "forward,15,3,1"
          "center,0,0,1"   ← Kilitlendi / RTL başlat
          "exit,0,0,0"     ← Bağlantıyı kapat
```

**Öğrenilen kavramlar:** string split, int/float parse, exception handling

---

### Bölüm 3 — NED Velocity Simülasyonu (Drone Olmadan)

MAVLink NED (North-East-Down) hız komutlarının simülasyonu — gerçek drone gerekmez.

```
NED Velocity Simülasyonu (Drone olmadan)/
└── bölüm3_ned_velocity_sim.py   → NED hız vektörü hesaplama simülasyonu
```

```
NED Koordinat Sistemi:
  vx → Kuzey (ileri)
  vy → Doğu (sağa)
  vz → Aşağı (iniş)

Hız ölçekleme:
  scale(err) = min(max_speed, max(min_speed, |err| × 0.005))
```

**Öğrenilen kavramlar:** MAVLink NED frame, hız ölçekleme, eşik algoritması

---

### Bölüm 4 — Güvenli Görev Sonu ve Temizlik Simülasyonu

Görev tamamlandığında bağlantıları güvenli kapatma ve kaynak temizliği.

```
Güvenli Görev Sonu ve Temizlik Simülasyonu/
└── bölüm4_temizlik_sim.py   → try/finally ile kaynak temizliği
```

**Öğrenilen kavramlar:** try/finally, context manager, socket.close(), vehicle.close()

---

### Bölüm 5 — Hata Yönetimi

Gerçek uçuş sırasında oluşabilecek hataları yakalama ve kurtarma.

```
Hata Yönetimi/
└── bölüm5_hata_yonetimi.py   → socket.timeout, exception türleri, graceful shutdown
```

**Öğrenilen kavramlar:** socket.timeout, KeyboardInterrupt, Exception hiyerarşisi

---

### BİRLEŞİK MİNİ SİMÜLASYON — Tüm Bölümlerin Entegrasyonu

Bölüm 1-5'in birleştirildiği çok iş parçacıklı mini simülasyon:

```
BİRLEŞİK MINI SİMÜLASYON/
└── bölüm_tum_testler_birlesik.py   → Threading ile sunucu+istemci eş zamanlı çalışır
```

```python
# Çalışma mimarisi
t1 = threading.Thread(target=server_thread)  # TCP sunucu
t2 = threading.Thread(target=client_thread)  # Test istemcisi
t1.start(); t2.start()
```

**Mesaj akışı:**
```
İstemci ─── "left,10,0,1"    ───► Sunucu → handle_command("left", dx=10, dy=0)
İstemci ─── "forward,15,3,1" ───► Sunucu → handle_command("forward", dx=15, dy=3)
İstemci ─── "center,0,0,1"   ───► Sunucu → Kilitlendi
İstemci ─── "exit,0,0,0"     ───► Sunucu → Bağlantı kapat
```

---

## Drone Görev Kodu — `drone_bilsem/`

Raspberry Pi üzerinde çalışan **gerçek DroneKit** görev kodu. Yer istasyonundan gelen TCP komutlarına göre droneyi yönlendirir ve hedefe kilitlenince yük bırakır.

```
drone_bilsem/
├── drone_mission.py              → Ana görev kodu (DroneKit + TCP + Servo)
└── TFLite_detection_webcam_simple.py → TensorFlow Lite nesne tespiti
```

### `drone_mission.py` — Sistem Mimarisi

```
Yer İstasyonu (TCP :5000)
        │
        │  "direction,dx,dy,locked"
        ▼
RPi (drone_mission.py)
├── TCP sunucu bağlantısı al
├── Mission Planner'a bağlan (tcp:192.168.10.2:5762)
├── GUIDED modu → ARM → Kalkış (15m)
│
└── Ana döngü:
    ├── Komut al → stable_move(vx, vy)  ← NED hız komutu
    ├── "center + locked" → drop_load() → RTL
    └── Haversine ile kat edilen mesafeyi logla
```

### Temel Fonksiyonlar

| Fonksiyon | İşlev |
|-----------|-------|
| `stable_move(vehicle, dx, dy)` | Hata vektörüne göre NED hız komutu hesaplar ve gönderir |
| `send_ned_velocity(vehicle, vx, vy, vz)` | MAVLink SET_POSITION_TARGET_LOCAL_NED mesajı üretir |
| `haversine(lat1, lon1, lat2, lon2)` | İki GPS koordinatı arası metre cinsinden mesafe |
| `drop_load()` | MG90S servo ile yük bırakma (10 sn cooldown) |
| `print_vehicle_status(vehicle)` | Pil seviyesi ve anlık GPS konumu loglar |

### Hız Ölçekleme Algoritması

```python
scale = lambda err: min(max_speed, max(min_speed, abs(err) * 0.005))
# dx=60px → vy = 0.005 × 60 = 0.30 m/s (max 0.35 ile sınırlı)
# dx=10px → vy = 0.005 × 10 = 0.05 m/s (min 0.06 ile yukarı çekilir)
# dx<30px → vy = 0  (eşik altında dur)
```

### `TFLite_detection_webcam_simple.py` — Nesne Tespiti

Raspberry Pi Camera ile gerçek zamanlı TensorFlow Lite nesne tespiti. Tespit edilen nesnenin merkez koordinatını (dx, dy) TCP üzerinden drone görev koduna iletir.

```
Kamera Görüntüsü → TFLite Model → Bounding Box → Merkez (dx,dy) → TCP → drone_mission.py
```

---

## 3D Tasarım Modelleri — `bilsem/`

F450 quadrotor yapımında kullanılan tüm bileşenlerin SolidWorks ve STEP modelleri:

| Bileşen | Model Dosyası | Format |
|---------|--------------|--------|
| **F450 Çerçeve** | `f450-frame-1.snapshot.1/` | SLDASM, SLDPRT |
| **SunnySky X2212 Motor (980KV)** | `sunnysky-x2212-13-980kv-1.snapshot.1/` | SLDASM, SLDPRT |
| **30A ESC** | `exceed-rc-proton-30a-esc-1.snapshot.5/` | SLDPRT |
| **Pixhawk 2.4** | `pixhawk-2-4-1.snapshot.1/` | STEP, STL |
| **Raspberry Pi 4 Model B** | `raspberry-pi-4-model-b-1.snapshot.3/` | SLDASM, STEP |
| **Raspberry Pi AI Kamera** | `raspberry-pi-ai-camera-1.snapshot.1/` | STEP |
| **M8N GPS** | `m8n-gps-1.snapshot.1/` | SLDASM, SLDPRT |
| **SiK Telemetri Radyo V3** | `sik-telemetry-radio-v3-1.snapshot.5/` | SLDASM, STL, STEP |
| **Matek FCHUB-12S PDB** | `matek-12s-pdb-1.snapshot.3/` | IPT, STEP |
| **LiPo Batarya (3S/4S)** | `lipo-battery-4.snapshot.2/` | SLDPRT |
| **FlySky iA6B Alıcı** | `flysky-ia6b-receiver-1.snapshot.2/` | SLDPRT |
| **MG90S Servo** | `tower-pro-mg90s-micro-servo-2.snapshot.3/` | STEP, STL |
| **10" Pervane (CW/CCW)** | `10-inch-cw-ccw-propeller-set-1.snapshot.6/` | STEP |
| **Yük Bırakma Mekanizması** | `payload-dropping-mechanism-1.snapshot.1/` | SLDASM, STEP, STL |
| **İniş Takımı** | `f450-f550-quadcopter-high-landing-gear-1.snapshot.2/` | STEP |
| **Anti-Vibrasyon Platform** | `anti-vibration-platform-for-pixhawk-and-apm-1.snapshot.2/` | STP |

---

## Teknoloji Yığını

| Katman | Teknoloji |
|--------|-----------|
| **Drone Yazılımı** | Python 3.11, DroneKit, pymavlink |
| **Görüntü İşleme** | TensorFlow Lite, OpenCV |
| **İletişim** | TCP Socket (JSON/CSV), MAVLink |
| **Donanım** | Raspberry Pi 4B, Pixhawk 2.4, MG90S Servo |
| **GPIO** | gpiozero (servo kontrolü) |
| **3D Tasarım** | SolidWorks (.SLDPRT, .SLDASM), STEP, STL |

---

## Kurulum

```bash
# Python bağımlılıkları
pip install dronekit pymavlink gpiozero

# TFLite için (Raspberry Pi)
pip install tflite-runtime opencv-python

# Simülasyon testleri (drone gerekmez)
python "BİRLEŞİK MINI SİMÜLASYON/bölüm_tum_testler_birlesik.py"
```

---

## Bölüm Akışı

```
Bölüm 1: TCP Temelleri
    ↓
Bölüm 2: Komut Protokolü (direction,dx,dy,locked)
    ↓
Bölüm 3: NED Hız Simülasyonu
    ↓
Bölüm 4: Güvenli Görev Sonu
    ↓
Bölüm 5: Hata Yönetimi
    ↓
BİRLEŞİK SİMÜLASYON: Tümünü threading ile test et
    ↓
drone_bilsem: Gerçek DroneKit ile uçuş + TFLite hedef tespiti
```
