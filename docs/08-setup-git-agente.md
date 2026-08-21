# Setup de git para el agente

Este documento es para **Claude Code**, no para maje. El objetivo: que maje nunca tenga
que abrir un archivo de codigo ni escribir un comando de git. El agente commitea, empuja
y explica; maje revisa en GitHub y decide.

Repo: `git@github.com:Rodzilla-TheCreator/tata.git` · publico · rama `main`.

---

## 1 · Que debe hacer el agente al abrir el proyecto

```bash
git clone https://github.com/Rodzilla-TheCreator/tata.git
cd tata
```

Si la carpeta ya existe, `git pull` antes de tocar nada. **Siempre.** Hay mas de una
sesion de Claude trabajando sobre este repo y la otra pudo haber empujado.

---

## 2 · Dejar la maquina lista para empujar

Verificar primero, porque puede que ya este resuelto:

```bash
ssh -T git@github.com          # esperado: "Hi Rodzilla-TheCreator!"
gh api user --jq .login        # esperado: Rodzilla-TheCreator
```

**Si SSH ya responde con el saludo, no hay nada que hacer.** Saltar a la seccion 3.

### Si SSH falla

El agente genera la llave (la privada nunca sale de la maquina):

```bash
ssh-keygen -t ed25519 -C "rodrigo.j.monterroso@gmail.com" -f ~/.ssh/id_ed25519 -N ""
cat ~/.ssh/id_ed25519.pub
```

Y le pasa a maje la llave publica con esta instruccion exacta:

> Abri https://github.com/settings/ssh/new
> Titulo: algo que identifique la maquina. Key type: **Authentication Key**.
> Pega la llave y dale al boton verde **"Add SSH key"**.

**El agente no hace este paso.** Requiere autenticarse en GitHub y eso lo hace maje.
Error frecuente: maje pega la llave y no le da al boton. Si SSH sigue fallando,
preguntarle si le dio click antes de asumir otra causa.

### La trampa del insteadOf

`gh auth login` deja a veces una regla global que reescribe toda URL SSH a HTTPS,
y entonces la llave queda decorativa: git sigue usando el token, que caduca.
Comprobar y limpiar:

```bash
git config --global --get-regexp "url\..*insteadOf"
git config --global --unset-all "url.https://github.com/.insteadOf"
```

Confirmar que el remoto quedo en SSH de verdad — `get-url` miente si la regla sigue viva:

```bash
git remote set-url origin git@github.com:Rodzilla-TheCreator/tata.git
git remote get-url origin      # tiene que decir git@github.com, no https
git ls-remote origin main      # operacion de red real; si pasa, esta listo
```

### Si hace falta `gh` (crear repos, PRs, issues)

SSH mueve commits pero no crea repos. Para eso:

```bash
gh auth login -h github.com -p https -w
```

Lo corre **maje**, no el agente: el `-w` abre el navegador y se autoriza ahi, sin que
ningun token pase por el chat.

---

## 3 · Como trabaja el agente

**maje no toca codigo.** El agente edita, commitea y empuja. maje revisa en GitHub
o pregunta.

```bash
git pull                       # siempre, antes de editar
# ... el agente hace los cambios ...
git add -A
git commit -m "..."
git push
```

Directo a `main`. No hay CI ni otros colaboradores humanos; una rama por cambio
agrega ceremonia sin agregar seguridad. Si un cambio es grande o arriesgado, decirlo
antes de empujar y dejar que maje decida — no abrir una rama por reflejo.

### Mensajes de commit

En español, imperativo, primera linea corta y concreta. Si el cambio corrige algo,
el cuerpo dice **que estaba mal y por que**, no solo que se cambio. Ejemplo real
del repo:

```
sim-isaac: colliders del USD, arranque sin sensores y spawn medido

Las 513 PhysicsCollisionAPI estaban aplicadas al Xform y no al Gprim.
UsdPhysics construye el collider a partir de la geometria, asi que piso,
muros y racks no generaban ningun collider [...]
```

### Antes de empujar

- `git status` limpio de basura: nada de `.orig`, `.bak`, `__pycache__`, capturas sueltas
- Los `.py` compilan: `python -m py_compile <archivo>`
- Si se toco `PropuestaIT_RETHINK.usda`, validar con `pxr` (`pip install usd-core`):
  tiene que abrir, `upAxis Z`, `metersPerUnit 1`, y las `CollisionAPI` en `Cube` — **nunca
  en `Xform`**, ahi PhysX no crea collider y todo se vuelve atravesable

### Cuando SI preguntar antes de actuar

- Cambiar la visibilidad del repo. **Hoy es publico** y lleva el caso de negocio de Omar,
  la escala de costos, el nombre del cliente y los planes de visita. maje ya decidio
  publico sabiendo eso; no relitigarlo, pero tampoco cambiarlo por cuenta propia.
- Borrar archivos, reescribir historia, `push --force`.
- Publicar cualquier cosa fuera de este repo.

---

## 4 · Estado al 21-ago-2026

Ultimo commit: `77057f9`.

Arreglado y ya en el repo:

| Que | Donde |
|---|---|
| 513 `CollisionAPI` movidas de `Xform` a `Cube "geo"` | `sim-isaac/PropuestaIT_RETHINK.usda` |
| Emision de colliders + flag `colision` que se ignoraba | `sim-isaac/export_usd.py` |
| `--sin-sensores`, imports diferidos, `RigidBodyAPI` al Xform padre, `initialize()` tras `reset()`, `SPAWN` medido | `sim-isaac/tata_sim.py` |

Pendiente, por orden:

1. **Renombrar los niveles del CLI.** `tata_sim.py` usa `scrappy|industrial|produccion|maximo`
   y el `CLAUDE.md` dice explicitamente que nunca se use "scrappy". El CLI contradice al
   documento. Son ~10 lineas.
2. **Fase 2: articulacion.** Direccion trasera, mastil prismatico, uñas. La cinematica ya
   esta validada en `sim-web/` — se porta, no se inventa. Los encoders van aca, no en el
   dict `SENSORES`: no trazan rayos, se leen del estado del joint, y por eso **no gastan VRAM**.
3. **Deriva con LiDAR** una vez que la escena abra.

### Dos hallazgos que contradicen lo escrito en `docs/`

Medidos, no opinados. Reproducibles con `analisis/analisis_degeneracion.py`:

- **Lo que restringe el eje del pasillo es la pared del fondo, no los montantes del rack.**
  Con las tapas a la vista, el relieve casi no importa: de 15 cm a 0 cm el sigma longitudinal
  apenas va de 0.14 a 0.18 cm. Sin tapas y con relieve bajo, la matriz de informacion se
  vuelve **singular**. El script por defecto mete paredes a 4.5 m de cada extremo, y por eso
  no reproduce la tabla que quedo escrita.
- **El precipicio esta entre 15 y 12 m de alcance efectivo.** Arriba de 15 m no pasa nada con
  ningun relieve. Consecuencia para el BOM: un blanco retrorreflectivo en cada cabecera de
  pasillo vale mas que marcadores repartidos a lo largo, porque replica la restriccion que ya
  funciona.

### Isaac Sim

No esta instalado. Se descargo a medias en Windows y se borro: el enlace daba 0.4 MB/s para
un zip de 10.6 GB. **Se va a instalar en Linux.** Version 6.0.1, `python.bat` en Windows /
`python.sh` en Linux. Requisito minimo real: RTX 4080, **16 GB de VRAM**, 32 GB de RAM —
no los 8 GB que decia el contexto viejo. La maquina de maje tiene 8 GB, o sea la mitad
del minimo: correr headless y un LiDAR por corrida, nunca varios simultaneos.

Primer arranque:

```bash
./python.sh sim-isaac/tata_sim.py --sin-sensores
```

La primera vez compila shaders y puede tardar 10-40 min con la ventana aparentemente
colgada. No matarlo.
