W,H = 1120, 700
S=[f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="Máquina de estados del TaTa de línea" font-family="ui-monospace,SFMono-Regular,Menlo,monospace">']
S.append('<defs><marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
         '<path d="M0,0 L10,5 L0,10 z" fill="var(--tx2)"/></marker>'
         '<marker id="ar2" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
         '<path d="M0,0 L10,5 L0,10 z" fill="var(--ac)"/></marker></defs>')
def box(x,y,w,h,label,sub=None,fill='var(--card)',stroke='var(--bd)',tc='var(--tx)',r=8,fs=13):
    o=[f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="1.2"/>']
    ty = y+h/2+ (0 if not sub else -6)
    o.append(f'<text x="{x+w/2}" y="{ty+4.5}" text-anchor="middle" fill="{tc}" font-size="{fs}" font-weight="600" letter-spacing=".08em">{label}</text>')
    if sub: o.append(f'<text x="{x+w/2}" y="{ty+21}" text-anchor="middle" fill="var(--tx2)" font-size="10.5">{sub}</text>')
    return ''.join(o)
def arrow(x1,y1,x2,y2,c='var(--tx2)',m='ar',d=None):
    dd=f' stroke-dasharray="{d}"' if d else ''
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{c}" stroke-width="1.4"{dd} marker-end="url(#{m})"/>'
def lbl(x,y,t,fill='var(--tx2)',fs=11,anchor='start',w=600):
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" fill="{fill}" font-size="{fs}" font-weight="{w}">{t}</text>'

# ---------- capa 1: selector de tarea ----------
S.append(lbl(0,18,'1 · SELECTOR DE TAREA — se evalúa en orden, gana el primero que se cumple','var(--tx2)',11.5,'start',700))
S.append(box(0,34,132,58,'LIBRE','sin tarea','var(--card2)','var(--bd)'))
rows=[('TRASBORDO','hay un cubo mío esperando en el fondo','var(--vi)'),
      ('PEDIDO','me pidieron un color que tengo en rack','var(--am)'),
      ('ENTRADA','el humano dejó un cubo (sólo lo ve A)','var(--bl)'),
      ('PASE','lo que cargo no es mío → al trasbordo','var(--vi)'),
      ('REUBICAR','cubo mal ubicado en mi rack','var(--gr2)')]
y=34
for i,(name,cond,col) in enumerate(rows):
    S.append(box(196,y,150,40,name,None,'var(--card)',col,col,8,12))
    S.append(lbl(360,y+24,cond))
    S.append(arrow(132 if i==0 else 168,y+20 if i==0 else y+20,192,y+20))
    if i==0: S.append(arrow(132,63,192,54))
    else: S.append(f'<line x1="168" y1="{y-14}" x2="168" y2="{y+20}" stroke="var(--tx2)" stroke-width="1.4"/>')
    if i<len(rows)-1:
        S.append(lbl(160,y+50,'si no','var(--tx3)',10,'end'))
    y+=54
S.append(f'<line x1="168" y1="54" x2="168" y2="54" stroke="var(--tx2)"/>')
S.append(f'<line x1="168" y1="54" x2="168" y2="{34+4*54+20}" stroke="var(--tx2)" stroke-width="1.4" opacity=".55"/>')
S.append(lbl(196,y+18,'ninguna se cumple → espera y vuelve a evaluar','var(--tx3)',11))
S.append(lbl(196,y+38,'trasbordo lleno → A se bloquea: no puede soltar lo que no es suyo','var(--rd)',11))

# ---------- capa 2: secuencia de movimiento ----------
Y0=424
S.append(lbl(0,Y0-16,'2 · SECUENCIA DE MOVIMIENTO — corre dos veces por tarea: ORIGEN (tomar) y DESTINO (dejar)','var(--tx2)',11.5,'start',700))
steps=[('CARRIL','elige lado, curva en S'),
       ('RECTA','traslado por el pasillo'),
       ('GIRO 90°','traza calculada'),
       ('ELEVA','a la altura del nivel'),
       ('APROXIMA','creep hasta zᵢₙ'),
       ('EXTIENDE','pantógrafo 0.61 m'),
       ('SUBE / BAJA','toma o deposita'),
       ('RETRAE','pantógrafo a 0'),
       ('RETROCEDE','sale de la bahía'),
       ('DESGIRA','la misma traza al revés'),
       ('TRÁNSITO','uñas abajo')]
bw,bh,gap = 168,50,16
for i,(n,sub) in enumerate(steps):
    r,c = divmod(i,6)
    x = c*(bw+gap); yy = Y0 + r*(bh+52)
    hi = n in ('GIRO 90°','SUBE / BAJA','DESGIRA')
    S.append(box(x,yy,bw,bh,n,sub,'var(--card)','var(--ac)' if hi else 'var(--bd)',
                 'var(--ac)' if hi else 'var(--tx)',8,12))
    if c<5 and i<len(steps)-1:
        S.append(arrow(x+bw+3, yy+bh/2, x+bw+gap-4, yy+bh/2))
    if c==5 and i<len(steps)-1:
        S.append(f'<path d="M{x+bw/2},{yy+bh+3} v20 H{bw/2} v{24}" fill="none" stroke="var(--tx2)" stroke-width="1.4" marker-end="url(#ar)"/>')
yy = Y0 + (bh+52)
S.append(lbl(0, yy+bh+40, 'ORIGEN: sube 12 cm para cargar · DESTINO: baja 4 cm para soltar. El cubo nunca se arrastra.','var(--tx2)',11.5))
S.append(lbl(0, yy+bh+60, 'zᵢₙ = |Δz| + 0.60 − 1.00 − 0.61 → 1.04 m para un rack, 1.59 m para el trasbordo del fondo.','var(--tx2)',11.5))
S.append('</svg>')
open('sec/fsm.svg','w').write('\n'.join(S)); print('ok', len('\n'.join(S)))
