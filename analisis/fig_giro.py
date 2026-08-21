import numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle

L_REC, FLEN, ANCHO, CARGA_W, REACH, Wa, PAS, CLR = 2.91,1.21,1.054,1.20,0.61,1.797,3.00,0.20
L_EXT, XPIV = L_REC+REACH, 1.91
SURF,INK,INK2,MUT = '#1a1a19','#eceae4','#b4b0a6','#6e6b64'
AZUL,NARANJA,VERDE,ROJO,AMB = '#3987e5','#d95926','#199e70','#e34948','#c98500'
ast = lambda tip: Wa + (tip-XPIV) + CLR

fig = plt.figure(figsize=(13.8,9.6), facecolor=SURF)
gs = fig.add_gridspec(2,2, height_ratios=[1.30,1], hspace=.36, wspace=.14,
                      left=.05, right=.975, top=.80, bottom=.11)

def panel(ax, tip, col, cara_lbl):
    ax.set_facecolor(SURF)
    A = ast(tip); piv = tip-XPIV
    ax.add_patch(Rectangle((-1.6,0),6.6,PAS,color='#212420',zorder=0))
    ax.add_patch(Rectangle((-1.6,-0.55),6.6,0.55,color='#2f5c9e',zorder=1))
    ax.add_patch(Rectangle((-1.6,PAS),6.6,0.55,color='#2f5c9e',zorder=1))
    th = np.linspace(np.radians(-30), np.radians(210), 220)
    ax.plot(Wa*np.cos(th), piv+Wa*np.sin(th), color=AMB, lw=1.6, ls=(0,(5,3)), zorder=3)
    cara = tip-FLEN
    ax.add_patch(Rectangle((-ANCHO/2,0),ANCHO,cara,color='#8a8f96',zorder=4))
    ax.add_patch(Rectangle((-CARGA_W/2,cara),CARGA_W,FLEN,color='#d6d9dd',ec='#5b6470',lw=1,zorder=5))
    ax.plot([0],[piv],'o',ms=8,color=AMB,zorder=6)
    ax.text(-0.78,piv,'pivote',color=AMB,fontsize=9.5,va='center',ha='right')
    y0 = piv+Wa+CLR
    ax.annotate('',(2.75,0),(2.75,y0),arrowprops=dict(arrowstyle='<->',color=col,lw=2.2))
    ax.text(2.90,y0/2,f'Ast {A:.2f} m',color=col,fontsize=14,weight='bold',va='center')
    ax.annotate('',(4.75,0),(4.75,PAS),arrowprops=dict(arrowstyle='<->',color=INK2,lw=1.6))
    ax.text(4.90,PAS/2,f'pasillo\n{PAS:.2f} m',color=INK2,fontsize=11,va='center')
    ax.axhline(y0,color=col,lw=1.3,ls=(0,(3,3)))
    ax.text(-1.55,3.62,cara_lbl,color=INK2,fontsize=10.5)
    ax.set_xlim(-2.2,5.9); ax.set_ylim(-0.75,3.88); ax.set_aspect('equal'); ax.axis('off')

a1 = fig.add_subplot(gs[0,0]); panel(a1,L_REC,VERDE,'punta a 2.91 m del culo · barrido 2.80 m + 20 cm de holgura')
a2 = fig.add_subplot(gs[0,1]); panel(a2,L_EXT,ROJO,'punta a 3.52 m del culo · barrido 3.41 m, no entra')
a1.set_title('Pantógrafo RECOGIDO — cabe',color=VERDE,fontsize=13.5,weight='bold',pad=24)
a2.set_title('Pantógrafo EXTENDIDO — no cabe',color=ROJO,fontsize=13.5,weight='bold',pad=24)

ax = fig.add_subplot(gs[1,:]); ax.set_facecolor(SURF); ax.axis('off')
BAY, H = 1.29, (1.29-1.20)/2
ax.add_patch(Rectangle((0,0),BAY,1.0,fc='#212420',ec='#2f5c9e',lw=2.5,zorder=1))
ax.add_patch(Rectangle((H,0.03),CARGA_W,0.94,fc='#d6d9dd',ec='#5b6470',lw=1.2,zorder=2))
ax.text(BAY/2,0.5,'maxicubo\n1.20 m',ha='center',va='center',color='#2b2f36',fontsize=11,weight='bold',zorder=3)
ax.annotate('',(0,1.15),(H,1.15),arrowprops=dict(arrowstyle='<->',color=AMB,lw=1.8))
ax.annotate('',(H+CARGA_W,1.15),(BAY,1.15),arrowprops=dict(arrowstyle='<->',color=AMB,lw=1.8))
ax.text(H/2,1.26,'4.5 cm',ha='center',color=AMB,fontsize=11,weight='bold')
ax.text(BAY-H/2,1.26,'4.5 cm',ha='center',color=AMB,fontsize=11,weight='bold')
ax.annotate('',(0,-0.24),(BAY,-0.24),arrowprops=dict(arrowstyle='<->',color=INK2,lw=1.5))
ax.text(BAY/2,-0.46,f'bahía {BAY:.2f} m',ha='center',color=INK2,fontsize=11)
ax.annotate('',(2.00,0.50),(2.70,0.50),arrowprops=dict(arrowstyle='<->',color=VERDE,lw=2.6))
ax.text(2.35,0.76,'desplazador ±12 cm',ha='center',color=VERDE,fontsize=12,weight='bold')
ax.text(2.35,0.30,'cubre 2.7 veces\nel error tolerable',ha='center',va='top',color=INK2,fontsize=10.5)
ax.text(3.45,0.92,'LO QUE ESTO SIGNIFICA',color=INK,fontsize=12.5,weight='bold')
for i,t in enumerate([
  'El Ast ya trae adentro los 20 cm de holgura de norma: el barrido real son 2.80 m.',
  'Recogido cabe con holgura normal. Extendido pide 3.41 m de barrido y no existe ese pasillo.',
  'En el pasillo sobran 90 cm por lado del maxicubo. La bahía deja 4.5 cm por lado.',
  'La nav no tiene que alinear perfecto: dentro de ±4.5 cm y el desplazador termina el trabajo.']):
    ax.text(3.45,0.66-i*0.22,'·  '+t,color=INK2,fontsize=11)
ax.set_xlim(-0.35,9.9); ax.set_ylim(-0.62,1.45)

fig.text(0.05,0.965,'EDR18N2 de 2.91 m en pasillo de 3.00 m: la geometría del giro',
         color=INK,fontsize=17,weight='bold',va='top')
fig.text(0.05,0.921,'2.91 m es con el pantógrafo RECOGIDO · extendido son 3.52 m · pivote en el eje de ruedas de carga, a 1.91 m del culo',
         color=MUT,fontsize=11,va='top')
fig.text(0.05,0.888,'Pivote comprobado por dos caminos: entre ejes de ficha (1.562 + 0.35 = 1.91 m) y despejarlo de que la máquina SÍ trabaja hoy en 3.00 m.  El Ast incluye 20 cm de holgura de norma.',
         color=MUT,fontsize=10,va='top')
fig.text(0.05,0.055,'REGLA:  girar recogido, extender sólo cuando ya está alineado.',
         color=AMB,fontsize=13,weight='bold',va='center')
fig.text(0.05,0.022,'Un Baoli KBE 20 pide 3.82 m: no entra de ninguna forma.',color=MUT,fontsize=11,va='center')
plt.savefig('geometria_giro_edr.png',dpi=150,facecolor=SURF)
print('recogido',round(ast(L_REC),2),'· extendido',round(ast(L_EXT),2))
