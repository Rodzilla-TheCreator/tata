import json, math

BAY=1.30; NCOL=12; RACKD=1.10; AISLE=3.00; HALF=AISLE/2
LTOT=2.91; LCH=1.70; Wt=1.054; WB=1.562; XPIV=1.91; FLEN=1.21; REACH=0.61
CUBE_D=1.20

def step(p, ds, d):
    dth = -(ds/WB)*math.tan(d)
    th2 = p[2] + dth*0.5
    return (p[0]+ds*math.cos(th2), p[1]+ds*math.sin(th2), p[2]+dth)

def corners(p):
    c,s = math.cos(p[2]), math.sin(p[2]); hw = Wt/2
    def pt(a,l): return (p[0]+a*c-l*s, p[1]+a*s+l*c)
    ch=[pt(-XPIV,hw),pt(-XPIV,-hw),pt(-(XPIV-LCH),hw),pt(-(XPIV-LCH),-hw)]
    fk=[pt(LTOT-XPIV,0.30),pt(LTOT-XPIV,-0.30)]
    return ch,fk

def chassis_poly(p):
    c,s = math.cos(p[2]), math.sin(p[2]); hw=Wt/2
    def pt(a,l): return (p[0]+a*c-l*s, p[1]+a*s+l*c)
    return [pt(-XPIV,hw),pt(-(XPIV-LCH),hw),pt(-(XPIV-LCH),-hw),pt(-XPIV,-hw)]

def forks_poly(p, reach=0.0):
    c,s = math.cos(p[2]), math.sin(p[2])
    def pt(a,l): return (p[0]+a*c-l*s, p[1]+a*s+l*c)
    a0 = -(XPIV-LCH)+reach; a1 = a0+FLEN+0.10
    return [pt(a0,0.37),pt(a1,0.37),pt(a1,0.23),pt(a0,0.23)], \
           [pt(a0,-0.23),pt(a1,-0.23),pt(a1,-0.37),pt(a0,-0.37)]

def plan(side):
    best=None
    lane=0.0
    while lane <= 0.9501:
        for deg in range(88,45,-1):
            d = math.radians(deg)
            p=(0.0, side*lane, 0.0); path=[p]
            chMin,chMax,fkMin,fkMax = 9,-9,9,-9; n=0
            while abs(p[2]) < math.pi/2 and n < 3000:
                n+=1; p = step(p, 0.015, -side*d); path.append(p)
                ch,fk = corners(p)
                for q in ch: chMin=min(chMin,q[1]); chMax=max(chMax,q[1])
                for q in fk: fkMin=min(fkMin,q[1]); fkMax=max(fkMax,q[1])
            if n>=3000: continue
            p=(p[0],p[1],side*math.pi/2); path[-1]=p
            chV=max(-HALF-chMin, chMax-HALF); fkV=max(-(HALF+0.60)-fkMin, fkMax-(HALF+0.60))
            holg=min(HALF-chMax, chMin+HALF)
            score=(1e3+chV*1e3 if chV>-0.02 else 0)+(1e2+fkV*1e2 if fkV>0 else 0)-holg*10+abs(lane)*0.4
            if best is None or score<best['score']:
                best=dict(score=score,lane=lane,deg=deg,path=path,holg=holg,
                          chMin=chMin,chMax=chMax,fkMin=fkMin,fkMax=fkMax,end=p)
        lane += 0.025
    return best

P = plan(+1)
end = P['end']
# anclar: el pivote final en x=0
sh = -end[0]
path = [(x+sh, z, th) for (x,z,th) in P['path']]
EXF = 0.0
for p in path:
    ch,fk = corners(p)
    for q in ch+fk: EXF = max(EXF, q[0])

zin = lambda dz: abs(dz)+CUBE_D/2-(LTOT-XPIV)-REACH
out = dict(
  lane=P['lane'], deg=P['deg'], holg=P['holg'],
  chMin=P['chMin'], chMax=P['chMax'], fkMax=P['fkMax'],
  barrido=P['chMax']-P['chMin'], EXF=EXF,
  entry=path[0][0], endz=end[1],
  zin_rack=zin(HALF+RACKD/2), zin_hand=zin(2.60),
  R=WB/math.tan(math.radians(P['deg'])),
)
print(json.dumps(out, indent=1))
json.dump(dict(meta=out,
   path=[[round(x,4),round(z,4),round(th,5)] for x,z,th in path[::12]]+[[round(path[-1][0],4),round(path[-1][1],4),round(path[-1][2],5)]],
   poses=[[round(v,4) for v in path[min(len(path)-1,int(f*(len(path)-1)))]] for f in (0,0.25,0.5,0.75,1.0)],
   ), open('sec/giro.json','w'))
