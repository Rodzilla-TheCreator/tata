#!/usr/bin/env python3
"""master_falso_can.py — el Master del EDR, de mentira, en el SH-C30G de maquinon. Para probar el CAN
del rig (rig.ino) en el banco, por la cadena aislada de verdad (ADuM + B0505S + TJA), sin montacargas.

Imita lo grabado del real (herramientas/can/multipiloto.md):
  1. boot-ups del grupo (701, 704, 707, 708, 71E = 00)   → el rig armado contesta 702 00 a los ~0.8 s
  2. lee 0x1000 del nodo 2 (602 40 00 10 00)            → el rig contesta 582 43 00 10 00 00 00 00 00
  3. NMT START a todos (000 01 00) y latido 701 05
  4. SYNC (080) cada 20 ms                              → el rig manda 0x182 detrás de cada SYNC
y muestra el 0x182 decodificado y el latido del nodo 2.

Cableado: CANH↔CANH, CANL↔CANL y GND del SH-C30G a GND_bus (el lado aislado del rig). Interruptor
R120 del SH-C30G ENCENDIDO: con la R3 del TJA nuevo, el bus queda en ~60 Ω (medirlo apagado).

Linux (maquinon). Si el SH-C30G trae firmware candleLight (aparece como can0):
    sudo ip link set can0 up type can bitrate 250000
    python3 master_falso_can.py                       (socketcan, can0)
Si trae slcan (aparece como /dev/ttyACM0):
    python3 master_falso_can.py --slcan /dev/ttyACM0
Windows (i3): si aparece como puerto COM es slcan →  py master_falso_can.py --slcan COM9
Si no aparece COM (candleLight / gs_usb): pip install gs_usb pyusb, driver WinUSB con Zadig, y
    py master_falso_can.py --gsusb
Requiere:  pip install python-can
"""
import argparse
import time

import can

SYNC_S = 0.020


def decodificar_182(d):
    b0, b1, b2, b3, b4, b5, b6, b7 = d
    y = b0 if b4 & 0x08 else (-b0 if b4 & 0x10 else 0)
    x = -b1 if b4 & 0x04 else (b1 if b4 & 0x02 else 0)
    b = b2 if b4 & 0x40 else (-b2 if b4 & 0x20 else 0)
    bot = "".join(n for n, m in (("N", 8), ("S", 4), ("E", 2), ("W", 1)) if b5 & m) or "-"
    return f"y {y:+4d}  x {x:+4d}  palanca {b:+4d}  botones {bot:4s} pito {b4 & 1}  (b3 {b3} b7 {b7})"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slcan", help="puerto serie del SH-C30G si usa slcan (p. ej. /dev/ttyACM0)")
    ap.add_argument("--gsusb", action="store_true", help="SH-C30G con firmware candleLight (gs_usb), Windows")
    ap.add_argument("--canal", default="can0", help="interfaz socketcan (por defecto can0)")
    a = ap.parse_args()
    if a.slcan:
        bus = can.Bus(interface="slcan", channel=a.slcan, bitrate=250000)
    elif a.gsusb:
        bus = can.Bus(interface="gs_usb", channel=0, index=0, bitrate=250000)
    else:
        bus = can.Bus(interface="socketcan", channel=a.canal)

    def tx(i, d):
        bus.send(can.Message(arbitration_id=i, data=bytes(d), is_extended_id=False))

    print("Master falso. Armá el CAN del rig (botón «Armar CAN») y después Enter acá.")
    input()
    for n in (0x701, 0x704, 0x707, 0x708, 0x71E):
        tx(n, [0x00])
    print("boot-ups del grupo enviados; esperando el 702 00 del rig…")
    t0 = time.monotonic()
    fase, ult, t_sync, t_hb, t_imp = "boot", None, 0, 0, 0
    vistos = 0
    while True:
        m = bus.recv(timeout=0.002)
        ahora = time.monotonic()
        if m is not None and not m.is_error_frame:
            i, d = m.arbitration_id, list(m.data)
            if i == 0x702 and d == [0x00] and fase == "boot":
                print(f"  {ahora - t0:5.2f} s  702 00: el rig hizo boot-up. Leo 0x1000…")
                tx(0x602, [0x40, 0x00, 0x10, 0x00, 0, 0, 0, 0]); fase = "sdo"
            elif i == 0x582 and fase == "sdo":
                ok = d[:4] == [0x43, 0x00, 0x10, 0x00]
                print(f"  {ahora - t0:5.2f} s  582 {' '.join(f'{x:02X}' for x in d)}  {'OK' if ok else 'RARO'}. NMT START.")
                tx(0x000, [0x01, 0x00]); fase = "op"
            elif i == 0x702 and fase == "op" and d != [0x05] and ahora - t_imp > 1:
                print(f"  latido del nodo 2 = {d[0]:02X} (05 = operacional)")
            elif i == 0x182:
                vistos += 1
                if d != ult:
                    print(f"  {ahora - t0:6.2f} s  182 {' '.join(f'{x:02X}' for x in d)}   {decodificar_182(d)}")
                    ult = d
            elif 0x080 < i < 0x100:
                print(f"  EMERGENCIA del nodo {i & 0x7F}: {' '.join(f'{x:02X}' for x in d)}")
        if fase == "boot" and ahora - t0 > 5:
            print("  5 s sin 702 00: ¿armaste el CAN del rig? ¿CANH/CANL/GND bien? ¿terminación ~60 Ω?")
            t0 = ahora; tx(0x701, [0x00])
        if fase == "op":
            if ahora - t_sync >= SYNC_S:
                tx(0x080, []); t_sync = ahora
            if ahora - t_hb >= 0.1:
                tx(0x701, [0x05]); t_hb = ahora
            if ahora - t_imp >= 5:
                print(f"  … {vistos} tramas 182 en 5 s (con SYNC cada 20 ms deberían ser ~250)")
                vistos, t_imp = 0, ahora


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
