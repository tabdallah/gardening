#!/bin/bash

echo "Starting webcam"
#mjpg_streamer -i "/usr/lib/input_uvc.so -y" -o "/usr/lib/output_http.so -w ./www"
mjpg_streamer -b -i "input_raspicam.so -rot 180" -o "output_http.so -w /usr/gardening/web_interface"
