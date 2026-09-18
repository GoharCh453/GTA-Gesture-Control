$ErrorActionPreference = "Stop"

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
# MediaPipe 0.10.11 declares opencv-contrib-python, which conflicts with the
# camera-tested GUI wheel. The runtime only needs the solutions API here.
python -m pip install --no-deps mediapipe==0.10.11

python -c "import cv2, mediapipe as mp; print('OpenCV:', cv2.__version__); print('MediaPipe:', mp.__version__); print('DirectShow:', hasattr(cv2, 'CAP_DSHOW'))"
Write-Host "Setup complete. Run: python control.py"
