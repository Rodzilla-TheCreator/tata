const { chromium, devices } = require('playwright');
(async () => {
  const b = await chromium.launch({ args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'] });
  const ctx = await b.newContext({ ...devices['iPhone 13 landscape'], hasTouch:true, isMobile:true });
  const p = await ctx.newPage();
  const errs=[]; p.on('pageerror',e=>errs.push(e.message));
  await p.goto('file:///home/claude/rundown/Almacen_RETHINK_3D.html');
  await p.waitForTimeout(9000);
  await p.evaluate(()=>{setDrive(true); setCabina(true);});
  await p.waitForTimeout(1200);
  const pos = () => p.evaluate(()=>{
    const r=o=>{const e=document.getElementById(o).getBoundingClientRect();return [Math.round(e.left),Math.round(e.top)];};
    return {joy:r('tjoy'), btns:r('tbtns'), win:r('camwin'), scrollY:window.scrollY,
            bodyOverflow:getComputedStyle(document.body).overflow};
  });
  console.log('antes :', JSON.stringify(await pos()));
  // simular que aparece la barra del navegador: alto -80 px
  await p.setViewportSize({width:750, height:262});
  await p.waitForTimeout(900);
  console.log('barra :', JSON.stringify(await pos()));
  await p.setViewportSize({width:750, height:342});
  await p.waitForTimeout(900);
  console.log('vuelve:', JSON.stringify(await pos()));
  // intentar hacer scroll con el dedo
  await p.touchscreen.tap(400,180);
  await p.mouse.move(400,120); await p.mouse.down(); await p.mouse.move(400,300,{steps:8}); await p.mouse.up();
  console.log('tras arrastrar, scrollY =', await p.evaluate(()=>window.scrollY));
  console.log('ERRORS:', JSON.stringify(errs.slice(0,3)));
  await b.close();
})();
