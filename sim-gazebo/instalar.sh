#!/usr/bin/env bash
# TaTa · instalar.sh — Gazebo Harmonic + lo de Python para sim-gazebo/ (Ubuntu 22.04 o 24.04; superspeed es 22.04).
# Probado el 24-nov-2026 en Ubuntu 24.04 (contenedor, sin pantalla). No toca ROS: Harmonic convive con Fortress.
set -e
sudo apt-get update
sudo apt-get install -y curl lsb-release gnupg python3-pip python3-tk
sudo curl -sSL https://packages.osrfoundation.org/gazebo.gpg -o /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] https://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" \
  | sudo tee /etc/apt/sources.list.d/gazebo-stable.list > /dev/null
sudo apt-get update
sudo apt-get install -y gz-harmonic python3-gz-transport13 python3-gz-msgs10
# OpenCV con ArUco (contrib) para el Python del sistema (el que trae los bindings de gz)
# el Python que tiene los bindings de Gazebo (los de apt van al Python del sistema; un venv activo no los ve)
PY=""
for p in /usr/bin/python3 python3 python3.12 python3.10; do
  if command -v "$p" > /dev/null && "$p" -c "import gz.transport13" 2> /dev/null; then PY="$p"; break; fi
done
if [ -z "$PY" ]; then echo "gz.transport13 no aparece en ningún python3"; exit 1; fi
echo "Python con Gazebo: $PY"
if "$PY" -m pip install --help | grep -q break-system-packages; then EXTRA=--break-system-packages; else EXTRA=; fi
"$PY" -m pip install --user $EXTRA "opencv-contrib-python-headless<4.11" "numpy<2"
"$PY" -c "from gz.transport13 import Node; import cv2; assert hasattr(cv2.aruco, 'ArucoDetector'); print('listo: gz-transport13 y OpenCV', cv2.__version__)"
gz sim --versions
