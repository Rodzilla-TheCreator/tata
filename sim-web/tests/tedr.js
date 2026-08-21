const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({ args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport:{width:1500,height:980} });
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
  await p.waitForTimeout(700);

  await p.click('#seg-esq button[data-e="edr"]');
  await p.waitForTimeout(900);
  console.log('preset:', JSON.stringify(await p.evaluate(()=>({
    esq:CONF.esquema, nom:FK.nom||PRESETS.edr18n2.nom, L:+FK.L.toFixed(2), W:+FK.W.toFixed(3),
    WB:+FK.WB.toFixed(3), FLEN:+FK.FLEN.toFixed(2), VMAX:+FK.VMAX.toFixed(2),
    kmh:+(FK.VMAX*3.6).toFixed(1), SSHIFT:FK.SSHIFT, largoTotal:+(FK.L+FK.FLEN).toFixed(2) }))));

  // gatillos analógicos
  const gas = async (rt, lt) => await p.evaluate(([r,l])=>{
    window.__pad.buttons[7]={pressed:r>0,value:r};
    window.__pad.buttons[6]={pressed:l>0,value:l};
    readInputs(); return { thr:+IN.thr.toFixed(2), brakeA:+(IN.brakeA||0).toFixed(2) };
  },[rt,lt]);
  console.log('RT 100%      :', JSON.stringify(await gas(1,0)));
  console.log('RT 40%       :', JSON.stringify(await gas(0.4,0)));
  console.log('LT 60% freno :', JSON.stringify(await gas(0,0.6)));
  await gas(0,0);

  // B cambia de sentido
  const antes = await p.evaluate(()=>CONF.dir);
  await p.evaluate(()=>{window.__pad.buttons[1]={pressed:true,value:1};});
  await p.waitForTimeout(350);
  await p.evaluate(()=>{window.__pad.buttons[1]={pressed:false,value:0};});
  await p.waitForTimeout(250);
  const desp = await p.evaluate(()=>({dir:CONF.dir, txt:document.getElementById('d_sentido').textContent, manejando:drv.on}));
  console.log(`B · sentido ${antes} → ${desp.dir} (${desp.txt}) · sigue manejando: ${desp.manejando}`);
  const rev = await p.evaluate(()=>{window.__pad.buttons[7]={pressed:true,value:1};readInputs();
    const r=+IN.thr.toFixed(2); window.__pad.buttons[7]={pressed:false,value:0}; return r;});
  console.log('RT en reversa:', rev);

  // desplazador lateral
  const sh = await p.evaluate(()=>{
    const out=[]; drv.shift=0;
    IN.sprOut=1; for(let i=0;i<200;i++) stepForks(1/60); out.push(+drv.shift.toFixed(3));
    IN.sprOut=0; IN.sprIn=1; for(let i=0;i<400;i++) stepForks(1/60); out.push(+drv.shift.toFixed(3));
    IN.sprIn=0; drv.shift=0; syncForks();
    return { tope:out[0], topeNeg:out[1], carroX:+drv.mesh.userData.carro.position.x.toFixed(3) };
  });
  console.log('desplazador  :', JSON.stringify(sh), '· recorrido total', (sh.tope-sh.topeNeg).toFixed(2), 'm');
  // el desplazador absorbe error lateral
  console.log('separación en esquema EDR bloqueada:', await p.evaluate(()=>{
    const s0=drv.spread; IN.sprOut=1; for(let i=0;i<60;i++) stepForks(1/60); IN.sprOut=0;
    return drv.spread===s0; }));
  await p.screenshot({path:'edr_panel.png'});
  console.log('ERRORS:', JSON.stringify(errs.slice(0,3)));
  await b.close();
})();
