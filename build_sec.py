# Inyecta three.js en la plantilla y escribe el HTML final.
# encoding='utf-8' explicito: sin eso, en Windows Python abre en cp1252
# y revienta con los acentos de la plantilla.
import io
tpl   = io.open('sec/sec_tpl.html', encoding='utf-8').read()
three = io.open('node_modules/three/build/three.min.js', encoding='utf-8').read()
out   = tpl.replace('__THREE__', three)
io.open('TaTa_Secuencia.html', 'w', encoding='utf-8', newline='\n').write(out)
print('bytes', len(out))
