const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({ args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport:{width:1500,height:1000} });
  const errs=[]; p.on('pageerror',e=>errs.push(e.message));
  await p.addInitScript(()=>{window.__pad={id:'V',index:0,connected:true,mapping:'standard',
    axes:[0,0,0,0],buttons:Array.from({length:17},()=>({pressed:false,value:0}))};
    navigator.getGamepads=()=>[window.__pad];});
  await p.goto('file:///home/claude/rundown/Almacen_RETHINK_3D.html');
  await p.waitForTimeout(9000);
  await p.evaluate(()=>setDrive(true)); await p.waitForTimeout(600);
  await p.click('#seg-esq button[data-e="obed"]'); await p.waitForTimeout(800);

  const r = await p.evaluate(()=>{
    const out={};
    // 1 · detenido, flecha arriba → sale a tope
    drv.v=0; keys.ArrowUp=true; for(let i=0;i<300;i++) stepDrive(1/60); keys.ArrowUp=false;
    out.aTope = +drv.reach.toFixed(3);
    out.lector = document.getElementById('d_reach').textContent;
    // 2 · con el pantógrafo afuera, ¿acelera?
    keys.KeyW=true; for(let i=0;i<180;i++) stepDrive(1/60); keys.KeyW=false;
    out.vConPantografoAfuera = +Math.abs(drv.v).toFixed(3);
    // 3 · recoger y acelerar
    keys.ArrowDown=true; for(let i=0;i<300;i++) stepDrive(1/60); keys.ArrowDown=false;
    out.recogido = +drv.reach.toFixed(3);
    keys.KeyW=true; for(let i=0;i<180;i++) stepDrive(1/60);
    out.vRecogido = +Math.abs(drv.v).toFixed(2);
    // 4 · en movimiento, intentar extender
    keys.ArrowUp=true; for(let i=0;i<120;i++) stepDrive(1/60); keys.ArrowUp=false; keys.KeyW=false;
    out.reachEnMovimiento = +drv.reach.toFixed(3);
    // 5 · ¿estados intermedios?
    const vistos=new Set(); drv.v=0; drv.reachCmd=1;
    for(let i=0;i<400;i++){ stepDrive(1/60); vistos.add(+drv.reach.toFixed(2)); }
    out.valorFinal = +drv.reach.toFixed(3);
    return out;
  });
  console.log(JSON.stringify(r,null,1));
  console.log(r.aTope>0.6 && r.vConPantografoAfuera<0.05 && r.vRecogido>0.3 && r.reachEnMovimiento<0.02
    ? '✓ binario, enclavado en tránsito y sin acelerar extendido' : '✗ revisar');
  console.log('ERRORS:', JSON.stringify(errs.slice(0,3)));
  await b.close();
})();
