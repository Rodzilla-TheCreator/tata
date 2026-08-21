import numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
exec(open('analisis_degeneracion.py').read().split('print("\\n Incertidumbre')[0])

def geo(relieve, bahias=60):
    S=[]
    for lado in (+1,-1):
        yP,yC = lado*ANCHO/2, lado*(ANCHO/2+relieve)
        for k in range(bahias):
            x0=k*BAY
            S += [(x0,yP,x0+POSTE,yP),(x0+POSTE,yP,x0+POSTE,yC),
                  (x0+POSTE,yC,x0+BAY,yC),(x0+BAY,yC,x0+BAY,yP)]
    return np.array(S,float)

rel = np.linspace(0.005, 0.20, 26)
sx, sy = [], []
for r in rel:
    H = informacion(np.array([36.0,0.0]), geo(r))
    C = np.linalg.inv(H); d = np.sqrt(np.diag(C))*100
    sx.append(d[0]); sy.append(d[1])
sx, sy = np.array(sx), np.array(sy)

SURF, INK, INK2, MUT = '#1a1a19', '#eceae4', '#b4b0a6', '#6e6b64'
AZUL, NARANJA = '#3987e5', '#d95926'
fig, ax = plt.subplots(figsize=(9.6,5.4), facecolor=SURF)
ax.set_facecolor(SURF)
for s in ax.spines.values(): s.set_visible(False)
ax.spines['bottom'].set_visible(True); ax.spines['bottom'].set_color('#3a3833')
ax.grid(axis='y', color='#2c2a26', lw=.8); ax.set_axisbelow(True)

ax.plot(rel*100, sx, lw=2, color=NARANJA, solid_capstyle='round')
ax.plot(rel*100, sy, lw=2, color=AZUL, solid_capstyle='round')
ax.axvline(8, color=MUT, lw=1, ls=(0,(4,3)))
ax.text(8.4, sx.max()*0.95, 'rack típico\n8 cm de relieve', color=INK2, fontsize=9.5, va='top')
ax.text(rel[-1]*100+0.3, sx[-1], 'a lo largo\ndel pasillo', color=NARANJA, fontsize=10.5, va='center', weight='bold')
ax.text(rel[-1]*100+0.3, sy[-1], 'a lo ancho', color=AZUL, fontsize=10.5, va='center', weight='bold')
i8 = int(np.argmin(abs(rel-0.08)))
ax.plot([8],[sx[i8]], 'o', ms=8, color=NARANJA, mec=SURF, mew=2)
ax.plot([8],[sy[i8]], 'o', ms=8, color=AZUL, mec=SURF, mew=2)
ax.annotate(f'{sx[i8]:.2f} cm', (8, sx[i8]), textcoords='offset points', xytext=(10,10),
            color=INK, fontsize=11, weight='bold')
ax.annotate(f'{sy[i8]:.2f} cm', (8, sy[i8]), textcoords='offset points', xytext=(10,-16),
            color=INK, fontsize=11, weight='bold')

ax.set_xlim(0, rel[-1]*100+3.4); ax.set_ylim(0, max(sx)*1.12)
ax.set_xlabel('Relieve del rack — cuánto sobresale el montante frente a la carga  (cm)',
              color=INK2, fontsize=10.5, labelpad=9)
ax.set_ylabel('Incertidumbre de una pose  (cm)', color=INK2, fontsize=10.5, labelpad=9)
ax.tick_params(colors=MUT, labelsize=9.5, length=0)
fig.text(0.028, 0.955, 'Lo que sostiene al SLAM en un pasillo uniforme es el montante del rack',
         color=INK, fontsize=14.5, weight='bold', va='top')
fig.text(0.028, 0.893, 'Pasillo Nave Este · 5.54 m de ancho · sin pared visible al fondo · ruido de rango 2 cm',
         color=MUT, fontsize=10, va='top')
fig.text(0.028, 0.055, 'Con relieve cero las dos paredes quedan lisas y el problema queda',
         color=MUT, fontsize=9.5, va='top')
fig.text(0.028, 0.022, 'matemáticamente indeterminado: el SLAM se desliza sin límite.',
         color=MUT, fontsize=9.5, va='top')
plt.tight_layout(rect=[0.02,0.085,1,0.86])
plt.savefig('degeneracion_pasillo.png', dpi=145, facecolor=SURF)
print('relieve 8 cm →  largo', round(sx[i8],3), 'cm | ancho', round(sy[i8],3), 'cm | relación', round(sx[i8]/sy[i8],1))
print('relieve 0.5 cm →', round(sx[0],3), 'cm | relación', round(sx[0]/sy[0],1))
