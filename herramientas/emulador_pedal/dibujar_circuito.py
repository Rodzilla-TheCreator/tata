# genera herramientas/emulador_pedal/circuito_modulos.svg  (python herramientas/emulador_pedal/dibujar_circuito.py)
O=[]
def a(s): O.append(s)
W,H=1180,960
CAFE='#8b5a2b'; AZUL='#1f63d6'; BLANCO='#8a9099'; NEGRO='#111'; ROJO='#d0312d'; GND='#444'; GPIO='#e07b00'
def line(pts,c,w=3,dash=None):
    d='M'+' L'.join(f'{x},{y}' for x,y in pts)
    a(f'<path d="{d}" fill="none" stroke="{c}" stroke-width="{w}" stroke-linejoin="round"{" stroke-dasharray=%s"%chr(34)+dash+chr(34) if dash else ""}/>')
def vhop(x,y0,y1,hops,c,w=3):
    d=f'M{x},{y0}'
    for yc in sorted(hops):
        d+=f' V{yc-7} A7,7 0 0 1 {x},{yc+7}'
    d+=f' V{y1}'
    a(f'<path d="{d}" fill="none" stroke="{c}" stroke-width="{w}"/>')
def hhop(y,x0,x1,hops,c,w=3):
    d=f'M{x0},{y}'
    for xc in sorted(hops):
        d+=f' H{xc-7} A7,7 0 0 1 {xc+7},{y}'
    d+=f' H{x1}'
    a(f'<path d="{d}" fill="none" stroke="{c}" stroke-width="{w}"/>')
def dot(x,y,c='#111'): a(f'<circle cx="{x}" cy="{y}" r="5" fill="{c}"/>')
def term(x,y): a(f'<circle cx="{x}" cy="{y}" r="7" fill="#fff" stroke="#333" stroke-width="2"/>')
def t(x,y,s,size=14,anchor='start',w='normal',c='#111',it=False):
    a(f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}" font-weight="{w}" fill="{c}"{" font-style=%sitalic%s"%(chr(34),chr(34)) if it else ""}>{s}</text>')
def resv(x,y0,y1,c):
    n=6; h=(y1-y0)/n; pts=[(x,y0)]
    for i in range(n): pts.append((x+(8 if i%2==0 else -8), y0+h*(i+0.5)))
    pts.append((x,y1)); line(pts,c,2.5)
def gapv(x,y0,y1,c):   # jumper abierto: dos bornes, se pone uno de los dos
    a(f'<circle cx="{x}" cy="{y0}" r="5" fill="#fff" stroke="{c}" stroke-width="2.5"/>')
    a(f'<circle cx="{x}" cy="{y1}" r="5" fill="#fff" stroke="{c}" stroke-width="2.5"/>')
    a(f'<path d="M{x-9},{y0+4} Q{x-16},{(y0+y1)/2} {x-9},{y1-4}" fill="none" stroke="#999" stroke-width="1.5" stroke-dasharray="3 3"/>')

a(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Helvetica, Arial, sans-serif">')
a(f'<rect width="{W}" height="{H}" fill="#fff"/>')
t(30,40,'Emulador del pedal de hombre muerto · versión con dos módulos de relé de 1 canal',22,w='bold')
t(30,64,'herramientas/emulador_pedal/LEEME.md · relés dibujados SIN ACTIVAR (= ESP muerto, paro apretado o sin latido) · 17-nov-2026',13,c='#555')

# zona del equipo / del ESP
a('<rect x="20" y="88" width="770" height="590" rx="10" fill="#f6f3ee" stroke="#d8cfc0"/>')
t(34,110,'LADO DEL EQUIPO · todo el voltaje sale de los pines 1 y 3 del propio equipo',13,w='bold',c='#6b5537')
a('<rect x="795" y="88" width="365" height="590" rx="10" fill="#eef3f8" stroke="#c9d6e4"/>')
t(808,110,'LADO DEL ESP · GND = amarillo',13,w='bold',c='#36506e')

# conector XS160
a('<rect x="40" y="128" width="130" height="530" rx="8" fill="#fff" stroke="#333" stroke-width="2"/>')
t(105,360,'XS160',16,'middle','bold'); t(105,378,'conector suelto',12,'middle',c='#555'); t(105,393,'del equipo, pines 1–4',12,'middle',c='#555')
P={1:(170,160),2:(170,260),4:(170,490),3:(170,630)}
nom={1:('1 · café','+'),2:('2 · blanco','salida A'),4:('4 · negro','salida B'),3:('3 · azul','−')}
for k,(x,y) in P.items():
    term(x,y); t(x-14,y-4,nom[k][0],13,'end','bold'); t(x-14,y+12,nom[k][1],12,'end',c='#555')

# módulos
def modulo(y,nombre):
    a(f'<rect x="520" y="{y}" width="240" height="140" rx="8" fill="#fdecea" stroke="{ROJO}" stroke-width="2"/>')
    t(688,y+24,nombre,15,'middle','bold',c='#8e1f1b')
    t(688,y+44,'1 canal 5V',11,'middle',c='#8e1f1b')
    t(688,y+58,'SRD-05VDC',11,'middle',c='#8e1f1b')
    t(688,y+76,'jumper H/L',11,'middle','bold',c='#8e1f1b')
    t(688,y+90,'en H',11,'middle','bold',c='#8e1f1b')
    yNO,yCOM,yNC=y+30,y+70,y+110
    for yy,s in ((yNO,'NO'),(yCOM,'COM'),(yNC,'NC')): term(520,yy); t(532,yy+5,s,12,w='bold')
    # contacto: COM unido a NC (sin activar)
    line([(575,yCOM),(605,yCOM)],'#333',2.5); line([(605,yCOM),(618,yNC-14)],'#333',2.5)
    a(f'<circle cx="605" cy="{yCOM}" r="3" fill="#333"/>')
    line([(575,yNC),(622,yNC),(622,yNC-12)],'#333',2.5); line([(575,yNO),(622,yNO),(622,yNO+14)],'#333',2.5)
    for yy,s in ((yNO,'IN'),(yCOM,'DC−'),(yNC,'DC+')): term(760,yy); t(748,yy+5,s,12,'end',w='bold')
    return yNO,yCOM,yNC
A=modulo(190,'Módulo A'); B=modulo(420,'Módulo B')
# A: NO 220, COM 260, NC 300 ; B: NO 450, COM 490, NC 530

# riel + (café): pin1 -> x=230 vertical hasta 580 ; arriba hasta x=450
line([P[1],(420,160)],CAFE,3.5); dot(230,160,CAFE)
vhop(230,160,580,[260,490],CAFE,3.5)
line([(230,580),(450,580)],CAFE,3.5)
# riel − (azul): pin3 -> x=470 vertical hasta NC A
line([P[3],(470,630)],AZUL,3.5)
vhop(470,630,300,[],AZUL,3.5)  # placeholder, se redibuja con saltos abajo
O.pop()
d=f'M470,630 V{530+7} A7,7 0 0 0 470,{530-7} V{490+7} A7,7 0 0 0 470,{490-7} V300'
a(f'<path d="{d}" fill="none" stroke="{AZUL}" stroke-width="3.5"/>')
line([(470,300),(520,300)],AZUL,3.5); dot(470,300,AZUL)   # NC A al −
line([(470,450),(520,450)],AZUL,3.5); dot(470,450,AZUL)   # NO B al −
# salidas
line([P[2],(520,260)],BLANCO,4)    # pin 2 -> COM A (cruza la + en x=230 con salto ya hecho)
line([P[4],(520,490)],NEGRO,3.5)    # pin 4 -> COM B
# J1: + (160) -> nodo 212 -> NO A
line([(330,160),(330,176)],CAFE,3); gapv(330,181,199,CAFE); line([(330,204),(330,212)],'#7a4a1f',3); dot(330,160,CAFE)
line([(420,160),(420,164)],CAFE,3); resv(420,164,190,CAFE); gapv(420,195,206,CAFE); dot(420,160,CAFE)
line([(330,212),(495,212),(495,220),(520,220)],'#7a4a1f',3); dot(420,212,'#7a4a1f')
t(340,195,'directo',11,c='#6b5537'); t(432,182,'47 kΩ',11,w='bold',c='#6b5537')
t(372,238,'J1: poné UNO de los dos',11,'middle',w='bold',c='#6b5537')
# J2: + (580) -> NC B (530)
line([(330,580),(330,566)],CAFE,3); gapv(330,561,545,CAFE); line([(330,540),(330,530)],'#7a4a1f',3); dot(330,580,CAFE)
line([(420,580),(420,570)],CAFE,3); resv(420,570,548,CAFE); gapv(420,543,531,CAFE); dot(420,580,CAFE)
line([(420,526),(420,515),(330,515),(330,530)],'#7a4a1f',3)
line([(420,515),(500,515),(500,530),(520,530)],'#7a4a1f',3)
O.pop(); O.pop()
# redibujo J2 más limpio: nodo en y=515
line([(330,540),(330,515),(500,515),(500,530),(520,530)],'#7a4a1f',3)
line([(420,526),(420,515)],'#7a4a1f',3); dot(420,515,'#7a4a1f')
t(337,560,'directo',11,c='#6b5537'); t(430,566,'47 kΩ',11,w='bold',c='#6b5537')
t(372,606,'J2: poné UNO de los dos',11,'middle',w='bold',c='#6b5537')
t(250,660,'arrancá con J1 y J2 en «47 kΩ»',12,w='bold',c='#6b5537')

# lado del ESP: buses
IN,GN,V5=830,880,930
line([(760,220),(IN,220)],GPIO,3); line([(760,450),(IN,450)],GPIO,3); dot(IN,450,GPIO)
vhop(IN,220,700,[],GPIO,3)
line([(760,260),(GN,260)],GND,3)
O.pop(); hhop(260,760,GN,[IN],GND,3)
line([(760,490),(GN,490)],GND,3); O.pop(); hhop(490,760,GN,[IN],GND,3); dot(GN,490,GND)
vhop(GN,260,700,[],GND,3)
hhop(300,760,V5,[IN,GN],ROJO,3); hhop(530,760,V5,[IN,GN],ROJO,3); dot(V5,530,ROJO)
vhop(V5,300,600,[],ROJO,3)
t(945,360,'IN, DC− y DC+',12,w='bold',c='#36506e')
t(945,376,'de A y B van juntos',12,c='#36506e')
t(945,400,'(en cada módulo: IN arriba,',11,c='#36506e',it=True)
t(945,414,'DC− al medio, DC+ abajo)',11,c='#36506e',it=True)
# paro de hongo NC entre 600 y 650 (contacto cerrado, se abre al apretar)
term(V5,600); term(V5,650)
line([(V5,600),(V5+16,600),(V5+16,650),(V5,650)],ROJO,3)
line([(V5+16,625),(V5+40,625)],'#333',2.5); a(f'<path d="M{V5+40},603 A22,22 0 0 1 {V5+40},647 Z" fill="{ROJO}"/>')
line([(V5,650),(V5,700)],ROJO,3)
t(V5+70,612,'PARO de hongo',13,w='bold',c=ROJO); t(V5+70,628,'contacto NC (11–12)',11.5,c=ROJO); t(V5+70,644,'apretado: suelta A y B',11.5,c=ROJO)
# ESP
a('<rect x="805" y="700" width="345" height="90" rx="8" fill="#fff" stroke="#333" stroke-width="2"/>')
for x,s,c in ((IN,'GPIO27',GPIO),(GN,'GND',GND),(V5,'5V / VIN',ROJO)):
    term(x,700); t(x,722,s,12,'middle','bold',c)
t(978,752,'ESP32 · watchdog 200 ms, rearme GPIO32',12,'middle',c='#333')
t(978,770,'BANCO, sin ESP: IN a 5 V con un cable',12,'middle',w='bold',c='#333')

# tabla y notas
y0=720
a(f'<rect x="20" y="{y0-12}" width="770" height="236" rx="10" fill="#fafafa" stroke="#ddd"/>')
t(34,y0+10,'Qué ve el equipo',15,w='bold')
rows=[('','pin 2 (blanco)','pin 4 (negro)','estado'),
      ('relés SIN activar (IN bajo, paro o ESP muerto)','− (bajo)','+ por J2 (alto)','tiene que ser «suelto»'),
      ('relés activados (IN alto)','+ por J1 (alto)','− (bajo)','«pisado»')]
xs=[34,370,505,640]
for i,r in enumerate(rows):
    for x,s in zip(xs,r): t(x,y0+36+i*22,s,12.5,w='bold' if i==0 else 'normal')
notas=['• Siempre una salida alta y la otra baja: nunca 0/0 ni 1/1 (evento 1.06). El + nunca toca el −: cada salida va al COM.',
       '• Si en el equipo «sin activar» resulta «pisado», se cruzan 2 y 4 en la bornera: sin activar SIEMPRE = suelto.',
       '• Módulo activo en bajo o sin jumper H/L: NO sirve (ESP muerto = pisado). Control: IN al aire → relé suelto.',
       '• Banco: fuente 12 V, + al pin 1 y − al pin 3; multímetro en 2 y 4 contra 3. 47 kΩ con 10 kΩ de carga ≈ 2.1 V.',
       '• Equipo: los Dupont no van al XS160. Primero medir pines 1, 2, 4 contra 3 (llave ON, sensor desconectado).']
for i,s in enumerate(notas): t(34,y0+112+i*21,s,12.2,c='#333')
a(f'<text x="{W-20}" y="{H-14}" font-size="11" text-anchor="end" fill="#999">TaTa · Montasa</text>')
a('</svg>')
open('/home/user/tata/herramientas/emulador_pedal/circuito_modulos.svg','w',encoding='utf-8').write('\n'.join(O))
