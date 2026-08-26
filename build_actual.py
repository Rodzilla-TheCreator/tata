# Visor del sector A (disposicion actual) con three.js y los datos inyectados.
import io
tpl   = io.open('sim-web/actual_tpl.html', encoding='utf-8').read()
three = io.open('node_modules/three/build/three.min.js', encoding='utf-8').read()
data  = io.open('datos/sectorA.json', encoding='utf-8').read()
giro  = io.open('datos/giro_trayectorias.json', encoding='utf-8').read()
out = (tpl.replace('__THREE__', three)
          .replace('__DATA__', data)
          .replace('__GIRO__', giro))
io.open('sim-web/dist/RETHINK_Actual.html', 'w', encoding='utf-8', newline='\n').write(out)
print('bytes', len(out))
