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

# Check if music.mp3 exists
if [ ! -f music.mp3 ]; then
  echo "Error: music.mp3 not found! Please provide background music file named 'music.mp3'."
  exit 1
fi

# Export display variable for the virtual display
export DISPLAY=:99

# Start Xvfb virtual display on :99 in background
Xvfb :99 -screen 0 1920x1080x24 -ac &
if [ ! -f music.mp3 ]; then
  echo "Error: music.mp3 not found! Please provide background music file named 'music.mp3'."
  exit 1
fi

openbox &
# xsetroot -cursor transparent_cursor.xbm transparent_cursor.xbm

if [ -f banner.png ]; then
  echo "Background banner found. Setting as fallback."
  feh --bg-scale banner.png
fi

# Run Selenium Python script in background
# python3 stream.py &

echo "Starting FFmpeg to stream your virtual display ${DISPLAY} to YouTube..."
xdotool mousemove 1920 1080

# Infinite loop to restart stream if it stops (e.g. broken pipe)
while true; do
  # Run FFmpeg with video from virtual display and audio from mixed sources
  ffmpeg \
    -f x11grab -video_size 1920x1080 -framerate 60 -i :99 \
    -f alsa -ac 2 -i default \
    -stream_loop -1 -i music.mp3 \
    -filter_complex "[2]adelay=4000|4000[aud];[1][aud]amix=inputs=2:duration=longest:dropout_transition=2[aout]" \
    -map 0:v -map "[aout]" \
    -c:v libx264 -preset fast -b:v 2500k -maxrate 2500k -bufsize 5000k \
    -c:a aac -b:a 160k -ar 44100 -g 50 -strict experimental \
    -f flv "rtmp://a.rtmp.youtube.com/live2/${YT_STREAM_KEY}"

  echo "FFmpeg exited, restarting stream in 1 seconds..."
  sleep 1
done