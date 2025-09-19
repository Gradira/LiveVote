#!/bin/bash

# Export display variable for the virtual display
export DISPLAY=:99

# Start Xvfb virtual display on :99 in background
Xvfb :99 -screen 0 1920x1080x24 -ac &
openbox &

# Run Selenium Python script in background
# python3 stream.py &

# Replace YOUR_STREAM_KEY with your actual YouTube stream key before running
echo "Starting FFmpeg to stream your virtual display ${DISPLAY} to YouTube..."
ffmpeg -re -i output.mp4 \
  -c:v libx264 -preset veryfast -b:v 4500k -maxrate 5000k -bufsize 9000k \
  -c:a aac -b:a 128k \
    -f flv rtmp://a.rtmp.youtube.com/live2/8eec-6825-fvdw-7q7w-80ta
