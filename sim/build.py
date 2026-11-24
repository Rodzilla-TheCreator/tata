"""Mete sim/sim_datos.json en sim/sim_tpl.html y escribe sim/simulacion.html (un solo archivo).
`python sim/build.py v3b` hace lo mismo con sim_datos_v3b.json → simulacion_v3b.html (la del 09-nov)."""
import os
import sys

SUF = '_v3b' if 'v3b' in sys.argv[1:] else ''

AQUI = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(AQUI, 'sim_tpl.html'), encoding='utf-8') as f:
    tpl = f.read()
with open(os.path.join(AQUI, f'sim_datos{SUF}.json'), encoding='utf-8') as f:
    datos = f.read()
assert '/*DATOS*/null' in tpl
with open(os.path.join(AQUI, f'simulacion{SUF}.html'), 'w', encoding='utf-8') as f:
    f.write(tpl.replace('/*DATOS*/null', datos))
print(f'sim/simulacion{SUF}.html ({(len(tpl) + len(datos)) / 1024:.0f} KB)')
