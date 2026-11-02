# Inyecta giro_318.json en la plantilla → animacion_pasillo.html (autocontenido, lo sirve Pages)
import json, os
d = os.path.dirname(os.path.abspath(__file__))
giro = open(os.path.join(d, "giro_318.json"), encoding="utf-8").read()
tpl = open(os.path.join(d, "animacion_tpl.html"), encoding="utf-8").read()
open(os.path.join(d, "animacion_pasillo.html"), "w", encoding="utf-8").write(tpl.replace("__GIRO__", giro))
print("animacion_pasillo.html listo")
