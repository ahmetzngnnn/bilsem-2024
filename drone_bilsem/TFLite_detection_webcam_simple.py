import os
import argparse
import cv2
import numpy as np
import time
import socket
from threading import Thread
import importlib.util



def calc_hsv_hist(frame, bbox):
    x, y, w, h = [int(v) for v in bbox]
    x, y = max(0, x), max(0, y)
    w = max(1, min(frame.shape[1] - x, w))
    h = max(1, min(frame.shape[0] - y, h))
    roi = frame[y:y+h, x:x+w]
    hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    hist = cv2.calcHist([hsv_roi], [0, 1, 2], None, [8, 8, 8], [0, 180, 0, 256, 0, 256])
    cv2.normalize(hist, hist)
    return hist

def smooth_bbox(prev_bbox, new_bbox, alpha=0.5):
    if prev_bbox is None:
        return new_bbox
    px, py, pw, ph = prev_bbox
    nx, ny, nw, nh = new_bbox
    sx = int(px * (1 - alpha) + nx * alpha)
    sy = int(py * (1 - alpha) + ny * alpha)
    sw = int(pw * (1 - alpha) + nw * alpha)
    sh = int(ph * (1 - alpha) + nh * alpha)
    return (sx, sy, sw, sh)

class SimpleKalmanBox:
    def __init__(self, bbox):
        x, y, w, h = bbox
        self.dt = 1.
        self.state = np.array([x, y, w, h, 0, 0, 0, 0], dtype=np.float32)
        self.P = np.eye(8) * 100.
        self.F = np.eye(8)
        for i in range(4):
            self.F[i, i+4] = self.dt
        self.Q = np.eye(8) * 0.01
        self.H = np.eye(4,8)
        self.R = np.eye(4) * 20.

    def update(self, bbox=None):
        self.state = self.F @ self.state
        self.P = self.F @ self.P @ self.F.T + self.Q
        if bbox is not None:
            z = np.array(bbox[:4], dtype=np.float32)
            y = z - self.H @ self.state
            S = self.H @ self.P @ self.H.T + self.R
            K = self.P @ self.H.T @ np.linalg.inv(S)
            self.state = self.state + K @ y
            self.P = (np.eye(8) - K @ self.H) @ self.P
        return self.get_bbox()

    def get_bbox(self):
        x, y, w, h = self.state[:4]
        return (int(x), int(y), int(w), int(h))

class VideoStream:
    def __init__(self, src=1, resolution=(1280, 720), framerate=25):
        if isinstance(src, int):
            self.stream = cv2.VideoCapture(src, cv2.CAP_V4L2)
            self.stream.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
            self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
            self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])
            self.stream.set(cv2.CAP_PROP_FPS, framerate)
            self.stream.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
            self.stream.set(cv2.CAP_PROP_EXPOSURE, -6)
        else:
            self.stream = cv2.VideoCapture(src)
        (self.grabbed, self.frame) = self.stream.read()
        if not self.grabbed or self.frame is None:
            print("Kamera/video açılamadı!")
            exit()
        self.stopped = False

    def start(self):
        Thread(target=self.update, args=(), daemon=True).start()
        return self

    def update(self):
        while True:
            if self.stopped:
                self.stream.release()
                return
            (self.grabbed, self.frame) = self.stream.read()
            if not self.grabbed:
                self.stopped = True
                return

    def read(self):
        return self.frame

    def stop(self):
        self.stopped = True

# ---------- TCP KOMUTU ----------
SERVER_IP = "127.0.0.1"
SERVER_PORT = 5000
tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
while True:
    try:
        tcp_sock.connect((SERVER_IP, SERVER_PORT))
        print("TCP bağlantısı kuruldu.")
        break
    except Exception as e:
        print("Bağlanılamadı:", e)
        time.sleep(1)

# ---------- ARGPARSE ----------
parser = argparse.ArgumentParser()
parser.add_argument('--input', default='0', help='0 for camera or video file path')
parser.add_argument('--modeldir', required=True)
parser.add_argument('--graph', default='detect.tflite')
parser.add_argument('--labels', default='labelmap.txt')
parser.add_argument('--threshold', default=0.8)
parser.add_argument('--resolution', default='1280x720')
parser.add_argument('--fps', default=25, type=int)
parser.add_argument('--edgetpu', action='store_true')
args = parser.parse_args()

try:
    cam_index = int(args.input)
    input_src = cam_index
except ValueError:
    input_src = args.input


MODEL_NAME = args.modeldir
GRAPH_NAME = args.graph
LABELMAP_NAME = args.labels
min_conf_threshold = float(args.threshold)
resW, resH = args.resolution.split('x')
imW, imH = int(resW), int(resH)
fps = args.fps
use_TPU = args.edgetpu

pkg = importlib.util.find_spec('tflite_runtime')
if pkg:
    from tflite_runtime.interpreter import Interpreter
    if use_TPU:
        from tflite_runtime.interpreter import load_delegate
else:
    from tensorflow.lite.python.interpreter import Interpreter
    if use_TPU:
        from tensorflow.lite.python.interpreter import load_delegate

if use_TPU and (GRAPH_NAME == 'detect.tflite'):
    GRAPH_NAME = 'edgetpu.tflite'

CWD_PATH = os.getcwd()
PATH_TO_CKPT = os.path.join(CWD_PATH, MODEL_NAME, GRAPH_NAME)
PATH_TO_LABELS = os.path.join(CWD_PATH, MODEL_NAME, LABELMAP_NAME)

with open(PATH_TO_LABELS, 'r') as f:
    labels = [line.strip() for line in f.readlines()]
if labels[0] == '???':
    del(labels[0])

if use_TPU:
    interpreter = Interpreter(model_path=PATH_TO_CKPT, experimental_delegates=[load_delegate('libedgetpu.so.1.0')])
else:
    interpreter = Interpreter(model_path=PATH_TO_CKPT)
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()
height = input_details[0]['shape'][1]
width = input_details[0]['shape'][2]
floating_model = (input_details[0]['dtype'] == np.float32)
input_mean = 127.5
input_std = 127.5

frame_rate_calc = 1
freq = cv2.getTickFrequency()
videostream = VideoStream(src=input_src, resolution=(imW, imH), framerate=fps).start()
time.sleep(1)

lock_mode = False
lock_bbox = None
tracker_csrt = None
hsv_hist_locked = None
kalman = None
kalman_active = False
kalman_lost_frames = 0
MAX_KALMAN_FRAMES = 8

# --- Adaptif HSV eşik için ---
recent_similarities = []
MAX_RECENT = 10
HSV_SIMILARITY_THRESH = 0.28  # Başlangıç için makul bir değer

SEND_INTERVAL = 0.18
last_send_time = 0
AI_REFRESH_INTERVAL = 3.0
last_ai_refresh = time.time()
last_similarity = 0.0

while True:
    t1 = cv2.getTickCount()
    frame1 = videostream.read()
    if frame1 is None:
        print("Kamera/video akışı kayboldu! Çıkılıyor.")
        break
    frame = frame1.copy()

    now_time = time.time()
    run_ai = False
    # AI 3 saniyede bir çalışsın!
    if not lock_mode or now_time - last_ai_refresh > AI_REFRESH_INTERVAL:
        run_ai = True
        last_ai_refresh = now_time

    direction, dx, dy, locked_bit = "none", 0, 0, 0

    if run_ai or lock_bbox is None:
        # AI ile fire kutusu bul
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_resized = cv2.resize(frame_rgb, (width, height))
        input_data = np.expand_dims(frame_resized, axis=0)
        if floating_model:
            input_data = (np.float32(input_data) - input_mean) / input_std
        interpreter.set_tensor(input_details[0]['index'], input_data)
        interpreter.invoke()
        boxes = interpreter.get_tensor(output_details[0]['index'])[0]
        classes = interpreter.get_tensor(output_details[1]['index'])[0]
        scores = interpreter.get_tensor(output_details[2]['index'])[0]
        found_fire = False
        for i in range(len(scores)):
            if ((scores[i] > min_conf_threshold) and (scores[i] <= 1.0)):
                object_name = labels[int(classes[i])]
                if object_name.lower() != "fire":
                    continue
                ymin = int(max(0, (boxes[i][0] * imH)))
                xmin = int(max(0, (boxes[i][1] * imW)))
                ymax = int(min(imH, (boxes[i][2] * imH)))
                xmax = int(min(imW, (boxes[i][3] * imW)))
                w = xmax - xmin
                h = ymax - ymin
                if w <= 5 or h <= 5 or xmin < 0 or ymin < 0 or xmax > imW or ymax > imH:
                    continue
                new_bbox = (xmin, ymin, w, h)
                lock_bbox = smooth_bbox(lock_bbox, new_bbox, alpha=0.7) if lock_bbox is not None else new_bbox
                tracker_csrt = cv2.TrackerCSRT_create()
                tracker_csrt.init(frame, lock_bbox)
                kalman = SimpleKalmanBox(lock_bbox)
                kalman_active = False
                kalman_lost_frames = 0
                hsv_hist_locked = calc_hsv_hist(frame, lock_bbox)
                last_similarity = 1.0

                # --- Adaptif HSV threshold güncelle (daha esnek!)
                recent_similarities.append(1.0)
                if len(recent_similarities) > MAX_RECENT:
                    recent_similarities.pop(0)
                HSV_SIMILARITY_THRESH = min(recent_similarities) - 0.12
                HSV_SIMILARITY_THRESH = max(0.13, HSV_SIMILARITY_THRESH)
                print(f"[Adaptive Threshold] HSV benzerlik toleransı: {HSV_SIMILARITY_THRESH:.2f}")
                lock_mode = True
                found_fire = True
                print("AI ile takip kutusu güncellendi.")
                break

    elif lock_mode and tracker_csrt is not None:
        ok_csrt, bbox_csrt = tracker_csrt.update(frame)
        if ok_csrt:
            bbox = smooth_bbox(lock_bbox, bbox_csrt, alpha=0.5)
            lock_bbox = bbox
            hist_now = calc_hsv_hist(frame, lock_bbox)
            similarity = cv2.compareHist(hsv_hist_locked, hist_now, cv2.HISTCMP_CORREL)
            last_similarity = similarity
            # HSV toleransına göre kilit kır
            if similarity > HSV_SIMILARITY_THRESH:
                if kalman is not None:
                    kalman.update(lock_bbox)
                kalman_active = False
                kalman_lost_frames = 0
            else:
                print(f"Renk uzayı değişti (sim={similarity:.2f}, thresh={HSV_SIMILARITY_THRESH:.2f}) → Kilit kırıldı, AI aramasına geçiliyor.")
                lock_mode = False
                lock_bbox = None
                tracker_csrt = None
                kalman = None
                hsv_hist_locked = None
                kalman_active = False
                kalman_lost_frames = 0
        else:
            if kalman is not None and kalman_lost_frames < MAX_KALMAN_FRAMES:
                lock_bbox = kalman.update()
                kalman_active = True
                kalman_lost_frames += 1
                print(f"CSRT kutuyu kaybetti, Kalman tahmini ile devam ({kalman_lost_frames}).")
            else:
                print("Takip kayboldu, kilit sıfırlandı, AI aramasına geçiliyor.")
                lock_mode = False
                lock_bbox = None
                tracker_csrt = None
                kalman = None
                hsv_hist_locked = None
                kalman_active = False
                kalman_lost_frames = 0

    # --- Çizim ve TCP gönderim ---
    if lock_bbox is not None:
        p1 = (int(lock_bbox[0]), int(lock_bbox[1]))
        p2 = (int(lock_bbox[0]+lock_bbox[2]), int(lock_bbox[1]+lock_bbox[3]))
        cv2.rectangle(frame, p1, p2, (0, 0, 255), 2)
        center_x, center_y = imW // 2, imH // 2
        bbox_cx = int(lock_bbox[0] + lock_bbox[2] // 2)
        bbox_cy = int(lock_bbox[1] + lock_bbox[3] // 2)
        cv2.line(frame, (center_x, center_y), (bbox_cx, bbox_cy), (0,255,0), 2)
        dx, dy = bbox_cx - center_x, bbox_cy - center_y

        tolerance = 30
        direction = "center"
        if abs(dx) > tolerance or abs(dy) > tolerance:
            if abs(dx) > abs(dy):
                direction = "right" if dx > 0 else "left"
            else:
                direction = "forward" if dy > 0 else "backward"
        locked_bit = 1

        # Benzerlik oranı ve threshold kutunun üstünde yazsın
        sim_text = f"sim: {last_similarity:.2f} (thr: {HSV_SIMILARITY_THRESH:.2f})"
        cv2.putText(frame, sim_text, (p1[0], max(p1[1] - 10, 20)), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,255), 2)

        if time.time() - last_send_time > SEND_INTERVAL:
            msg = f"{direction},{dx},{dy},{locked_bit}\n"
            try:
                tcp_sock.sendall(msg.encode())
                print("Komut gönderildi:", msg.strip())
            except Exception as e:
                print("TCP Hata:", e)
            last_send_time = time.time()

    t2 = cv2.getTickCount()
    time1 = (t2 - t1) / freq
    frame_rate_calc = 1 / time1
    cv2.putText(frame, f'FPS: {frame_rate_calc:.2f} {"KALMAN" if kalman_active else "CSRT"}', (30, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2, cv2.LINE_AA)
    cv2.imshow('Object detector', frame)

    key = cv2.waitKey(1)
    if key == ord('q'):
        break
    if key == ord('r'):
        print("Manuel olarak kilit açıldı, tekrar AI'ya geçildi.")
        lock_mode = False
        lock_bbox = None
        tracker_csrt = None
        kalman = None
        hsv_hist_locked = None
        kalman_active = False
        kalman_lost_frames = 0

cv2.destroyAllWindows()
videostream.stop()
tcp_sock.close()
