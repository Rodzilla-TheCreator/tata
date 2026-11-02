# Protocolo para trabajar en un equipo ajeno — prestado, de cliente o en mantenimiento

**Escrito el 02-nov-2026.** Generaliza `docs/23` (que es el caso concreto del MT 118) a
**cualquier** equipo que no sea nuestro. Va en el deck de Omar como «Cualquier equipo, sin dejar
huella» (`presentaciones/deck_o3.js`, slide 13c).

> **La regla que da el permiso:** ningún cambio irreversible. Si todo va por conectores y el
> equipo sale idéntico a como llegó, se puede tocar. Si algo exigiera cortar, empalmar o
> perforar, **no se hace en un equipo ajeno**: va al 122 o no va.

---

## 1 · El DB9 se adapta a cada equipo

El cableado del DB9 de servicio **puede cambiar de un equipo a otro**. En el 122 resultó
CAN_H = 8, CAN_L = 3, y el pin 6 trae +24 V; otro equipo de la misma familia puede venir
cableado distinto. Lo que **no** cambia en la familia Jungheinrich ETR / EDR es el bus:
**CANopen a 250 kbaud** (manual de servicio, tabla «Sistemas de BUS utilizados»).

**Fuera de esta familia no está garantizado.** Se mide igual; si no es CAN, el paso 2 lo dice.

| Paso | Cómo | Qué se espera |
|---|---|---|
| 1 · Medir | **Llave OFF, batería fuera si se puede.** Matriz de ohmios entre los 9 pines (36 pares, 5 min) y cada pin contra el negativo de batería | Un par con **60–120 Ω** = CAN alto/bajo. La tierra = el pin con continuidad al negativo de batería (si no hay ninguno, la masa se toma del negativo con cable aparte) |
| 2 · Confirmar | **Llave ON**, voltímetro contra el **negativo de batería** (no el chasis) | Los dos del par cerca de **2.5 V** (alto un poco arriba). Anotar cualquier pin con tensión de batería o +24 V: **ese nunca se conecta** |
| 3 · Repinear | Mover los cables en la **bornera del DB9 macho** a los pines medidos | Cinco minutos. El cable no cambia, solo su asignación |
| 4 · Escuchar | `escucha_can.ino` (LISTEN_ONLY) | Tramas a 250k y **0 errores**. Muchos errores → CAN alto y bajo invertidos (en solo escucha, cambiarlos no daña nada) |

**Con el paso 4 ya se leen sus sensores.** Saber **qué byte es qué sensor** en un equipo nuevo
pide además una sesión guiada corta (`grabar_can.py` con guion, como el 06-oct con el
multipiloto); dentro de la familia, lo decodificado en el 122 sirve de punto de partida.

**Terminación:** el manual pide 60 Ω ± 10 % en el bus. Medir lo que tiene el equipo antes de
conectar; si el TJA del cable trae su R3 puesta, el bus baja a la mitad. Se decide antes, no por
accidente (`herramientas/can/LEEME.md`, sección del 14-oct).

---

## 2 · Antes de tocar nada

- [ ] **Autorización** de quien corresponda para ese equipo (Miguel / Omar), y saber hasta qué
      nivel (abajo) está autorizado
- [ ] **Foto de frente de cada conector** que se vaya a desconectar. Es el mapa para restituir
- [ ] **Línea base:** el equipo funciona hoy (prende, el multipiloto maneja, el timón mueve la
      rueda). Anotar los **códigos que ya tiene** el display
- [ ] Las mediciones del paso 1 si es un equipo nuevo

## 3 · Siempre

- **Todo por conectores.** No se corta, no se empalma, no se perfora, no se abre una pieza
  original (para el multipiloto se usa el **repuesto**)
- **Las piezas originales quedan a la mano** y vuelven de inmediato ante cualquier falla
- **Una cosa a la vez.** Restituir entre prueba y prueba; nunca dos cosas desconectadas
- Pines prohibidos según lo medido (en el 122: **5, 6 y 9**)

## 4 · Los tres niveles

| Nivel | Qué | Condición | Riesgo |
|---|---|---|---|
| **1 · Escuchar** | `escucha_can` en el DB9. Solo lectura | Siempre que haya autorización de conectar | Ninguno: LISTEN_ONLY no manda ni ACK |
| **2 · Mandar, quieto** | Imitar el nodo 2 (repuesto) y/o emular el timón | Autorización explícita. **Pedal SIN puentear**: el Master rechaza marcha, elevación y descenso con `E190x` (22-oct). Paro en mano | **Códigos.** Hoy no se pueden borrar (licencia de Judit vencida). Los de pedal se van solos / al reiniciar; **los de dirección (nodo 4) no se sabe** → el timón no se prueba en equipo ajeno hasta saberlo (`docs/23`, regla cero) |
| **3 · Movimiento** | Pedal habilitado + comando | **Solo en nuestro equipo**, o con permiso explícito. **Cadena de paro construida y probada** (watchdog 200 ms + hongo). Rueda en el aire, paro en mano | Real. Por eso va último y con todo lo anterior cumplido |

## 5 · Salida — el equipo vuelve igual que llegó

- [ ] Conectores originales puestos; fotos comparadas contra las de antes
- [ ] El equipo hace lo mismo que en la línea base
- [ ] **Sin códigos nuevos activos.** Si quedó alguno, reiniciar; si no se va, avisar a Miguel
      **antes** de que el equipo salga. Nunca se devuelve un equipo con una falla silenciada
- [ ] Escucha final con 0 errores

## 6 · Lo que se anota en el repo de cada visita

Equipo y número de serie · pinout del DB9 medido · terminación medida · códigos al llegar y al
salir · qué nivel se hizo y qué se aprendió.
