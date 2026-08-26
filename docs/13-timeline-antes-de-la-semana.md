# Todo lo que va antes de la semana de locos

Ordenado por **dependencia, no por día**. Los días los asigna maje.

---

## Bloque 0 · Disparar YA — es lo único con reloj externo

Todo lo demás se recupera trasnochando. **Los módulos que no se pidieron hoy no llegan
porque alguien se quede despierto.**

Se pide ahora lo que sirve en **todas** las ramas del diagnóstico, sin importar qué salga:

```
MCP4728 ×2 · ADUM1201 ×4 · DG419 ×4 · AS5600 ×3 · MCP6002 ×4
BNO085 ×1 · DC-DC aislado 48→12 y 12→5 · analizador lógico 8 ch
hongo de paro NC · TVS SMBJ
```

**No se pide todavía:** nada específico de dirección. Depende de la pregunta 8 de `docs/11`.

De Steren, cuando se pueda: protoboards, placa perforada, relés SPDT de señal, borneras de
tornillo, 1N4148 y 1N4007, resistencias 1k/10k, capacitores 100nF/10µF, cable calibre 22
**multifilar** (vibración), fusibles y portafusibles.

---

## Bloque 1 · Antes de la visita, desde el cuarto

| | Qué |
|---|---|
| 1 | Imprimir `docs/12` (la sombra) y `docs/11` (las doce preguntas) |
| 2 | Armar y **probar en casa** el AS5600 + Arduino. Que funcione antes, no allá |
| 3 | Puntas de retro-sondeo, o hacerlas con alfileres gruesos y termorretráctil |
| 4 | Celular cargado y con espacio para video; segunda cámara si la hay |
| 5 | Tabla rígida o escuadra para bajar puntos del cuerpo al piso |
| 6 | Tiza de varios colores — una por corrida del operador |
| 7 | Coordinar con José Asturias: día, hora, EPP, acceso |

---

## Bloque 2 · La visita — dos sesiones, no una

**Sesión A · la sombra.** 1 hora, flexómetro y papel, `docs/12`. Máquina apagada salvo el
último ejercicio. **Desbloquea todo lo demás.**

**Sesión B · el diagnóstico eléctrico.** 2.5 horas, `docs/11`, doce preguntas. Ni un cable
cortado.

Pueden ser el mismo día si dejan. **Si hay que elegir una, es la A**: sin la silueta el
planificador sigue siendo hipótesis, y sin eso no hay nada que programar.

---

## Bloque 3 · Después, sin volver al sitio

| | Qué | Depende de |
|---|---|---|
| 1 | Meter la silueta real al planificador y re-correr | sesión A |
| 2 | Recalcular la ventana de carriles; ver si los 85 cm se mueven | ↑ |
| 3 | Cerrar los tres planes de `docs/10` según qué caso salió | sesión B |
| 4 | Comprar lo específico de dirección, ya sabiendo cuál es | ↑ |
| 5 | Soldar las placas de intercepción | ↑ |
| 6 | Firmware de teleop: rampa, tope por velocidad, cambio de sentido con gatillos en cero | — |
| 7 | La dispersión del operador, escrita como requisito de precisión | sesión A |
| 8 | Escena de choque en 3D con la silueta medida | sesión A |

---

## Bloque 4 · Documentar mientras pasa, no después

El pathway 2 se escribe **haciendo** el pathway 1. Un procedimiento redactado de memoria seis
meses tarde no entrena a nadie.

- **Bitácora de la visita el mismo día.** No el fin de semana.
- **El rundown para Omar** — qué pedirle al próximo cliente: DWG, fecha, contacto de
  mantenimiento, acceso, ventana horaria.
- **El guion de venta de Omar** — ya hay un cliente esperando y hoy el guion no existe.

---

## Dos advertencias

**El bloque 0 no se recupera con horas.** Es el único con dependencia externa.

**Cuidado con el cliente nuevo de Omar.** La sustancia son dos máquinas trabajando en
RETHINK, y hoy hay cero. Llevarlo al cliente nuevo antes de terminar el pathway 1 gasta el
argumento antes de tenerlo. Vale decirle: *dame RETHINK primero, y después lo llevamos.*
