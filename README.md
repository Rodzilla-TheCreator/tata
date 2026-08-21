# TaTa

**Tecnología Avanzada de Transporte Autónomo** — kit de retrofit que vuelve autónomos, por
etapas, los montacargas que un almacén ya opera. Proyecto interno de **Montasa**, San Pedro Sula.

No vendemos una máquina nueva: vendemos el cerebro, los ojos y las manos que le faltan a la
que ya está trabajando.

## Por dónde empezar

| Si querés… | Andá a |
|---|---|
| Entender todo el proyecto | `CLAUDE.md` — se lee solo si abrís esta carpeta con Claude Code |
| Manejar el almacén en 3D | `sim-web/dist/Almacen_RETHINK_3D.html`, abrilo en el navegador |
| Montar el banco de Isaac Sim | `sim-isaac/README_SIM.md` |
| Ver los números del producto | `producto/TaTa_Escala_EDR18N2.xlsx` |
| Presentarle a Omar | `presentaciones/TaTa_Caso_Negocio_Omar.pdf` |

## Estructura

```
docs/           los hallazgos y las decisiones, en prosa
sim-web/        simulador three.js — fuente, build y los dos HTML publicados
sim-isaac/      banco de pruebas Isaac Sim 6.0: escena USD y rigs de sensores
analisis/       los cálculos que sostienen cada afirmación, con sus figuras
datos/          geometría extraída del DWG del cliente
producto/       BOM y escala de madurez del kit
presentaciones/ los dos decks vivos, con sus guiones
campo/          material para visitas al almacén
```

## Estado

| | |
|---|---|
| Máquina objetivo | Mitsubishi **EDR18N2**, reach truck pantográfico de operador parado |
| Cliente piloto | RETHINK / ELCATEX, almacén de maxicubos |
| Simulador web | funcionando, desplegado en GitHub Pages |
| Banco Isaac Sim | escena y rigs listos; falta la articulación |
| Prototipo físico | pendiente de aprobación de presupuesto |

## Deploy del simulador

Los dos HTML de `sim-web/dist/` son autocontenidos: three.js va embebido, no piden red.
Se copian tal cual a donde se sirvan.

```bash
python3 sim-web/build.py            # → Almacen_RETHINK_3D.html
python3 sim-web/build_operador.py   # → Manejo_Montacargas.html (vista de operador)
```

## Licencia

Sin licencia pública. Todos los derechos reservados mientras no se defina el acuerdo
entre las partes.
