#!/bin/bash

echo "Starting webcam"
#mjpg_streamer -b -i "input_raspicam.so -rot 180" -o "output_http.so -w /usr/gardening/web_interface"
mjpg_streamer -b -i "input_uvc.so -r 1280x720 -d /dev/video0 -f 30 -q 80" -o "output_http.so -w /usr/gardening/web_interface"
echo "Stopped webcam"

