# Lo que traen los manuales bajados de Scribd — 30-sep-2026

**Los PDF NO están en el repo** (es público y son documentos con derechos de terceros).
Viven en la i3, en `C:\Users\Rodz\Downloads\`. Este archivo dice qué hay en cada uno y
en qué página, para no tener que volver a leerlos enteros.

## 1 · «ETR 335D 345 parts manual» — Scribd 1071038591, 516 págs.

**El título miente.** Lleva la portada y los índices del manual de servicio del ETR 335D,
pero casi todo el contenido es del **ETR 320 (2006–07)** y de otros equipos. Sin el
esquema `99515375`.

| Págs. | Qué es | ¿Aplica al nuestro? |
|---|---|---|
| 1–8 | portada e **índices de sección** del manual real del ETR 335D | sí, solo como índice |
| 25–30 | esquema `99400317`, **ETR 320** | no |
| 31–110 | índice de designaciones eléctricas, **08.14** | **sí** |
| 125–348 | códigos de evento **04.17** | sí. El `0106` llega solo hasta `.15` |
| 346–348 | **IDs de nodo CAN** | sí |
| 352–355 | display CANDIS (03.06): pines y **menú de servicio** | parecido |
| 356–380 | Jungheinrich **ISM** (módulo de acceso, data recorder) | parecido |
| 381–392 | computadora de a bordo (03.06), modo servicio | parecido |
| 393–410 | **CanCode** (01.12) | parecido |
| 411–412 | fusibles, **ETR 320** | no |
| 413–428 | pines del **ECR**, incluye el `X200` | otro modelo |
| 429–431, 460–462 | controlador AS4814i | otro modelo |
| 512–516 | controlador de dirección AS4803z | parecido |

### Lo que se saca

**La sección 002 «Electrical», edición 07.15, del manual real del ETR 335D** (pág. 3) trae
justo lo que falta: *Fuses · EMERGENCY stop switch · CanCode · Plugs/connectors ETR
335D/340/345 · Wiring ETR 340/345/335d · Diagnosis*. Es lo que hay que pedir a MCF.

**Índice 08.14 (págs. 31–110):**
- `X200` = **Service-Stecker**, conector de servicio. Es el único conector «de servicio»
- `4F15` = Zugangsberechtigung, autorización de acceso
- `6U10` = módulo de acceso · `X680` / `X681` = sus conectores
- `A1` = Sicherungskarte, la tarjeta de fusibles

**Nodos CAN fijos (págs. 346–348):**

| Nodo | Qué es | Nodo | Qué es |
|---|---|---|---|
| 1 | Master | 11 | MFC 1 (frenos) |
| 2 / 10 | Multi-Pilot 1 / 2 | 12 | MFC 2 (hidráulica) |
| 3 | Display (CANDIS / a bordo) | 16 / 17 | batería / cargador |
| 4 / 5 / 6 | dirección / rueda carga der. / izq. | 28 | CanCode |
| 7 | elevación | 29 | ISM |
| 8 / 9 | tracción 1 / 2 | 30 | **PC de servicio** |
| 31 | **APM+**, interfaz de automatización | | |

**Conector de servicio del ECR, `X7` = `X200` (pág. 420):**
```
1 n.c.   2 CAN 0 V   3 CAN_LOW   4 n.c.   5 GND conmutado
6 +24 V conmutado    7 n.c.      8 CAN_HIGH   9 CAN +12 V
```
Cuadra con lo medido en nuestro DB9 (pin 6 alimentado por fusible; pin 5 abierto con la
batería fuera). **Pero es de otro modelo, y el propio manual avisa (pág. 431) que la
distribución X100/X200 cambia por tipo de equipo.** En el ETR 320, `X200` es el conector del
controlador de elevación. Pista fuerte, no dato.

**Módulo de acceso ISM, conector `X680` (pág. 360):** CAN de entrada y de salida (va *en*
el bus), pin 15 *«U-ISM out (24V) for JUDIT»*, y separación de potencial entre 0 V y
batt−, salvo en equipos JUSTCAP/CANopen 250k.

**Menú de servicio** (pág. 355): DRIVE / LIFT / STEER / BATTERY, cada uno con *Parameter* y
*Diagnose*. En nuestro equipo **funciona**: se entra por Settings + P-arriba + PIN de 4
dígitos. *Diagnose* muestra sensores en vivo. El PIN no se anota acá.

## 2 · «Manual de Servicio Montacargas Mitsubishi ESR23N2 36 2» — Scribd 593992870, 46 págs.

Scribd le pone «FG25N» por IA; el título original es ESR23N2. **No es nuestro equipo**:
es la **generación Mitsubishi anterior, con electrónica ZAPI** (controladores AC-2, AC-3,
MHYRIO; display SICOS), 36 V, fusibles `1F1…9F1`. Nuestro EDR18N2 es Jungheinrich.

Lo que sí enseña, pág. 13, *Communication Connections*: su **conector de programación
`X15`** es **serie diferencial** (pares `PCL`/`NCL` de RXD y TXD, más BOOT, +12 V y dos GND
en 3 y 6), cableado al display. **No es RS-232**: ni con el pinout correcto hablaría un
cable FTDI. Y **no cuadra con nuestro DB9**: allá el pin 6 es GND, acá el pin 6 viene de un
fusible.

## Lo que falta, y dónde

- El esquema `99515375` (+ `99520663`, `99520170`): revendedor 25 USD, o MCF vía Montasa
- La sección 002 «Electrical» 07.15 del manual del ETR 335D: MCF vía Montasa
