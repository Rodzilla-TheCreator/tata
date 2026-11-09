"""Mete sim/sim_datos.json en sim/sim_tpl.html y escribe sim/simulacion.html (un solo archivo)."""
import os

AQUI = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(AQUI, 'sim_tpl.html'), encoding='utf-8') as f:
    tpl = f.read()
with open(os.path.join(AQUI, 'sim_datos.json'), encoding='utf-8') as f:
    datos = f.read()
assert '/*DATOS*/null' in tpl
with open(os.path.join(AQUI, 'simulacion.html'), 'w', encoding='utf-8') as f:
    f.write(tpl.replace('/*DATOS*/null', datos))
print(f'sim/simulacion.html ({(len(tpl) + len(datos)) / 1024:.0f} KB)')
