# La sombra del EDR18N2 — datos crudos y dónde están

Acá van los `.json` que baja `herramientas/sombra.html`, uno por visita. Se commitean: son el
dato crudo de campo y no se regeneran. Procedimiento: `docs/12-medicion-de-la-sombra.md`.

## Estado al 06-nov-2026: la tabla cruda NO está en el repo

Se revisó todo: `main`, la rama vieja `claude/claude-code-remote-access-j7ylyk` y el historial
completo de las dos. **Ningún commit trae la tabla de estaciones** (ni `.json`, ni `.md`, ni
foto de la hoja). Lo único que quedó son resúmenes:

| Dato | Valor | Dónde quedó escrito |
|---|---|---|
| Fecha de la medición | **8-sep-2026** (Las Palmas), un solo lado, simetría asumida | `docs/15` §A1 y §A3 |
| `W_RESTO` ancho del capó | 1.065 m (confirmado) | `CLAUDE.md`, 18-sep |
| Escalón capó → patas | 0.25 m (confirmado) | `CLAUDE.md`, 18-sep |
| `L_ANCHO` largo del tramo ancho | **0.48 m** (el repo decía 0.20) | `CLAUDE.md`, 18-sep |
| El tramo ancho | **estaciones 102 a 150** | `docs/15` §A1 |
| Rueda de carga | **estación 282** | `CLAUDE.md` y `docs/15` §A2 |
| Culo, perpendicular | 95 cm → semiancho negativo, **imposible** (diagonal o flexómetro abierto ~1°) | `docs/15` §A3 |
| `W_MAX` pata a pata | **nunca se midió** (1.315 es del repo) | `CLAUDE.md` |
| Puntos de la curva del culo | **perdidos**: estaban en la tabla cruda | — |

## Dónde buscarla

La captura se hizo con Claude en campo, probablemente desde la i3 o desde el celular:

1. **En la i3, en las conversaciones de Claude Code** (se guardan en disco). En PowerShell:
   ```
   Select-String -Path "$env:USERPROFILE\.claude\projects\*\*.jsonl" -Pattern "estaci" -List | Select Path
   ```
   Abrí el archivo que salga y buscá la tabla de estaciones.
2. **En el navegador donde se usó `sombra.html`** (celular o laptop): abrí `herramientas/sombra.html`
   en ese mismo navegador. Si los datos siguen en su almacenamiento (`tata_sombra_v2`), aparecen
   las corridas → **«Bajar .json»** y subilo acá.
3. **En Descargas** de ese aparato: `sombra_AAAA-MM-DD.json`.
4. **En claude.ai / la app del celular**: buscar en el historial «estación», «sombra» o «culo».

## Por qué importa ahora

- **El radio del culo** decide si el giro de 90° vacío entra en 3.00 m sin usar el retranqueo entre
  postes (`clases/giro.html` §3). `planificador_rutas.py` hoy usa el culo **en ángulo recto**; el
  viejo `planificador_giro.py` suponía radio 12 cm.
- **Dato en tensión:** `docs/15` pone el tramo ancho en las **estaciones 102–150**, pero las siluetas
  de `planificador_rutas.py` lo ponen **delante de la torre**, a 1.70–2.18 m del culo. Si las
  estaciones se contaron desde el culo, las patas no están donde el planificador las dibuja. No
  cambia el ancho máximo del giro (los extremos son el culo y la punta de uña), pero sí el resto de
  la silueta. Se resuelve con la tabla cruda o midiendo de nuevo.
