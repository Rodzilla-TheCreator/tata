# Las máquinas y el entorno

Cómo está armado el fierro con el que se trabaja TaTa, cómo se llegó ahí, y las trampas que
costaron horas. **Escrito el 28-ago-2026.**

Son **tres sujetos** aunque haya dos computadoras: `i3`, `maquinon` y `superspeed`. Se usan
esos nombres siempre.

## Los tres

| | i3 | maquinon | superspeed |
|---|---|---|---|
| Qué es | Dell Inspiron 15 3511 | ASUS ROG Zephyrus M16 GU604VI | **El SSD USB de 1 TB**, no una computadora |
| Sistema | Windows 11 | Windows 11 Home | Ubuntu 22.04.5 + XFCE |
| CPU/RAM | specs bajas | 32 GB | (corre en el maquinon) |
| GPU | Intel UHD | Intel Iris Xe + **RTX 4070 Laptop, 8 GB** | la del maquinon |
| Papel | terminal desde donde se trabaja | Windows para jugar | **el entorno del proyecto** |
| Tailscale | 100.77.162.44 | 100.123.1.45 | 100.83.146.2 |

`maquinon` y `superspeed` son **el mismo fierro arrancando de discos distintos**, así que nunca
están en línea a la vez. La i3 es el reflejo de la luna; los otros dos son dos soles que no
alumbran juntos.

La identidad de `superspeed` en Tailscale **viaja con el SSD**, no con la máquina donde se
enchufe.

### Cómo se llega a cada una

```bash
ssh maquinon            # puerto 2222, entra a WSL2
ssh rodz@superspeed     # Linux nativo
```

- `sudo` en superspeed es **NOPASSWD** (`/etc/sudoers.d/010-rodz`). Aceptable porque sshd es
  **solo llave**: `PasswordAuthentication no`. Para abusarlo hace falta la llave privada de la i3.
- La i3 tiene **ssh-agent deshabilitado** y habilitarlo pide admin, así que no se puede
  reenviar la llave con `ssh -A`. Cada máquina necesita su propia llave en GitHub.

Llaves públicas registradas en GitHub:

```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICRmOxkl7bgHuisZA22PAqfcKKRazqGgBpKFuyrjOiuu rodz@flotas-i3
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDLnqazRpP+p0gWnXh4zKceNOCRiiZeGwsf8NxxrPAKT rodrigo.j.monterroso@gmail.com
```

---

# superspeed

## Cómo se construyó

**Ubuntu 22.04.5 instalado por `debootstrap`, enteramente en remoto desde la i3, sin arrancar
ningún instalador.** El único momento de presencia física fue un doble clic para borrar el disco.

Se eligió **22.04 y no 24.04 ni 26.04** por dos razones: Isaac Sim solo soporta 22.04 y 24.04,
y el equipo de Botoni habla en términos de 22.04 con ROS 2 Humble. 22.04 va con Humble; 24.04
va con Jazzy, y cambiar implicaría portar.

### El disco

Serial **`DD564198838A3`**. **Usar siempre el serial como guarda en cualquier script
destructivo, nunca el número de disco** — el número cambia al reconectar.

| Partición | Tamaño | Formato | Etiqueta |
|---|---|---|---|
| 1 | 1 GiB | FAT32 | `SSPD-ESP` |
| 2 | 952.9 GiB | ext4 | `superspeed` |

**Sin LUKS**, por decisión: el disco no sale del escritorio y no se quería un paso extra diario.

### El procedimiento, en orden

```bash
# 1. Borrar y pasar a GPT — desde Windows, con UAC
Clear-Disk -Number 1 -RemoveData -RemoveOEM -Confirm:$false
Initialize-Disk -Number 1 -PartitionStyle GPT

# 2. Prestarle el disco crudo a WSL2 — NO necesita elevación
wsl --mount "\\.\PHYSICALDRIVE1" --bare      # se devuelve con: wsl --unmount

# 3. Particionar (dentro de WSL, como root)
sgdisk --zap-all /dev/sde
sgdisk -n1:0:+1G -t1:ef00 -c1:ESP            /dev/sde
sgdisk -n2:0:0   -t2:8300 -c2:superspeed-root /dev/sde
mkfs.vfat -F32 -n SSPD-ESP /dev/sde1
mkfs.ext4 -L superspeed    /dev/sde2

# 4. Sistema base
debootstrap --arch=amd64 --components=main,universe jammy /mnt/superspeed \
            http://archive.ubuntu.com/ubuntu

# 5. Dentro del chroot: kernel, GRUB, red
apt-get install linux-generic linux-generic-hwe-22.04 initramfs-tools \
  grub-efi-amd64 grub-efi-amd64-signed shim-signed efibootmgr \
  network-manager openssh-server sudo locales tzdata

# 6. GRUB PORTÁTIL — la clave de todo
grub-install --target=x86_64-efi --efi-directory=/boot/efi --removable --no-nvram --recheck
```

**`--removable` es lo que hace que funcione.** Deja el arranque en `\EFI\BOOT\BOOTX64.EFI`, que
es la ruta de respaldo que cualquier máquina UEFI busca sola. Por eso arranca en el maquinon y
arrancaría en la i3 sin registrar nada en el firmware de ninguna.

`--no-nvram` es obligatorio: dentro de WSL no hay `efivars` y `efibootmgr` fallaría.

**Verificar que `BOOTX64.EFI` sea el shim firmado**, o Secure Boot no arranca:

```bash
cmp /boot/efi/EFI/BOOT/BOOTX64.EFI /usr/lib/shim/shimx64.efi.signed.latest
```

### El initramfs tiene que traer USB

La raíz vive en un disco USB, así que el initramfs necesita `usb-storage`, `uas` y `xhci-pci`.
Con `MODULES=most` en `/etc/initramfs-tools/initramfs.conf` entran solos. Verificar:

```bash
lsinitramfs /boot/initrd.img-6.8.0-138-generic | grep -E "usb-storage|uas|xhci"
```

## El arranque

**El menú de arranque del maquinon es ESC, no F8.**

El firmware **no** usa la entrada genérica «Removable Device» para este SSD: le creó la suya
propia. Esto solo se supo mirando `efibootmgr` desde Linux nativo, y tumbó un script que
apuntaba al GUID equivocado.

```
BootCurrent: 0004
BootOrder:   0004,0000,0003,0002
Boot0000* Windows Boot Manager   \EFI\Microsoft\Boot\bootmgfw.efi
Boot0004* UEFI OS                \EFI\BOOT\BOOTX64.EFI      <- superspeed
```

Orden puesto desde Linux:

```bash
sudo efibootmgr -o 0004,0000,0003,0002
sudo efibootmgr -t 3
```

Con el SSD conectado arranca superspeed. Sin el SSD, el firmware no encuentra `Boot0004` y cae
solo a Windows. **Verificado.**

### Volver a Windows con un clic

`/usr/local/bin/ir-a-windows` busca la entrada de Windows, la pone como `BootNext` —un solo
arranque— y reinicia. El siguiente arranque vuelve a superspeed sin tocar nada.

```bash
sudo ir-a-windows
```

Hay lanzador en el escritorio y en el menú de aplicaciones. El sudoers lo permite sin clave
(`/etc/sudoers.d/020-ir-a-windows`).

**XFCE trae los iconos de escritorio apagados por defecto.** Se prenden con
`xfconf-query -c xfce4-desktop -p /desktop-icons/style -n -t int -s 2`.

## NVIDIA y Secure Boot — esto se repite en cada kernel

**Secure Boot se queda encendido.** Apagarlo rompe Valorant en Windows, porque Vanguard lo
exige. Todo lo que sigue existe para no tener que apagarlo.

**Cuatro pasos, y los cuatro hacen falta:**

**1. Blacklistear nouveau a mano.** El paquete de NVIDIA **no lo hace solo**. Sin esto, nouveau
sobre una GPU Ada cuelga el escritorio con pantalla negra y cursor congelado — fue lo que pasó
en el primer arranque.

```bash
printf 'blacklist nouveau\noptions nouveau modeset=0\n' > /etc/modprobe.d/blacklist-nouveau.conf
```

**2. Módulos prefirmados por Canonical**, no los de DKMS. Con Secure Boot, el módulo DKMS da
`modprobe: ERROR: could not insert 'nvidia': Key was rejected by service`.

```bash
apt install nvidia-driver-595 linux-modules-nvidia-595-generic-hwe-22.04
```

**3. Sacar el de DKMS, porque tiene precedencia.** Este es el paso que no es obvio:
`/lib/modules/.../updates/dkms/nvidia.ko` gana sobre `/lib/modules/.../kernel/nvidia-595/nvidia.ko`,
así que aunque instales los firmados, `modprobe` sigue tomando el que no carga.

```bash
dkms remove nvidia/595.84 --all
depmod -a
```

**4. Cargar la pila completa.** Solo `nvidia` no alcanza para Vulkan: hacen falta también
`nvidia_modeset`, `nvidia_uvm` y `nvidia_drm`.

```bash
printf 'nvidia\nnvidia_modeset\nnvidia_uvm\nnvidia_drm\n' > /etc/modules-load.d/nvidia.conf
echo 'options nvidia-drm modeset=1' > /etc/modprobe.d/nvidia-drm.conf
```

### Cómo se verifica que quedó bien

```bash
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
#  NVIDIA GeForce RTX 4070 Laptop GPU, 8188 MiB, 595.84
vulkaninfo --summary | grep deviceName
#  tiene que aparecer la NVIDIA, no solo Intel y llvmpipe
mokutil --sb-state
#  SecureBoot enabled
```

**Vulkan es la prueba que importa**, porque es lo que Isaac Sim exige y lo que WSL2 no podía dar.

## La suspensión mata el acceso remoto

superspeed se suspendió tres veces en una noche y dejó de ser alcanzable. Bloqueada así:

```bash
systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target
```

Más `HandleLidSwitch=ignore` e `IdleAction=ignore` en `/etc/systemd/logind.conf.d/10-superspeed.conf`.

**Es la versión bruta: ahora no duerme nunca, ni con batería.** Para el escenario de escritorio
está bien. Si algún día se usa con batería, revertir con
`systemctl unmask sleep.target suspend.target`.

## Red

`NetworkManager` en Ubuntu viene con **todo lo cableado sin administrar**:
`/usr/lib/NetworkManager/conf.d/10-globally-managed-devices.conf` dice
`unmanaged-devices=*,except:type:wifi,except:type:gsm,except:type:cdma`. En una instalación de
escritorio viene un override en `/etc`; con `debootstrap` no llega. Se arregla:

```bash
printf '[keyfile]\nunmanaged-devices=none\n' > /etc/NetworkManager/conf.d/10-globally-managed-devices.conf
systemctl restart NetworkManager
```

Adaptador USB-ethernet **ASIX AX88179B**, lo toma `cdc_ncm`. **Al 28-ago-2026 no sirve**: linkea
a **100 Mb half duplex** con dos cables distintos, y a veces ni responde el DHCP. 100/half es el
fallback del estándar cuando **falla la autonegociación**, lo que apunta a que el puerto del otro
lado está forzado a mano. WiFi da 61 Mbps contra 30 del cable, así que la métrica del cableado se
subió a 700 para que gane el WiFi. `cdc_ncm` no soporta `ethtool -r` ni forzar velocidad.

## Qué hay instalado

| | |
|---|---|
| Kernels | 5.15.0-190 y **6.8.0-138 (HWE)** |
| Escritorio | **XFCE** + LightDM |
| GPU | nvidia-driver-595 (595.84) |
| ROS 2 | **Humble**, 288 paquetes, con `rviz2` y `colcon` |
| Gazebo | **Fortress 6.18.0** — el binario es `ign gazebo`, no `gz sim` |
| Puente | `ros_gz`, `ros_gz_bridge`, `ros_gz_image`, `ros_gz_interfaces`, `ros_gz_sim` |
| Isaac Sim | 6.0.1, zip de 12.12 GiB, MD5 verificado |
| Claude Code | 2.1.250 en `~/.local/bin/claude` |
| Navegador | Firefox 154 del repo de Mozilla, **no snap** |

**Por qué XFCE y no GNOME:** xrdp funciona mejor, Isaac Sim prefiere Xorg sobre Wayland, y el
compositor de GNOME se queda con VRAM que hace falta cuando solo hay 8 GB.

---

# maquinon

Windows 11 Home con WSL2 Ubuntu 22.04. Es donde vive Windows para jugar y desde donde se prestó
el disco para construir superspeed.

- `sshd`, `Tailscale` y `SunshineService` son **servicios en Automatic**, así que arrancan antes
  del login. Con la máquina en pantalla de bloqueo hay red, SSH y streaming.
- **Dos rutas SSH:** el puerto **2222** es sshd nativo dentro de WSL2 vía `netsh portproxy` y
  sirve para todo. El **22** es sshd de Windows con `DefaultShell=wsl.exe` y **solo sirve
  interactivo** — rompe con comandos y scp porque Windows invoca la shell como `shell -c`.
- El portproxy del 2222 se cae tras cada reboot y lo reactiva la tarea `WSL2-SSH-PortProxy`,
  que tarda hasta 5 min. **Se arreglaría de raíz** poniendo `networkingMode=mirrored` en
  `.wslconfig`, pero puede incomodar a docker-desktop.
- **`wsl --mount` no necesita elevación.** El único UAC de todo el proceso fue el borrado del disco.
- **Faltan `node` y `npm`**, que hacen falta para `presentaciones/deck_*.js` y para el
  `three.min.js` de `build_sec.py` y `build_actual.py`.
- **RDP no existe**: es Windows Home. El equivalente gráfico es Moonlight/Sunshine.

## Canales para no copiar y pegar entre máquinas

**Sesión tmux compartida `tata`.** Se ve igual desde las dos máquinas y sobrevive desconexiones.

```bash
tmux attach -t tata                        # en maquinon
ssh -t maquinon tmux attach -t tata        # desde la i3
```

**tmux no trae el mouse activado.** Sin `set -g mouse on` la rueda manda flechas al shell. Ya
está puesto en `~/.tmux.conf` con `history-limit 100000`.

**Carpeta `tata-acciones`** en `C:\Users\rodm_\Desktop\`. Ahí van los `.cmd` que necesitan UAC;
se auto-elevan con doble clic y se avisan por tmux. Convención: numerados por orden.

**Los procesos lanzados por SSH en Windows no aparecen en el escritorio** — caen en otra sesión.
Para abrir una ventana visible hay que usar una tarea programada con `/it`. Y `wt.exe` desde
WindowsApps es un alias de ejecución que **falla en silencio** en ese contexto: la tarea reporta
éxito y no abre nada. Con `cmd.exe` directo sí funciona.

---

# Trampas que costaron tiempo

- **Los paths de Windows pierden barras** al pasar por ssh → bash → powershell.
  `\\.\PHYSICALDRIVE1` llega como `\.\PHYSICALDRIVE1` y el dispositivo no existe. **Escribir los
  comandos a un archivo `.sh` con heredoc citado (`<< "SH"`) y ejecutar el archivo.** Inline no.
- **`set -o pipefail` mata `tr ... | head -c5`**: `head` cierra la tubería, `tr` muere con
  SIGPIPE y `set -e` aborta. Usar `od -An -N8 -tx1 /dev/urandom | tr -d " \n" | cut -c1-5`.
- **`grep` sin coincidencias devuelve 1** y con `set -e` aborta el script a mitad.
- **`chpasswd` dentro de un chroot** da *Authentication token manipulation error*. Funciona con
  `openssl passwd -6` + `usermod -p HASH`.
- **Nunca correr `du` sobre un chroot con `/proc` bind-montado** — escupe miles de líneas.
- **`winget` se corrompe** (`0x80071130 Fast Cache data not found`) y entonces *cualquier*
  install falla con «no se encontró ningún paquete». Se arregla con `winget source update`.
- **Windows solo pudo encoger C: 2.6 GB** de 926, aun con 125 GB libres, y sin hibernación ni
  pagefile grande. Los archivos inamovibles al final del volumen —probablemente el VHDX de WSL2
  o las shadow copies— lo pinchan. Por eso Linux no fue a una partición del disco interno.

---

# Pendientes

- **Display virtual para Sunshine.** Con dos monitores conectados y uno apagado, DisplayFusion
  mantiene el perfil y las ventanas se abren en el monitor muerto. La salida es darle a Sunshine
  su propio display virtual, que existe siempre. Sin hacer.
- **xrdp** está instalado y habilitado en superspeed, **sin probar** desde la i3.
- **`node` y `npm`** en el WSL2 del maquinon.
- **Isaac Sim** descargado y verificado, falta `./post_install.sh`.
- **El ethernet**, si alguna vez se sabe qué hay del otro lado del cable.
