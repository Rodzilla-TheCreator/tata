# Simular los mandos — multipiloto, timón y pedal

**Escrito el 02-oct-2026.** Es el camino de **las manos por los mandos físicos** de `docs/19`:
el ESP32 hace lo que hoy hace el operador, por el mismo cable por el que lo hace él.

**De dónde sale:** de los mensajes de evento del manual de servicio
(`herramientas/Codigos de error reach color_*.pdf`). Cada mensaje dice **qué chequea el
equipo para decidir que una señal es válida**, y eso es justo lo que hay que respetar para
que no se dé cuenta de que no es un humano.

> **Advertencia:** la lista de eventos es **común a muchos equipos Jungheinrich** — menciona
> EJC, motores de combustión, asientos. Las reglas de abajo son las que el fabricante usa en
> su familia, y son las más probables en el ETR. **Se confirman midiendo en nuestro equipo**
> antes de construir nada.

---

## Las cuatro reglas que el equipo usa para no dejarse engañar

| # | Regla | Dónde aparece | Qué pasa si se viola |
|---|---|---|---|
| 1 | **Interruptores dobles: un contacto NC y uno NA**, que cambian juntos. Solo valen `0/1` y `1/0` | evento `1.06` (interruptor de seguridad, **hombre muerto**), `1.70`, `1.71`, `1.72` (botones del multipiloto) | `0/0` o `1/1` por más de **500 ms** → falla. En el hombre muerto, **2000 ms**, y **solo se borra reiniciando el equipo** |
| 2 | **Señales analógicas dobles y complementarias**: dos canales que suman ~5 V | evento `1.11` sub 7: «V1 + V2 > 5,5 V o < 4,5 V» | 250 ms fuera de rango → falla |
| 3 | **El sensor del timón es seno/coseno**: canales A y B, y tienen que quedar sobre el círculo unitario | eventos `1.54`, `1.55`, `1.56` | dos procesadores (control y monitor) comparan: más de 500 dígitos de diferencia **cinco veces seguidas en 50 ms** → falla |
| 4 | **Todo en cero al arrancar** y al aplicar el interruptor de seguridad | eventos `9.51`, `9.52` | consigna de traslación o hidráulica distinta de cero por 500 ms → falla |

La regla 4 es **la misma** que `docs/19` llama «arranque en cero». El fabricante llegó a lo
mismo por el mismo motivo.

Y hay una quinta, transversal: **teach-in**. El rango de cada sensor (dónde está el cero,
dónde los topes) lo **aprende** el equipo con Judit (eventos `1.36` y `3.80`, «reenseñar el
MULTIPILOTO»). **Una señal simulada tiene que caer dentro del rango aprendido**, o el equipo
la rechaza. Por eso primero se mide la señal real, y después se imita.

---

## Cada mando, uno por uno

### 1 · El pedal — hombre muerto

**Qué es:** un interruptor de pie con **un contacto NC y uno NA** (regla 1).

```
pedal suelto:      NC cerrado · NA abierto      → «nadie»
pedal pisado:      NC abierto · NA cerrado      → «hay operador»
```

**Cómo se simula:** un **relé de doble contacto inversor (DPDT)**. Un solo relé mueve los
dos contactos a la vez, así que nunca existe el `0/0` ni el `1/1` por más que unos
milisegundos. Lo maneja el ESP32, y **ese relé es el watchdog de `docs/10`**: si se corta
el latido, el relé cae, el equipo ve «pedal suelto» y frena con su propia rampa.

**Ojo con el paralelo:** no se puede poner el relé en paralelo con el pedal real. Con el
pedal suelto su NC está cerrado, y para «pisar» hay que **abrir** ese NC. Hace falta cortar
la línea NC — y no se corta nada. La solución es la de abajo: un arnés enchufable.

### 2 · El timón — sensor seno/coseno

**Qué es:** un sensor de ángulo que entrega **dos canales, A y B**, uno proporcional al seno
y otro al coseno del giro (regla 3). Como el volante da **5.5 vueltas** de tope a tope
(`0x2414`), el sensor da varias vueltas, y el controlador las cuenta.

**Cómo se simula:** **dos canales de DAC**:

```
A = Vo + Va · sen(θ)
B = Vo + Va · cos(θ)
```

donde `θ` es el ángulo del volante virtual. El ESP32 lo va acumulando según lo que pida el
control, **que es exactamente el control Obed**: el timón se queda donde se lo deja.

Tres cuidados:
- **La amplitud `Va` tiene que ser constante** para no salirse del círculo
- **Pasos chicos y rápidos.** Un salto grande de θ se parece a un cable cortado. Actualizar
  a 1 kHz o más, con la velocidad de giro limitada
- `Vo` y `Va` **no se adivinan**: se miden girando el volante real despacio

### 3 · El multipiloto — botones y palancas

**Qué es:** un **nodo CAN propio** (nodo 2, «controles de reposabrazos multifunción»). Por
dentro tiene:
- **botones dobles NC + NA** (regla 1): inclinación, desplazador, selector de dirección…
- **elementos proporcionales** — la palanca de traslación y las hidráulicas — con su
  teach-in. Lo más probable es que sean **dobles y complementarios** (regla 2)

**Cómo se simula — la ruta B de maje:** **abrir un multipiloto de repuesto** y meter las
señales **adentro**, antes de su electrónica:
- botones → relés DPDT o pares de interruptores analógicos complementarios
- palancas → **dos canales de DAC por palanca**, con `V2 = 5 V − V1`

**La gran ventaja:** la electrónica del multipiloto sigue armando sus tramas CAN. **No hay
que descifrar el protocolo**, y el maestro sigue viendo su palanca de siempre.

---

## Cómo se conecta sin cortar un cable

**Arneses enchufables**, uno por mando:

```
   mando real ──[ conector ]──┐
                              ├── SELECTOR ──[ conector ]── mazo del equipo
   ESP32 / DAC / relé ────────┘
               «manual»  /  «teleop»
```

Se desenchufa el mando, se enchufa el arnés en el medio, y un selector físico elige quién
manda. En «manual», el equipo queda como de fábrica. Para el multipiloto ni siquiera hace
falta: se cambia el original por el repuesto modificado.

Para eso hace falta **el conector macho y hembra de cada mando**. Se identifican por foto,
de frente, como los TE de la tarjeta de fusibles.

---

## Cuántos canales hacen falta

| Mando | DAC | Relés |
|---|---|---|
| Timón | 2 | — |
| Palanca de traslación | 2 | — |
| Pedal / hombre muerto | — | 1 DPDT (es el watchdog) |
| Sentido de marcha, claxon | — | 1 DPDT c/u |
| **Fase del hito** | **4** | **3** |
| Cada palanca hidráulica (fase 2) | +2 c/u | — |

Los **4 canales de DAC** son los que `CLAUDE.md` ya pedía. El número salía de la regla 2;
ahora también lo pide la regla 3.

---

## Qué medir antes de construir nada

Todo pasivo. Mucho se puede ver en **Diagnose** del display, que ya muestra sensores en vivo.

```
□ PEDAL, batería fuera, escala de ohmios:
    con el conector del pedal suelto, identificar NC y NA pisando y soltando
□ TIMÓN, llave ON, multímetro (o el ADC del ESP32 grabando) contra el negativo:
    canales A y B girando DESPACIO → Vo, Va, y que de verdad sean seno/coseno
    contar las vueltas tope a tope (corrige el 2.6 del simulador)
□ TIMÓN en Diagnose (STEER): qué valor muestra, y si se mueve con lo medido
□ MULTIPILOTO: con la escucha CAN corriendo, mover cada palanca y botón:
    qué trama cambia (sirve para el plan del bus y como control del de los mandos)
□ FOTOS de frente de los conectores del pedal, del sensor del timón y del multipiloto
□ CONSEGUIR un multipiloto de repuesto para abrirlo
```

## Lo que no se hace

- Cortar cables o pinchar aislante: **arneses enchufables**
- Abrir el multipiloto **original**: se abre un repuesto
- Probar con el equipo en el piso sin el hongo en serie y alguien al lado
- Simular el hombre muerto sin que el relé sea el del watchdog: **el pedal virtual es el
  freno**, y tiene que caer solo si se corta el latido
