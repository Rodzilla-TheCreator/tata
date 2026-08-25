# ─────────────────────────────────────────────────────────────────────────────
# Planificador de giro del EDR18N2 en pasillo de 3.00 m — Hybrid A*
#
# Por que Hybrid A* y no un barrido de arcos:
#   el montacargas es NO HOLONOMO. No se mueve de lado y tiene radio minimo de
#   giro (0.33 m a tope de direccion). Un PuzzleBot de eje diferencial gira en
#   el sitio, asi que posicion y rumbo se desacoplan y planificar es trivial.
#   Aca no: los caminos optimos son curvas de Reeds-Shepp, y con obstaculos se
#   resuelven con Hybrid A*, que es el mismo planificador que usa un auto
#   autonomo para estacionar.
#
#   El error previo fue barrer arcos a tope de direccion con un greedy. El
#   operador humano modula el angulo de forma continua y alterna sentido; eso
#   no es un arco, es una secuencia de primitivas. Hybrid A* la encuentra sola.
#
# ADVERTENCIA — la silueta es una hipotesis, no una medicion:
#   W_MAX  1.315  medido en campo (punto mas ancho, patas portantes)
#   W_RESTO       supuesto: 25 cm mas angosto
#   L_ANCHO 0.20  supuesto: cuanto dura el ancho maximo a lo largo
#   R_ESQ   0.12  supuesto: radio de las orillas
#   XPIV    1.50  DERIVADO del radio de giro de ficha (Wa = 1.797), no medido
#   El resultado es muy sensible a esto. Ver docs/11-plan-de-diagnostico.md.
# ─────────────────────────────────────────────────────────────────────────────

import math, heapq, sys, io
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')

# ── geometria ────────────────────────────────────────────────────────────
HALF=1.50; WB=1.562; XPIV=1.50; LCH=1.70; Wa=1.797
W_MAX=1.315                 # punto mas ancho
W_RESTO=W_MAX-0.25          # 1.065 — el resto, 25 cm mas angosto
L_ANCHO=0.20                # el ancho maximo dura 20 cm de largo
R_ESQ=0.12                  # orillas redondeadas
DMAX=math.atan(WB/(math.sqrt(Wa**2-XPIV**2)-W_MAX/2))

def silueta(a_centro):
    """Puntos del contorno en marco del vehiculo. a=0 es el eje de ruedas de
       carga (pivote). El cuerpo va de -XPIV (culo) a -(XPIV-LCH) (mastil)."""
    a_culo=-XPIV; a_mast=-(XPIV-LCH)
    hr=W_RESTO/2; hm=W_MAX/2
    P=[]
    # cuerpo angosto con esquinas redondeadas
    for (ax,s) in ((a_culo,-1),(a_mast,+1)):
        for lado in (+1,-1):
            for k in range(5):
                t=k/4*math.pi/2
                P.append((ax+s*R_ESQ*(1-math.cos(t)), lado*(hr-R_ESQ*(1-math.sin(t)))))
    # banda ancha de 20 cm, tambien con orillas suavizadas
    a0,a1=a_centro-L_ANCHO/2, a_centro+L_ANCHO/2
    for lado in (+1,-1):
        P += [(a0,lado*hr),(a0+0.04,lado*hm),(a1-0.04,lado*hm),(a1,lado*hr)]
    return P

def step(p,ds,d):
    dth=-(ds/WB)*math.tan(d); th2=p[2]+dth*0.5
    return (p[0]+ds*math.cos(th2), p[1]+ds*math.sin(th2), p[2]+dth)

def libre(p,SIL,margen=0.05):
    c,s=math.cos(p[2]),math.sin(p[2])
    for a,l in SIL:
        z=p[1]+a*s+l*c
        if z> HALF-margen or z< -HALF+margen: return False
    return True

# ── Hybrid A* ────────────────────────────────────────────────────────────
DS=0.08
DELTAS=[-1.0,-0.6,-0.3,0.0,0.3,0.6,1.0]
def plan(p0, th_obj, SIL, tol_th=math.radians(2.5), tol_z=0.12, maxexp=260000):
    def key(p): return (round(p[0]/0.06), round(p[1]/0.06), round(p[2]/math.radians(4)))
    h0=abs(th_obj-p0[2])*1.2
    Q=[(h0,0.0,p0,None,0,None)]; visto={}; nodos=[]
    while Q:
        f,g,p,padre,rev,ult=heapq.heappop(Q)
        k=key(p)
        if k in visto and visto[k]<=g: continue
        visto[k]=g; idx=len(nodos); nodos.append((p,padre,ult))
        if abs(p[2]-th_obj)<tol_th and abs(p[1]-0.0)<1.0:
            return g,rev,idx,nodos
        if len(nodos)>maxexp: break
        for sg in (+1,-1):
            for dk in DELTAS:
                q=p; ok=True
                for _ in range(3):
                    q=step(q,sg*DS,dk*DMAX)
                    if not libre(q,SIL): ok=False; break
                if not ok: continue
                cambio = (ult is not None and ult!=sg)
                ng=g+3*DS+(0.55 if cambio else 0)+abs(dk)*0.05
                nh=abs(th_obj-q[2])*1.2
                heapq.heappush(Q,(ng+nh,ng,q,idx,rev+(1 if cambio else 0),sg))
    return None,None,None,nodos

print(f"silueta: ancho max {W_MAX} en {L_ANCHO*100:.0f} cm · resto {W_RESTO:.3f} · esquinas r={R_ESQ}")
print(f"delta max {math.degrees(DMAX):.1f}° · pasillo {2*HALF:.2f} m\n")
print(f"{'banda ancha en a=':>18s}{'carril inicial':>16s}{'exito':>8s}{'largo':>9s}{'cambios':>9s}")
print("─"*62)
for a_c in (-0.10, 0.10, 0.30, 0.50, 0.70):
    SIL=silueta(a_c)
    fila=[]
    for cm in range(70,146,5):
        lane=-(HALF-cm/100.0)
        p0=(0.0,lane,0.0)
        if not libre(p0,SIL): continue
        g,rev,idx,_=plan(p0, math.pi/2, SIL)
        if g is not None: fila.append((cm,g,rev))
    if fila:
        mejor=min(fila,key=lambda f:(f[2],f[1]))
        print(f"{a_c:15.2f} m{mejor[0]:14d} cm{'  SI':>8s}{mejor[1]:8.2f}m{mejor[2]:9d}")
    else:
        print(f"{a_c:15.2f} m{'—':>16s}{'  NO':>8s}{'—':>9s}{'—':>9s}")
