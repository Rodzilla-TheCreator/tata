import numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
OP,UNID,SOFT = 10309,3,4000
TATA_CX, TATA_AN = 97009, UNID*SOFT
FAB_CX,  FAB_AN  = 352500, UNID*4250
T = 2   # dos turnos
OPS_AN = OP*UNID*T
a = np.linspace(0,5,220)
op   = OPS_AN*a
tata = TATA_CX + TATA_AN*a
fab  = FAB_CX  + FAB_AN*a

SURF,INK,INK2,MUT = '#1a1a19','#eceae4','#b4b0a6','#6e6b64'
AZUL,NARANJA,VERDE = '#3987e5','#d95926','#199e70'
fig,ax = plt.subplots(figsize=(10,5.6), facecolor=SURF); ax.set_facecolor(SURF)
for s in ax.spines.values(): s.set_visible(False)
ax.spines['bottom'].set_visible(True); ax.spines['bottom'].set_color('#3a3833')
ax.grid(axis='y', color='#2c2a26', lw=.8); ax.set_axisbelow(True)
ax.plot(a, op/1000,   lw=2, color=NARANJA, solid_capstyle='round')
ax.plot(a, tata/1000, lw=2, color=VERDE,   solid_capstyle='round')
ax.plot(a, fab/1000,  lw=2, color=AZUL,    solid_capstyle='round')
cruce = TATA_CX/(OPS_AN-TATA_AN)
ax.plot([cruce],[ (TATA_CX+TATA_AN*cruce)/1000 ], 'o', ms=9, color=VERDE, mec=SURF, mew=2.5)
ax.annotate(f'se paga a los\n{cruce:.1f} años', (cruce,(TATA_CX+TATA_AN*cruce)/1000),
            textcoords='offset points', xytext=(12,-38), color=INK, fontsize=11, weight='bold')
ax.axvline(cruce, color=MUT, lw=1, ls=(0,(4,3)))
for y,txt,c in [(op[-1]/1000,'seguir con\noperadores',NARANJA),
                (tata[-1]/1000,'kit TaTa',VERDE),(fab[-1]/1000,'autónomos\nde fábrica',AZUL)]:
    ax.text(5.08, y, txt, color=c, fontsize=10.5, va='center', weight='bold')
ax.set_xlim(0,6.15); ax.set_ylim(0,fab[-1]/1000*1.06)
ax.set_xticks(range(6)); ax.set_xlabel('Años', color=INK2, fontsize=10.5, labelpad=9)
ax.set_ylabel('Costo acumulado  (miles de USD)', color=INK2, fontsize=10.5, labelpad=9)
ax.tick_params(colors=MUT, labelsize=9.5, length=0)
fig.text(0.028,0.955,'Tres formas de mover un maxicubo, a cinco años', color=INK, fontsize=14.5, weight='bold', va='top')
fig.text(0.028,0.893,'3 montacargas · 2 turnos · operador cargado $10,309 al año (Honduras 2026)', color=MUT, fontsize=10, va='top')
fig.text(0.028,0.038,'El autónomo de fábrica nunca alcanza a los operadores dentro de cinco años: se paga a los 7.2.', color=MUT, fontsize=9.5, va='top')
plt.tight_layout(rect=[0.02,0.07,1,0.86])
plt.savefig('retorno_5anios.png', dpi=145, facecolor=SURF)
print('cruce TaTa vs operadores:', round(cruce,2), 'años')
