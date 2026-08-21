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

  const paso = (axX, axY, n) => p.evaluate(([x,y,k])=>{
    window.__pad.axes[0]=x; window.__pad.axes[1]=y;
    for(let i=0;i<k;i++) stepDrive(1/60);
    return { timon:+(drv.timon*180/Math.PI).toFixed(0), steer:+(drv.steer*180/Math.PI).toFixed(1),
             reach:+drv.reach.toFixed(2), svg:document.getElementById('timon-g').getAttribute('transform'),
             txt:document.getElementById('d_timon').textContent };
  },[axX,axY,n]);

  console.log('palanca derecha 1s :', JSON.stringify(await paso(1, 0, 60)));
  console.log('  suelto 2s        :', JSON.stringify(await paso(0, 0, 120)), '← debe quedarse');
  console.log('media palanca 1s   :', JSON.stringify(await paso(0.5, 0, 60)), '← gira a la mitad');
  console.log('a fondo 4s (tope)  :', JSON.stringify(await paso(1, 0, 240)));
  const tope = await p.evaluate(()=>({ lock:+(FK.LOCK*180/Math.PI).toFixed(0),
    enTope: Math.abs(drv.timon) >= FK.LOCK-1e-6,
    aviso: document.getElementById('d_tope').style.display }));
  console.log('  tope             :', JSON.stringify(tope));
  console.log('izquierda 6s       :', JSON.stringify(await paso(-1, 0, 360)));
  await paso(0,0,1);
  console.log('pantógrafo afuera  :', JSON.stringify(await paso(0, -1, 150)));
  console.log('pantógrafo adentro :', JSON.stringify(await paso(0,  1, 300)));
  console.log('timón NO se movió con el eje vertical:', await p.evaluate(()=>Math.abs(drv.timon*180/Math.PI)));
  await p.evaluate(()=>{window.__pad.axes[0]=0;window.__pad.axes[1]=0;
    drv.timon=-FK.LOCK*0.45; drv.reach=0.3; stepDrive(1/60);});
  await p.waitForTimeout(300);
  await p.screenshot({path:'obed_panel.png'});
  console.log('ERRORS:', JSON.stringify(errs.slice(0,3)));
  await b.close();
})();
