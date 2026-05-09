# 🚁🔥 Akıllı İnsansız Hava Aracı ile Otonom Yangın Tespit ve Müdahale Sistemi

## Proje Özeti

Bu sistem; bir **drone** ve bir **yer istasyonu** ile çalışır. Drone, belirlenen bir alanı otonom olarak tarar, herhangi bir “ateş/yangın” tespit ettiğinde görüntü işleme tarafından gerçek zamanlı komut alır ve **hedefe kilitlenerek su bırakır**. Ardından eve (RTL) döner. Tüm sistem tamamen entegre, adaptif ve gerçek zamanlıdır.

---

## Sistem Bileşenleri

1. **Drone Kontrol Scripti** (`drone_mission.py` veya benzeri)

   * Drone’a otonom alan tarama, hücre bazlı görev oluşturma, yangın anında acil müdahale ve manuel modlara geçiş yeteneği kazandırır.
   * TCP/IP üzerinden dışarıdan gelen görüntü işleme komutlarını daima dinler.

2. **Görüntü İşleme ve Yangın Tespit Scripti** (`TFLite_detection_webcam_simple.py`)

   * TFLite modeli ile “fire” (ateş) tespiti yapar.
   * CSRT + Kalman ile yüksek kararlılıkla hedefi takip eder, AI ile periyodik kutu günceller.
   * TCP/IP ile drone scriptine yön, dx/dy ve kilit bilgisi gönderir.
   * **HSV uzayı ve benzerlik oranı** ile kilit tutarlılığını adaptif olarak yönetir.

---

## Klasör/Script Yapısı

```
/
├── drone_mission.py           # Drone otonom görev & TCP dinleyici scripti
├── TFLite_detection_webcam_simple.py  # Görüntü işleme ve yangın tespit scripti
├── Fire_detection_model/
│   ├── detect.tflite
│   └── labelmap.txt
├── requirements.txt
└── README.md
```

---

## Kurulum & Gereksinimler

### Donanım

* Raspberry Pi veya Jetson (görüntü işleme için)
* Pixhawk veya benzeri uçuş kontrolcü (drone)
* Kamera (USB veya CSI)
* Telemetri bağlantısı

### Yazılım

* Python 3.7+
* OpenCV 4.x
* numpy
* dronekit
* pymavlink
* Tensorflow Lite veya tflite\_runtime
* (isteğe bağlı) EdgeTPU desteği

### Kurulum

```bash
sudo apt-get update
sudo apt-get install python3-pip python3-opencv
pip3 install numpy dronekit pymavlink tflite-runtime
# veya: pip3 install tensorflow opencv-python
```

---

## Kullanım

### 1. **Drone Scriptini Başlat**

Drone’u bağlayıp arayüzde uçuşa hazır hale getirin.

```bash
python3 drone_mission.py
```

> İlk kalkış ve grid planı otomatik yapılır, alan taranır. Yangın tespit komutu alınca otomatik müdahale ve su bırakma işlemi başlatılır.

---

### 2. **Görüntü İşleme Scriptini Başlat**

Kendi model klasörünüzü ve ağırlıkları belirtin:

```bash
python3 TFLite_detection_webcam_simple.py --modeldir Fire_detection_model --graph detect.tflite --labels labelmap.txt
```

> Sadece “fire” etiketi olan nesneleri tespit eder ve merkeze kilitlenince drone’a yön, delta ve kilit komutları yollar.

---

## Özellikler

* **Otonom Alan Taraması:** 4 köşe GPS koordinatına göre alanı grid’e böler, otomatik olarak gezilir.
* **Gerçek Zamanlı Komut Dinleme:** Görüntü işleme scriptinden gelen yön komutları anında işlenir, gerekirse tarama iptal edilir.
* **Yüksek Güvenilirlikte Takip:** CSRT + Kalman + Adaptif HSV ile asla kilit kaybı yaşanmaz; sistem çevresel değişimlere dayanıklıdır.
* **Dinamik HSV Threshold:** Son AI tespitlerine göre benzerlik toleransı otomatik ayarlanır.
* **RTL (Return To Launch):** Görev veya müdahale sonrası drone otomatik olarak eve döner.
* **Su Bırakma:** Servo/kanal komutu ile tetiklenir.

---

## **Parametreler & Ayarlar**

* `corners`: Görev alanı dört köşe koordinatları
* `CELL_SIZE`: Hücre boyutu (metre)
* `ALTITUDE`: Uçuş yüksekliği (metre)
* `TCP_PORT`: Komut dinleme portu
* Görüntü işleme argümanları için `--modeldir`, `--threshold`, `--fps` vs. ayarlanabilir.

---

## **Hata Ayıklama ve Güvenlik**

* Komutlar anında terminalde gösterilir.
* HSV ve benzerlik oranı ekranda overlay olarak kutunun üstünde gözükür.
* Her iki script de bağlantı koparsa/kapatılırsa güvenli şekilde sonlandırılır.

---

## **Örnek Çalışma Akışı**

1. Drone ve görüntü işleme scriptleri başlatılır.
2. Drone otomatik olarak grid görevine başlar.
3. Görüntü işleme, “fire” tespit ettiğinde drone’u merkeze kilitleyecek komutlar yollar.
4. Drone görevini bırakıp ateşe yönelir, kilitlenince su bırakır.
5. Görev biter, drone otomatik olarak eve döner (RTL).

---

## Sık Sorulan Sorular

* **Farklı model veya kamera kullanabilir miyim?** Evet, model ve çözünürlük parametrelerini değiştirerek kullanabilirsin.

* **Başka nesne tespiti yapabilir miyim?** Hayır, bu sistem sadece “fire” etiketi ile çalışmak üzere optimize edilmiştir.

* **Hangi portlar ve ağ yapısı ile çalışıyor?** TCP/IP ile iki script birbirine bağlanır. Drone scripti sunucu, görüntü işleme istemci olarak bağlanır.

---


---

Hazırlayan:
**AHMET ZENGİN**
*2025*
