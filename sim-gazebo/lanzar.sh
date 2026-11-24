#!/usr/bin/env bash
# TaTa · lanzar.sh — genera el mundo (si falta) y abre Gazebo 3D + la consola. Correrlo DESDE EL ESCRITORIO de la
# máquina (no por ssh), o con DISPLAY=:0 si la sesión gráfica está abierta.
#   ./sim-gazebo/lanzar.sh                 # normal
#   ./sim-gazebo/lanzar.sh ogre            # si la gráfica es vieja o en WSL2 se ve mal
#   ./sim-gazebo/lanzar.sh --liviano       # sin procesar imágenes: el ArUco sale de la geometría (con el ruido medido)
cd "$(dirname "$0")"
MOTOR=ogre2; EXTRA=()
for a in "$@"; do
  case "$a" in
    ogre|ogre2) MOTOR="$a";;
    --liviano) EXTRA+=(--aruco-geometrico);;
  esac
done
# el Python que tiene los bindings de Gazebo (los de apt van al Python del sistema; un venv activo no los ve)
PY=""
for p in /usr/bin/python3 python3 python3.12 python3.10; do
  if command -v "$p" > /dev/null && "$p" -c "import gz.transport13" 2> /dev/null; then PY="$p"; break; fi
done
if [ -z "$PY" ]; then echo "Ningún python3 encuentra gz.transport13: correr primero ./sim-gazebo/instalar.sh"; exit 1; fi
# superspeed es una laptop híbrida (Iris Xe + RTX 4070): que Gazebo dibuje con la NVIDIA, no con la Intel
if command -v nvidia-smi > /dev/null && nvidia-smi > /dev/null 2>&1; then
  export __NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia
fi
"$PY" generar_mundo.py --motor "$MOTOR"
exec "$PY" correr.py "${EXTRA[@]}"
