# ─────────────────────────────────────────────────────────────────────────────
# Kit TaTa sobre Mitsubishi EDR18N2 · escala de madurez del hardware
#
# El EDR ya trae cosas que en un contrabalanceado había que comprar:
# cámara en las uñas, mando electrohidráulico proporcional (reach, elevación,
# desplazador, inclinación), tracción AC con controlador, y dirección eléctrica.
# En esta máquina el retrofit INTERCEPTA señales; casi no pone actuadores.
# ─────────────────────────────────────────────────────────────────────────────
NIV = ['Banco', 'Piloto', 'Serie', 'Flota', 'Homologado']

# (módulo, componente, [(desc, precio) × 5], nota)
D = [
("Cómputo","Módulo de cómputo IA",[
  ("Jetson Orin Nano 8 GB devkit",399),("Jetson Orin NX 16 GB",999),
  ("Jetson Orin NX 16 GB",999),("Jetson AGX Orin 32 GB",1799),
  ("2× AGX Orin 64 GB redundante",4600)],""),
("Cómputo","Carrier board",[
  ("Devkit carrier",0),("Industrial -40/+85, GMSL2, CAN",450),
  ("Industrial -40/+85, GMSL2, CAN",450),("+ alimentación redundante",780),
  ("Custom con watchdog y doble bus",1400)],""),
("Cómputo","Almacenamiento",[("NVMe consumo 512 GB",60),("NVMe industrial 1 TB",140),
  ("NVMe industrial 1 TB",140),("NVMe industrial 2 TB SLC",340),("RAID 1 doble NVMe",700)],""),
("Cómputo","Gabinete",[("Caja comercial IP54",120),("Aluminio IP54 + silentblocks",280),
  ("Aluminio IP54 + silentblocks",280),("IP66 mecanizado con disipador",620),
  ("IP67 con control térmico activo",1300)],""),
("Cómputo","Convertidor DC-DC",[("No aislado 150 W",70),("Aislado 300 W",210),
  ("Aislado 300 W",210),("Aislado redundante",480),("Doble redundante con monitoreo",950)],
  "el EDR es de 24/48 V: hace falta aislarlo del bus de tracción"),
("Cómputo","UPS de retención",[("Batería 12 V sellada",60),("Supercap 24 V",160),
  ("Supercap 24 V",160),("Supercap + BMS",380),("Doble bus con transferencia",820)],""),
("Cómputo","Protección eléctrica",[("Fusiblera básica",60),("Fusiblera + supresores + contactor",180),
  ("Fusiblera + supresores + contactor",180),("+ monitoreo de aislamiento",460),
  ("+ registro de eventos",900)],""),

("Navegación","LiDAR 3D",[("Livox Mid-360",749),("Livox Mid-360",749),
  ("Livox Mid-360",749),("RoboSense Helios / Ouster OS0",4500),
  ("Ouster OS1-64 + redundante",12000)],"desde el Banco, sin LiDAR no se prueba nada"),
("Navegación","IMU",[("BNO085",35),("Industrial 9-DOF",150),("Industrial 9-DOF",150),
  ("MEMS táctico ADIS16505",1200),("FOG táctico redundante",4000)],""),
("Navegación","Odometría de tracción",[("Lectura CAN del controlador",0),("Lectura CAN",0),
  ("Encoder propio de respaldo",180),("Absoluto SSI sellado",420),
  ("Absoluto redundante 2 canales",980)],"el controlador AC del EDR ya publica velocidad"),
("Navegación","Ángulo de dirección",[("Lectura del EPS por CAN",0),("Lectura del EPS por CAN",0),
  ("Encoder absoluto propio",320),("Absoluto redundante",760),
  ("Redundante certificado SIL 2",1600)],"la dirección del EDR ya es eléctrica y sabe su ángulo"),
("Navegación","Marcadores fiduciales",[("Vinilo impreso",80),("Reflectivos AprilTag, kit 60",180),
  ("Reflectivos AprilTag, kit 60",180),("Retroreflectivos industriales",480),
  ("Reflectores SICK certificados",1200)],""),

("Visión","Cámara de uñas",[("La que ya trae el EDR",0),("La que ya trae el EDR",0),
  ("Global shutter GMSL2 propia",380),("GMSL2 IP67 + iluminador",780),
  ("Par estéreo IP69K",1900)],"AHORRO: el EDR viene con cámara en las uñas de fábrica"),
("Visión","Cámara de mástil",[("USB 5 MP",180),("Basler dart 5 MP + iluminador",520),
  ("Basler dart 5 MP + iluminador",520),("Lector de código industrial",900),
  ("Lector Cognex / SICK certificado",2400)],"sube con el carro: es la que hace el inventario"),
("Visión","Cámara de profundidad frontal",[("Orbbec Gemini 335",250),("RealSense D455",400),
  ("RealSense D455",400),("Estéreo industrial GMSL",1400),
  ("Estéreo industrial redundante",3200)],""),
("Visión","Cámara de respaldo lateral",[("Ninguna",0),("Ninguna",0),
  ("Industrial IP67 150°",260),("IP69K GMSL2",540),("Par redundante",1150)],
  "el pasillo de 3 m deja 9 cm de holgura: ver el costado vale"),

("Carga","Altura del carro",[("Lectura del indicador del EDR",0),("Encoder de cable 0–8 m",350),
  ("Encoder de cable 0–8 m",350),("Encoder IP67 redundante",820),
  ("Redundante certificado",1800)],"alturas discretas: basta con saber en qué nivel está"),
("Carga","Presión hidráulica",[("Ninguno",0),("Ninguno",0),
  ("IFM 0–250 bar 4-20 mA",180),("IFM con diagnóstico IO-Link",360),
  ("Doble transductor redundante",780)],
  "sólo desde Serie, y para PESO, no para saber si topó: eso lo ve la cámara"),
("Carga","Presencia de carga",[("Sensor inductivo",40),("Réflex IP67",90),("Réflex IP67",90),
  ("Réflex IP69K con diagnóstico",210),("Doble canal certificado",520)],""),
("Carga","Posición del desplazador",[("Ninguna, lazo abierto",0),("Potenciómetro lineal",90),
  ("Encoder lineal magnético",280),("Encoder IP67",520),("Redundante",1100)],
  "±12 cm de recorrido: es el margen de alineación, hay que medirlo"),

("Actuación","Placa de intercepción",[("Ninguna, teleoperado por consola",0),
  ("Una placa: dirección + tracción + hidráulica",270),
  ("Misma placa, versión sellada",340),
  ("Doble placa redundante + diagnóstico",980),
  ("Certificada SIL 2 con canal cruzado",4200)],
  "PIEZAS, no ingeniería: MCU, CAN aislado, DAC, ADC, mux y drivers de válvula. BOM real $198."),
("Actuación","Módulo CAN del fabricante",[("Ninguno",0),("Ninguno — se emula por la placa",0),
  ("Gateway oficial si Mitsubishi lo abre",900),("Integración firmware con fabricante",2800),
  ("Controlador de tracción SIL 2",6500)],
  "sólo si conviene comprar el camino oficial en vez de emular"),
("Actuación","Freno",[("El regenerativo del propio EDR",0),("Regenerativo + corte de tracción",0),
  ("Regenerativo + corte de tracción",0),("Freno de resorte redundante",1900),
  ("Freno eléctrico certificado",4200)],"el EDR frena solo al soltar: el freno mecánico es de estacionamiento"),
("Actuación","Paro de emergencia",[("Seta cableada al contactor",120),
  ("Doble canal + relé de seguridad",450),("Doble canal + relé de seguridad",450),
  ("PNOZmulti + setas certificadas",1100),("Cadena certificada PL e",2400)],
  "desde el Banco: nunca se mueve sin un botón que corte"),
("Actuación","Selector de modo",[("Switch genérico",35),("Llave 3 posiciones",130),
  ("Llave 3 posiciones",130),("Llave con enclavamiento",340),("Enclavamiento certificado",780)],""),

("Seguridad","Escáner de seguridad",[("Ninguno",0),("Ninguno",0),("Ninguno",0),
  ("2× SICK nanoScan3 PL d",7000),("3× SICK microScan3",13500)],
  "sólo desde Flota: es la capa que va aparte y no toca la navegación"),
("Seguridad","Controlador de seguridad",[("Ninguno",0),("Ninguno",0),("Ninguno",0),
  ("SICK Flexi Soft",900),("PNOZmulti 2 redundante",3600)],""),
("Seguridad","Velocidad segura",[("Ninguna",0),("Ninguna",0),("Ninguna",0),
  ("SLS certificado",1700),("SLS + SDI + SSM",3400)],""),
("Seguridad","Bumper mecánico",[("Ninguno",0),("Ninguno",0),("Banda sensible frontal",500),
  ("Banda sensible doble canal",950),("Perimetral certificado",2200)],
  "en Serie sí: el taller choca a voluntad y hay que absorberlo"),
("Seguridad","Baliza y zona azul",[("Torreta genérica",45),("Torreta + proyector azul",270),
  ("Torreta + proyector azul",270),("IP69K",800),("Certificada con autodiagnóstico",1500)],""),

("Conectividad","Router",[("Comercial WiFi",120),("Teltonika industrial 5G",400),
  ("Teltonika industrial 5G",400),("Doble SIM con failover",780),("Redundante 5G privado",1900)],""),
("Conectividad","Antenas",[("Genéricas magnéticas",30),("Taoglas 2×5G + 2×WiFi",90),
  ("Taoglas 2×5G + 2×WiFi",90),("Industriales IP67",220),("Diversidad MIMO",480)],""),

("Interfaz","Pantalla",[("Tablet Android industrial",200),("Panel 10\" IP65",350),
  ("Panel 10\" IP65",350),("IP66 táctil con guantes",780),("HMI certificada redundante",1800)],""),
("Interfaz","Barra de estado LED",[("Tira direccionable",40),("Tira industrial",80),
  ("Tira industrial",80),("Perimetral IP67",190),("Perimetral con zonas",420)],""),

("Instalación","Arnés de cableado",[("Genérico con conectores",200),("M12 apantallado a medida",520),
  ("M12 apantallado a medida",520),("Certificado con trazabilidad",1200),
  ("Doble arnés redundante",2600)],""),
("Instalación","Soportes de montaje",[("Universales",250),("Mecanizados a medida",640),
  ("Mecanizados a medida",640),("+ análisis de vibración",1500),("Validados por FEA",3500)],""),
("Instalación","Consumibles y sellado",[("Prensaestopas básicos",60),("Prensaestopas + termocontraíble",130),
  ("Prensaestopas + termocontraíble",130),("Sellado IP67 certificado",280),
  ("Trazabilidad de lote",600)],""),
]
tot = [sum(c[2][i][1] for c in D) for i in range(5)]
print("| Módulo | Componente | " + " | ".join(NIV) + " |")
print("|---|---|" + "---|"*5)
for m,c,o,nota in D:
    print(f"| {m} | {c} | " + " | ".join(f"{d} · ${v:,}" for d,v in o) + " |")
print("| | **TOTAL** | " + " | ".join(f"**${t:,}**" for t in tot) + " |")
print()
for n,t in zip(NIV,tot): print(f"{n:12} ${t:,}")
ahorro = sum(1 for c in D if 'AHORRO' in c[3])
print(f"\nlíneas donde el EDR ya trae la función: {ahorro}")
