import base64
tpl = open('tpl.html').read(); three = open('node_modules/three/build/three.min.js').read()
data = open('almacen3d.json').read(); bot = open('botoni_module.html').read()
b = base64.b64encode(open('floor_tex.jpg','rb').read()).decode()
tpl = tpl.replace('<body>', '<body class="operador">', 1)
out = (tpl.replace('__THREE__', three).replace('__DATA__', data)
          .replace('__TEX__', 'data:image/jpeg;base64,' + b).replace('__BOTONI__', bot))
open('Manejo_Montacargas.html','w').write(out)
print('bytes', len(out))
