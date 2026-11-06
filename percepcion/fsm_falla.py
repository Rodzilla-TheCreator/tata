# ─────────────────────────────────────────────────────────────────────────────
# Falla y reanudación — qué pasos se pueden retomar a la mitad y cómo se deshace el resto
#
# CLAUDE.md, «Lo que falta» #4: hay pasos que NO se pueden reanudar a la mitad — el pantógrafo
# extendido en altura. Si entra un paro ahí, retomar EXTIENDE desde la mitad (o rendir el
# control así) deja hasta 1.067 m de pantógrafo afuera (doble profundidad; decía 0.61) a varios metros
# de altura.
#
# Reglas:
#   · NO REANUDABLES a la mitad: EXTIENDE, TOMA, RETRAE. Ante una falla se DESHACEN.
#     (RETRAE interrumpido no se «reanuda»: se termina de retraer, que es justo el deshacer.)
#   · Todo lo demás es reanudable: el equipo está en el pasillo, pantógrafo adentro.
#   · El deshacer va SIEMPRE en este orden, sin saltar pasos:
#       1. DESHACE_TOMA  si estaba en TOMA: devuelve la micro-altura (los 12 cm de subir o los
#                        4 cm de bajar) al punto donde empezó. Ni levanta ni suelta a ciegas:
#                        el cubo queda donde estaba antes de la TOMA
#       2. RETRAE        pantógrafo a 0, monótono, paso a paso
#       3. RETROCEDE     sale de la bahía (si había entrado: de APROXIMA a RETROCEDE)
#       4. TRANSITO      uñas abajo — recién con el pantógrafo adentro
#     La altura NO baja mientras el pantógrafo esté afuera (salvo el ajuste fino del paso 1).
#
# Eventos:
#   PARO            el paro físico corta todo: la FSM queda en FALLA, congelada. Al REARMAR
#                   (manual, docs/10) corre el deshacer y termina en PARADA. No retoma la tarea
#                   sola: reanudar es decisión del operador
#   ARUCO_PERDIDO   en paso reanudable: pausa y sigue. En no reanudable: deshace y vuelve a
#                   empezar la fase desde CARRIL (re-aproxima mirando la marca)
#   HUECO_OCUPADO   deshace, libera ese destino, marca el lugar como ocupado, y espera otro
#                   destino (ESPERA_HUECO / ESPERA_TRASBORDO) con el cubo en las uñas
# ─────────────────────────────────────────────────────────────────────────────

PASOS = ['CARRIL', 'RECTA', 'GIRO', 'ELEVA', 'APROXIMA', 'EXTIENDE', 'TOMA',
         'RETRAE', 'RETROCEDE', 'DESGIRA', 'TRANSITO']        # los del simulador, sin renombrar
NO_REANUDABLES = {'EXTIENDE', 'TOMA', 'RETRAE'}
REANUDABLES = set(PASOS) - NO_REANUDABLES
EN_BAHIA = set(PASOS[PASOS.index('APROXIMA'):PASOS.index('RETROCEDE') + 1])


def plan_deshacer(est, ext, altura, alt_toma0):
    """La secuencia segura desde donde quedó el equipo. Nunca salta pasos."""
    pasos = []
    if est == 'TOMA' and alt_toma0 is not None and abs(altura - alt_toma0) > 1e-9:
        pasos.append('DESHACE_TOMA')
    if ext > 1e-9:
        pasos.append('RETRAE')
    if est in EN_BAHIA:
        pasos.append('RETROCEDE')
    if altura > 1e-9:
        pasos.append('TRANSITO')
    return pasos


def seguro_para_ceder(est, ext, altura):
    """¿Se puede soltar el control así? Pantógrafo adentro y uñas abajo."""
    return ext <= 1e-9 and altura <= 1e-9
