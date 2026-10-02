# Pendientes del puerto — cierre del 30-sep-2026

Lo vigente arriba. El detalle de cada cosa está en `serie/tabla_fusibles_de9.md`,
`manuales_scribd.md` y `docs/16`.

## Dónde quedó

- **El DB9 probablemente es CAN, no serie.** El pinout del conector de servicio
  `X200` de Jungheinrich (sacado de un ECR) cuadra con lo medido: pin 6 = +24 V por el
  fusible 4F15, pin 5 = GND conmutado (abierto con batería fuera). CAN_L en el 3,
  CAN_H en el 8, tierra del bus en el 2. **Es hipótesis: la tabla es de otro modelo.**
- Eso explica el silencio del FTDI, el eco deformado y el «no tiene tierra».
- **El menú de servicio del display funciona** (Settings → Settings + P-arriba → PIN).
  *Diagnose* muestra sensores en vivo. El PIN no se anota en el repo.
- Códigos activos: `E2325.01` temp. aceite, `E2320.01` sensor de presión A,
  `E2504.01/.02` salidas del control hidráulico, `E0106.01/.02` hombre muerto (pedal),
  `E0106.16` sin documentar.
- Fusibles: **5 A temporales en 4F15 y 6F9** (van 2 A). **10 A en 5F3, 3F11 y 4F10**
  (van 2 A según el manual; 3F11 es el control de dirección).

## Banco, en la i3 — antes de ir al equipo

```
□ 1. 120 Ω TEMPORAL entre CANH y CANL en la protoboard (sin soldar)
□ 2. prueba_can.ino corrida 1  → ECO COMPLETO 20/20
       30-sep sin terminador: 0/20 y 135 errores RX. Sospecha: el terminador
□ 3. prueba_can.ino corrida 2, sin el cable RX (LV2 → GPIO22) → CERO RECIBIDAS
□ 4. QUITAR el 120 Ω temporal
□ 5. Re-soldar el DB9 macho:  CANH → 8 · CANL → 3 · GND → 2 · nada en 5, 6, 9
       Hoy está como CiA-303 (CANH 7, CANL 2). ⚠ Si el GND quedó en el pin 6,
       NO se conecta al equipo: ahí hay +24 V
□ 6. Cargar escucha_can.ino (LISTEN_ONLY, compila con esp32 3.3.11)
```

## En el montacargas

```
□ A. (1 min, recomendado antes de enchufar) confirmar X200:
       batería fuera:  pin 3 ↔ pin 8  ≈ 60 Ω
       llave ON, negra al pin 2:  pin 3 y 8 ≈ 2.5 V · pin 9 ≈ 12 V
□ B. escucha_can.ino — laptop a BATERÍA, conectar con llave OFF,
       después llave ON y paro arriba:
       · 60 s quieto · un ciclo de llave OFF→ON grabado desde el arranque
□ C. Con la escucha corriendo, entrar a Diagnose en el display:
       ¿aparece tráfico SDO (0x600/0x580) cuando el display pide valores?
□ D. STEER → Diagnose + escucha, girando el timón tope a tope, en video:
       · valores de los sensores de ángulo · qué PDO cambia
       · contar vueltas tope a tope (el simulador usa 2.6; fábrica 5.5)
□ E. Fotos de TODAS las pantallas de Diagnose y Parameter, solo leer.
       Buscar: relación de dirección, P1/P2/P3, retardo de freno
□ F. Buscar el conector del CanCode (12 pines, Mini-Mate-N-Lok) junto a la llave. Foto
□ G. Foto del conector del módulo KD Medi CO 250K (51540777): ¿puesto?
□ H. Cuando lleguen: fusibles de 2 A en 4F15, 6F9, 5F3, 3F11, 4F10 — con el chino
```

□ I. Si el DB9 no llega al bus: escuchar en el conector del MAESTRO 1U16
       (ver herramientas/componentes/). El bus pasa sí o sí por ahí.
       Sin cortar ni pinchar aislante: puntas de retro-sondeo por detrás del conector.
       Cómo encontrar el par CAN sin esquema:
         · batería fuera, escala 200 Ω: el par que da ≈ 60 Ω entre sí
         · llave ON, contra batería −: los dos ≈ 2.5 V en reposo;
           con tráfico, CANH promedia algo arriba y CANL algo abajo
       Alternativa más chica, si existe: el conector del CanCode junto a la llave (F)

**No se hace:** abrir, reprogramar o escribir en el 1U16 · FTDI al DB9 (mete tensión en CAN_L) · mover hidráulica (falta sensor,
riesgo de aceite) · *Save* en Parameter · entrar a STD-PARAMETER o CONFIGURATION.

## Fuera del equipo

```
□ MCF vía Montasa, serie 82824121: sección 002 «Electrical» 07.15 del ETR 335D
   + esquemas 99515375 / 99520170 / 99520663.  Alternativa: revendedor, 25 USD
□ Scribd: ETR335D Spare Parts Catalog 82822585 · ETR345A (teoría de operación, 13 p.)
□ De la Mitsubishi Publication List: todas las filas EDR18N2 / ESR20N2 / ESR23N2
□ Chino: ¿qué se sacó después del 18-sep? ¿también un sensor de presión (E2320)?
□ Chino: ¿en QUÉ EDR18N2 usaba el cable FTDI? ¿En este (serie 82824121) o en otros?
   Si fue en otros, ese equipo es el CONTROL: misma medición que acá
   (pin 3↔8, pin 2↔7, foto de la tarjeta de fusibles y de su etiqueta, número de serie).
   Si allá el DB9 es serie y acá es CAN, la diferencia es de configuración o revisión
   del equipo, no de la tarjeta: la tarjeta es pasiva, solo une el DB9 con el mazo.
□ Reporte a Miguel: listo en Documents\TaTa\Reporte_EDR18N2_2026-09-30.docx, sin enviar
```
