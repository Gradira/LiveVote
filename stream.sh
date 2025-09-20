#!/bin/bash

# Load env vars
set -a
[ -f .env ] && source .env
set +a

# Ensure stream key is present
if [ -z "$YT_STREAM_KEY" ]; then
  echo "Error: YT_STREAM_KEY is not set in .env"
  exit 1
fi

# Export display variable for the virtual display
export DISPLAY=:99

# Start Xvfb virtual display on :99 in background
Xvfb :99 -screen 0 1920x1080x24 -ac &
openbox &

# Run Selenium Python script in background
# python3 stream.py &

echo "Starting FFmpeg to stream your virtual display ${DISPLAY} to YouTube..."
ffmpeg -f x11grab -video_size 1280x720 -i :99 -f alsa -ac 2 -i default -c:v libx264 -preset fast -b:v 2500k -maxrate 2500k -bufsize 5000k -c:a aac -b:a 160k -ar 44100 -g 50 -strict experimental -f flv "rtmp://a.rtmp.youtube.com/live2/${YT_STREAM_KEY}"
