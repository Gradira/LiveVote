# Start Xvfb
Xvfb :99 -screen 0 1920x1080x24 &

# Set DISPLAY
export DISPLAY=:99

# Start Openbox
openbox &

# Set background image with feh
feh --bg-scale /home/christoph/Downloads/utonish/gradira/banner1920p.png
