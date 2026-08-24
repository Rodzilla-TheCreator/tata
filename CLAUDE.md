# TaTa — contexto para Claude Code

Kit de retrofit que vuelve autónomos, por etapas, los montacargas que un almacén ya opera.
Proyecto interno de **Montasa** (distribuidor de montacargas en San Pedro Sula, Honduras).

**Los detalles completos están en `docs/`.** Este archivo es el mapa; ahí está el territorio.

| Documento | Qué contiene |
|---|---|
| `docs/01-hallazgos-rethink.md` | Lo que encontramos en el almacén del cliente |
| `docs/02-maquina-y-geometria.md` | El EDR18N2 y si cabe el giro en 3 m |
| `docs/03-lidar-y-localizacion.md` | Por qué los marcadores van primero y el LiDAR de apoyo |
| `docs/04-seguridad-y-normativa.md` | Por qué la capa de seguridad va aparte |
| `docs/05-producto-y-negocio.md` | Escala de madurez, costos, retorno |
| `docs/06-simuladores.md` | Los dos simuladores y cómo se usan |
| `docs/07-estado-y-siguientes-pasos.md` | Qué falta, en orden, con puertas de decisión |
| `docs/08-setup-git-agente.md` | **Cómo dejar la máquina lista para empujar y cómo trabajar con git** |
| `docs/09-briefing-secuencia.md` | La simulación de secuencia: qué es y qué falta |
| `docs/10-intervencion-electrica.md` | Los tres planes de intervención: freno, tracción, dirección |
| `docs/11-plan-de-diagnostico.md` | **La visita de medición. Va ANTES del doc 10** |

## Lo mínimo para no meter la pata

**Máquina objetivo:** Mitsubishi **EDR18N2**, reach truck pantográfico de operador parado.
2.91 m de largo con uñas de 1.21 m, ancho 1.054, radio de giro 1.797, pantógrafo 0.61,
desplazador ±0.12, inclinación 4°/3°. Velocidad de trabajo **7.9 km/h**, no los 12 de catálogo.

**El pasillo mide 3.00 m.** Los 2.91 m son con el pantógrafo **recogido**; extendido son 3.52 m.
Recogido el barrido es **2.80 m** y el Ast **3.00 m** — ojo, el Ast ya incluye los 20 cm de
holgura de norma, así que **cabe con margen normal, no con margen cero**. Extendido el barrido
sube a 3.41 m y no existe ese pasillo. De ahí la regla: *girar recogido, extender sólo ya
alineado.*

**La tolerancia no está en el pasillo, está en la bahía.** En el pasillo sobran 90 cm por lado;
la bahía deja **4.5 cm**. El desplazador cubre eso 2.7 veces. **Requisito de nav: ±4.5 cm.**

**Marcadores primero, LiDAR de apoyo.** Un AprilTag en papel laminado da posición absoluta sin
deriva. Al LiDAR le queda ver lo que no debería estar ahí, y sostener la operación cuando el
marcador falla.

**La seguridad va aparte por norma**, no por recorte. ISO 3691-4 exige que la capa certificada
esté aislada de la navegación. Se puede desarrollar todo sin escáneres y montarlos después sin
tocar la matemática. Lo único que sí hay que fijar desde hoy es el sobre de velocidad: **1.5 m/s**.

**Nunca llamar "freno automático" a nada en hardware de nivel Ingenio.** Es asistencia de frenado
en modo demostración, teleoperado con un dedo sobre un paro físico.

**Piezas y ingeniería son cosas distintas.** Emular las señales cuesta $198 de piezas; lo caro es
descubrir qué señal es cada cable, y eso es NRE — una vez para todo el modelo, no por unidad.

## Los cinco niveles

`Ingenio` → `Piloto` → `Serie` → `Flota` → `Homologado`.
No son cinco calidades: son cinco preguntas distintas. **Piloto ($8,458 en piezas) es el que se
recomienda.** Nunca usar la palabra "scrappy" en material que vaya a leer la dirección.

## Cómo trabajar aquí

- Responder en **español**, directo y conciso. Máximo **400 palabras** de prosa salvo que se pida
  más; tablas, código y listas de archivos no cuentan.
- No adular ni rellenar. Si algo está mal, decirlo de frente.
- **Verificar antes de afirmar.** Casi todo lo de `docs/` tiene su cálculo en `analisis/`.
  Si vas a contradecir un número, corré el script primero.
- Cuando un cálculo contradiga algo escrito antes, **corregirlo explícitamente**. Ya pasó dos
  veces en este proyecto y las dos veces mejoró el resultado.

## Equipo

- **maje** — lidera, construye todo, habla con operadores y mecánicos
- **Pato** — meses de LiDAR y SLAM en el proyecto de graduación. Su stack tuneado se trae al
  simulador antes de tocar nada; lo valioso es su parametrización
- **Christian** — captura y medición en campo
- **Fabrizio** — mediador y cara comercial
- **Omar** — dirige Montasa, aprueba presupuesto. Perfil financiero, poco contexto técnico

## Reconstruir los entregables

```bash
python3 sim-web/build.py             # simulador completo
python3 sim-web/build_operador.py    # vista de operador
python3 datos/extract3d.py           # re-extraer geometría del DXF (necesita el .dxf)
python3 sim-isaac/export_usd.py      # regenerar la escena USD
node presentaciones/deck_o2.js       # deck de Omar
node presentaciones/deck_r.js        # deck de RETHINK
```
