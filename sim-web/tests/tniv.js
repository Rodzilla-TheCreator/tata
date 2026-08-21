const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({ args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport:{width:1500,height:1000} });
  const errs=[]; p.on('pageerror',e=>errs.push(e.message));
  p.on('console',m=>{if(m.type()==='error')errs.push('C:'+m.text());});
  await p.addInitScript(() => {
    window.__pad={id:'V',index:0,connected:true,mapping:'standard',
      axes:[0,0,0,0],buttons:Array.from({length:17},()=>({pressed:false,value:0}))};
    navigator.getGamepads=()=>[window.__pad];
  });
  await p.goto('file:///home/claude/rundown/Almacen_RETHINK_3D.html');
  await p.waitForTimeout(9000);
  await p.evaluate(()=>setDrive(true));
  await p.waitForTimeout(600);
  await p.click('#seg-esq button[data-e="obed"]');
  await p.waitForTimeout(800);
  console.log('límites de inclinación EDR:', JSON.stringify(await p.evaluate(()=>({TF:FK.TF,TB:FK.TB,REACH:FK.REACH,LIFT:FK.LIFT}))));
  console.log('niveles disponibles:', JSON.stringify(await p.evaluate(()=>FK.NIVELES.filter(h=>h<=FK.LIFT+0.01))));

  // un empujón de palanca = un nivel
  const empujar = (dir, veces) => p.evaluate(([d,n])=>{
    const out=[];
    for(let k=0;k<n;k++){
      window.__pad.axes[1] = -d;             // arriba es negativo en el eje Y
      for(let i=0;i<8;i++) stepDrive(1/60);
      window.__pad.axes[1] = 0;
      for(let i=0;i<8;i++) stepDrive(1/60);
      out.push(drv.nivel);
    }
    for(let i=0;i<400;i++) stepDrive(1/60);  // dejar que la torre llegue
    return { secuencia:out, lift:+drv.lift.toFixed(2), txt:document.getElementById('d_nivel').textContent };
  },[dir,veces]);
  console.log('3 empujones arriba :', JSON.stringify(await empujar(1,3)));
  console.log('2 empujones abajo  :', JSON.stringify(await empujar(-1,2)));
  console.log('tope arriba (x9)   :', JSON.stringify(await empujar(1,9)));

  // inclinación limitada
  const tilt = await p.evaluate(()=>{
    IN.tiltB=1; for(let i=0;i<300;i++) stepForks(1/60); IN.tiltB=0; const max=+drv.tilt.toFixed(1);
    IN.tiltF=1; for(let i=0;i<400;i++) stepForks(1/60); IN.tiltF=0; const min=+drv.tilt.toFixed(1);
    return {atras:max, adelante:min};
  });
  console.log('inclinación tope   :', JSON.stringify(tilt), '← ficha EDR: 4° atrás, 3° adelante');

  // flechas verticales mueven el pantógrafo, no las uñas
  const pant = await p.evaluate(()=>{
    drv.reach=0; const l0=drv.lift;
    keys.ArrowUp=true; for(let i=0;i<200;i++) stepDrive(1/60); keys.ArrowUp=false;
    const r1=+drv.reach.toFixed(2), l1=+drv.lift.toFixed(2);
    keys.ArrowDown=true; for(let i=0;i<300;i++) stepDrive(1/60); keys.ArrowDown=false;
    return { afuera:r1, adentro:+drv.reach.toFixed(2), liftAntes:+l0.toFixed(2), liftDespues:l1 };
  });
  console.log('flechas ↑↓         :', JSON.stringify(pant));
  await p.screenshot({path:'obed2.png'});
  console.log('ERRORS:', JSON.stringify(errs.slice(0,3)));
  await b.close();
})();
