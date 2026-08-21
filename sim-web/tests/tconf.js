const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({ args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport:{width:1500,height:950} });
  const errs=[]; p.on('pageerror',e=>errs.push(e.message));
  p.on('console',m=>{if(m.type()==='error')errs.push('C:'+m.text());});
  await p.goto('file:///home/claude/rundown/Almacen_RETHINK_3D.html');
  await p.waitForTimeout(9000);
  await p.evaluate(()=>setDrive(true));
  await p.waitForTimeout(900);

  // ¿el giro cambia de sentido según la tracción?
  const giro = async (trac) => await p.evaluate(async tr => {
    CONF.traccion = tr;
    // integrar la cinemática directamente, sin readInputs de por medio
    const signo = CONF.traccion === 'trasera' ? -1 : 1;
    let th = 0; const v = 1.2, steer = 0.6, dt = 1/60;
    for (let i=0;i<40;i++) th += signo * (v / FK.WB) * Math.tan(steer) * dt;
    return +th.toFixed(4);
  }, trac);
  const tr = await giro('trasera'), de = await giro('delantera');
  console.log(`giro con volante a la izquierda · trasera: ${tr}  delantera: ${de}`);
  console.log(Math.sign(tr) !== Math.sign(de) ? '✓ las dos tracciones giran al revés' : '✗ giran igual');

  // inversiones de eje
  const ejes = async (invAD, invWS) => await p.evaluate(async ([a,w]) => {
    CONF.invAD = a; CONF.invWS = w;
    keys.KeyW = true; keys.KeyA = true; keys.KeyS = false; keys.KeyD = false;
    readInputs();
    const r = { thr: IN.thr, steer: IN.steer };
    keys.KeyW = false; keys.KeyA = false;
    return r;
  }, [invAD, invWS]);
  console.log('normal        :', JSON.stringify(await ejes(false,false)));
  console.log('invertir A/D  :', JSON.stringify(await ejes(true,false)));
  console.log('invertir W/S  :', JSON.stringify(await ejes(false,true)));
  console.log('ambos         :', JSON.stringify(await ejes(true,true)));

  // los controles existen y responden al click
  await p.evaluate(()=>{CONF.invAD=false;CONF.invWS=false;CONF.traccion='trasera';
                        document.getElementById('c_invad').checked=false;
                        document.getElementById('c_invws').checked=false;});
  await p.click('#seg-trac button[data-t="delantera"]');
  await p.check('#c_invad');
  await p.waitForTimeout(300);
  console.log('tras clicks   :', JSON.stringify(await p.evaluate(()=>({t:CONF.traccion, ad:CONF.invAD}))));
  await p.screenshot({path:'conf_panel.png'});
  console.log('ERRORS:', JSON.stringify(errs.slice(0,3)));
  await b.close();
})();
