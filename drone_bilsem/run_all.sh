#!/bin/bash
cd /home/raspberrypi/drone_bilsem
python3 drone_mission.py &
sleep 6
python3 TFLite_detection_webcam_simple.py --modeldir Fire_detection_model --graph detect.tflite --labels labelmap.txt

