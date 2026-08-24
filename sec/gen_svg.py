import json, math
D = json.load(open('sec/giro.json')); M = D['meta']
LTOT=2.91; LCH=1.70; Wt=1.054; XPIV=1.91; FLEN=1.21; REACH=0.61
HALF=1.50; RACKD=1.10

def chassis(p):
    c,s=math.cos(p[2]),math.sin(p[2]); hw=Wt/2
    f=lambda a,l:(p[0]+a*c-l*s, p[1]+a*s+l*c)
    return [f(-XPIV,hw),f(-(XPIV-LCH),hw),f(-(XPIV-LCH),-hw),f(-XPIV,-hw)]
def forks(p,reach=0.0):
    c,s=math.cos(p[2]),math.sin(p[2])
    f=lambda a,l:(p[0]+a*c-l*s, p[1]+a*s+l*c)
    a0=-(XPIV-LCH)+reach; a1=a0+FLEN
    return ([f(a0,0.37),f(a1,0.37),f(a1,0.23),f(a0,0.23)],
            [f(a0,-0.23),f(a1,-0.23),f(a1,-0.37),f(a0,-0.37)])

# ---- lienzo ----
X0,X1,Z0,Z1 = -2.85, 2.65, -1.95, 3.05
K = 132.0
Wpx, Hpx = (X1-X0)*K, (Z1-Z0)*K
sx = lambda x: (x-X0)*K
sz = lambda z: (z-Z0)*K
def poly(pts, **kw):
    d=' '.join(f'{sx(x):.1f},{sz(z):.1f}' for x,z in pts)
    a=' '.join(f'{k.replace("_","-")}="{v}"' for k,v in kw.items())
    return f'<polygon points="{d}" {a}/>'
def line(x1,z1,x2,z2,**kw):
    a=' '.join(f'{k.replace("_","-")}="{v}"' for k,v in kw.items())
    return f'<line x1="{sx(x1):.1f}" y1="{sz(z1):.1f}" x2="{sx(x2):.1f}" y2="{sz(z2):.1f}" {a}/>'
def txt(x,z,t,**kw):
    a=' '.join(f'{k.replace("_","-")}="{v}"' for k,v in kw.items())
    return f'<text x="{sx(x):.1f}" y="{sz(z):.1f}" {a}>{t}</text>'

S=[]
S.append(f'<svg viewBox="0 0 {Wpx:.0f} {Hpx:.0f}" width="100%" role="img" aria-label="Geometría del giro de 90 grados en pasillo de 3 metros" font-family="ui-monospace,SFMono-Regular,Menlo,monospace">')
S.append('<defs><pattern id="hatch" width="7" height="7" patternTransform="rotate(45)" patternUnits="userSpaceOnUse">'
         '<line x1="0" y1="0" x2="0" y2="7" stroke="var(--rk)" stroke-width="3"/></pattern></defs>')
# racks
S.append(poly([(X0,-HALF-RACKD),(X1,-HALF-RACKD),(X1,-HALF),(X0,-HALF)], fill='url(#hatch)', opacity='.5'))
S.append(poly([(X0,HALF),(X1,HALF),(X1,HALF+RACKD),(X0,HALF+RACKD)], fill='url(#hatch)', opacity='.5'))
# hueco de la bahía objetivo (1.30 de luz, centrado en x=0)
S.append(poly([(-0.65,HALF),(0.65,HALF),(0.65,HALF+RACKD),(-0.65,HALF+RACKD)], fill='var(--bay)', opacity='.9'))
S.append(line(-0.65,HALF,-0.65,HALF+RACKD, stroke='var(--ac2)', stroke_width='2'))
S.append(line(0.65,HALF,0.65,HALF+RACKD, stroke='var(--ac2)', stroke_width='2'))
# caras del pasillo
for z in (-HALF, HALF):
    S.append(line(X0,z,X1,z, stroke='var(--rk2)', stroke_width='2'))
# banda barrida por el chasis
S.append(poly([(X0,M['chMin']),(X1,M['chMin']),(X1,M['chMax']),(X0,M['chMax'])],
              fill='var(--swp)', opacity='.16'))
for z in (M['chMin'], M['chMax']):
    S.append(line(X0,z,X1,z, stroke='var(--swp)', stroke_width='1.5', stroke_dasharray='6 5', opacity='.85'))
# carril
S.append(line(X0,M['lane'],X1,M['lane'], stroke='var(--ln)', stroke_width='1.5', stroke_dasharray='2 7'))
# eje del pasillo
S.append(line(X0,0,X1,0, stroke='var(--gr)', stroke_width='1', stroke_dasharray='1 9', opacity='.7'))

# trayectoria del pivote
p=' '.join(f'{sx(x):.1f},{sz(z):.1f}' for x,z,_ in D['path'])
S.append(f'<polyline points="{p}" fill="none" stroke="var(--ac)" stroke-width="2.5"/>')

# siluetas
poses=D['poses']
for i,q in enumerate(poses):
    fin = (i==len(poses)-1)
    op = 0.16+0.16*i
    col = 'var(--ac)' if fin else 'var(--gh)'
    S.append(poly(chassis(q), fill='none', stroke=col, stroke_width='2.2' if fin else '1.4',
                  opacity=f'{1 if fin else op:.2f}'))
    fa,fb = forks(q)
    for f in (fa,fb):
        if fin: S.append(poly(f, fill=col, opacity='0.9', stroke='none'))
        else:   S.append(poly(f, fill='none', stroke=col, stroke_width='1', opacity=f'{op*0.8:.2f}'))
    S.append(f'<circle cx="{sx(q[0]):.1f}" cy="{sz(q[1]):.1f}" r="{3.4 if fin else 2.2}" fill="{col}" opacity="{1 if fin else op:.2f}"/>')
# uñas extendidas al final
q=poses[-1]
fa,fb = forks(q, REACH)
for f in (fa,fb):
    S.append(poly(f, fill='none', stroke='var(--ac2)', stroke_width='1.6', stroke_dasharray='4 3'))

# cotas
def cota(x, z1, z2, label, dx=0.0):
    o=[]
    o.append(line(x,z1,x,z2, stroke='var(--tx2)', stroke_width='1'))
    for z in (z1,z2): o.append(line(x-0.07,z,x+0.07,z, stroke='var(--tx2)', stroke_width='1'))
    o.append(txt(x+dx+0.09,(z1+z2)/2+0.05,label, fill='var(--tx)', font_size='12.5'))
    return ''.join(o)
S.append(cota(-2.62,-HALF,HALF,'3.00 m'))
S.append(cota(2.42,M['chMin'],M['chMax'],f"{M['barrido']:.2f} m", dx=-1.02))
S.append(txt(-2.53, -HALF-0.16, 'RACK', fill='var(--tx2)', font_size='11', letter_spacing='.14em'))
S.append(txt(-2.53, HALF+0.72, 'RACK · BAHÍA OBJETIVO', fill='var(--tx2)', font_size='11', letter_spacing='.14em'))
# holguras
S.append(txt(1.55, M['chMin']-0.11, f"holgura {abs(M['chMin']+HALF)*100:.0f} cm", fill='var(--ok)', font_size='12'))
S.append(txt(1.55, M['chMax']+0.24, f"holgura {(HALF-M['chMax'])*100:.0f} cm", fill='var(--ok)', font_size='12'))
S.append(txt(-2.78, M['lane']-0.10, f"carril {M['lane']:.2f} m", fill='var(--ln)', font_size='12'))
S.append(txt(-0.58, M['fkMax']+0.30, f"uñas {(M['fkMax']-HALF)*100:.0f} cm dentro de la bahía al girar", fill='var(--tx2)', font_size='12'))
S.append(txt(-0.58, HALF+0.98, f"pantógrafo +{REACH:.2f} m → fondo del cubo", fill='var(--ac2)', font_size='12'))
for i,q in enumerate(poses):
    lbl='①②③④⑤'[i]
    S.append(txt(q[0]-0.30, q[1]-0.16, lbl, fill='var(--ac)' if i==4 else 'var(--tx2)', font_size='13'))
S.append(txt(M['entry']-0.34, M['lane']+0.30, 'entra al carril', fill='var(--tx2)', font_size='11.5', text_anchor='middle'))
S.append(txt(-2.78, 1.32, 'alineado con la columna', fill='var(--ac)', font_size='11.5'))
S.append('</svg>')
open('sec/giro.svg','w').write('\n'.join(S))
print('svg', len('\n'.join(S)), 'lane', M['lane'], 'R', round(M['R'],3))
