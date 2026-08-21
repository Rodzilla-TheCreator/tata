# La capa de seguridad

## Qué hace un escáner certificado

Barre un plano a 15 cm del piso y define zonas de protección y de aviso. Si algo entra en la
zona, sus **dos salidas OSSD** caen en menos de 80 ms y van **cableadas directo al relé de
seguridad**, que corta la tracción. Doble canal: una falla sola no anula la función. Se
autodiagnostica según IEC 61508.

## Qué NO hace — y esto es lo importante

- No alimenta el filtro de Kalman
- No participa en la localización ni en el SLAM
- No planifica rutas ni corrige la pose
- **No pasa por la computadora de navegación**

ISO 3691-4 exige que las dos capas estén **arquitectónicamente aisladas**: la salida de seguridad
es certificada, el dato de navegación es sólo informativo. La computadora se puede colgar, el SLAM
se puede perder, el software puede tener un bug — y la máquina se detiene igual.

**Por eso se puede desarrollar el 100% de la navegación sin escáneres y montarlos después sin
tocar una línea de la matemática ni un parámetro de sintonización.** Son paro de emergencia, no
percepción. Agregarlos tarde no es deuda técnica: es la arquitectura correcta.

## El único acoplamiento real: el sobre de velocidad

Cálculo en `analisis/campo_proteccion.py`. Reacción total 330 ms — 80 del escáner, 50 del
controlador y contactor, 200 de respuesta del freno — más la distancia de frenado.

| Velocidad | Zona de protección mínima |
|---|---|
| 0.5 m/s | 0.33 m |
| 1.0 m/s | 0.68 m |
| 1.5 m/s | 1.16 m |
| 2.0 m/s | 1.76 m |
| 3.3 m/s | **3.91 m** |

A velocidad de catálogo la zona de protección tendría que medir más de lo que mide de ancho el
pasillo. Por eso ningún montacargas autónomo del mundo anda a catálogo bajo techo: todos operan
entre 1 y 1.5 m/s.

**El taller ya llegó por experiencia al mismo límite que impone la norma.** Su tope de 5–8 km/h
coincide con lo que permite la física del frenado.

**Decisión tomada: se diseña para 1.5 m/s desde la primera fase.** El hardware es add-on, el
sobre de velocidad no. Si se desarrolla a 3 m/s y después se mete el escáner, hay que rehacer el
control. Fijarlo ahora no cuesta nada.

## Regla no negociable para el prototipo

En hardware de nivel Ingenio **nunca se llama "freno automático" a nada**. Es *asistencia de
frenado en modo demostración*, teleoperado con un dedo humano sobre un paro físico.

Un freno que actúa solo es función de seguridad. Sin escáner certificado PL d no se vende ni se
demuestra como tal. Si alguien se confía y se lastima, se acabó TaTa y se acabó Montasa.
