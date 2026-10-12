# Almacén nuevo — pasillo de 3.18 m

**No es RETHINK.** Cliente/sitio todavía sin nombre en el repo. Datos dados por maje el 12-oct-2026.

| Dato | Valor | Origen |
|---|---|---|
| Ancho de pasillo libre | **3.18 m** | maje |
| Bahías por lado | **20** | maje |
| Ancho de bahía | **2.35 m** | maje |
| Separación entre bahías (poste) | **6" = 0.1524 m** | maje |
| Niveles | **4** (altura no importa por ahora) | maje |
| Largo del pasillo | **50.20 m** = 20 × 2.35 + 21 × 0.1524 | derivado |
| Fondo de rack | 1.10 m | **supuesto**, copiado de RETHINK |
| Huecos por bahía | 2 | **supuesto**, copiado de RETHINK |
| Equipo | EDR18N2, 2.91 m con uñas | `CLAUDE.md` |
| Equipo que opera hoy en el sitio | «MIMA o LIMA», pantógrafo | **de oídas, 12-oct.** No aparece como marca de montacargas; ITW Mima hace emplayadoras. Dato en tensión hasta ver la placa |

## El giro de 90°

`planificar_giro_318.py` — Hybrid A* con la silueta del `CLAUDE.md` **más las uñas**
(punta a 2.90 m del culo). Es la diferencia con `analisis/planificador_giro.py`, que es solo chasis.

| | Resultado |
|---|---|
| ¿Cabe a la primera, un solo arco? | **No.** Un arco a tope necesita el carril del pivote a ≥1.40 m del rack opuesto (culo) y ≤1.29 m (punta de uña). Se cruzan |
| Maniobra | **3 tramos: adelante 0.20 · atrás 0.28 · adelante 0.08 m** |
| Carril del pivote | 1.80 m desde el rack opuesto (ventana factible 1.00–2.15 m) |
| Holgura mínima | **5.3 cm** contra cara de rack, en toda la maniobra |

Con 3.18 m y 2.90 de largo, de frente al rack sobran **28 cm** en total entre culo y punta.
El giro entra, pero en dos tiempos — igual que el operador en RETHINK con 3.00 m.

**Mismas incertidumbres que el resto del repo:** `XPIV` derivado, `W_MAX` sin medir.
Si cambian, correr de nuevo el planificador.

## La animación

`animacion_pasillo.html` — planta a escala real, cámara que sigue al equipo, alzado de 4 niveles
esquemático. Lazo de 14 tareas a huecos al azar en ambos lados.

```bash
python3 almacen-nuevo/planificar_giro_318.py   # → giro_318.json
python3 almacen-nuevo/build_animacion.py       # → animacion_pasillo.html (se versiona, lo sirve Pages)
```

## Falta

- **Foto de la placa del equipo que opera ahí.** Si no es EDR18N2, el giro se recalcula con su largo con uñas, ancho y radio

- Nombre del cliente/sitio, y si la unidad de carga también es IBC
- Medir fondo de rack y confirmar si caben dos cargas por bahía
- Alturas de nivel, cuando importen
