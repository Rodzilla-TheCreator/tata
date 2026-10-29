// deck_o3.js — TaTa · Estado actual y pedido para Omar (octubre 2026)
// Deck corto de seguimiento: lo logrado, por que estoy parado, y dos pedidos
// (reparar el MT 122, bajar el presupuesto de computo de $1,400 a $500).
// Reusa el lenguaje visual de deck_o2.js. Genera TaTa_Estado_y_Pedido_Omar.pptx
const pptx = require('pptxgenjs');
const p = new pptx();
p.layout = 'LAYOUT_WIDE';               // 13.3 x 7.5
p.author = 'TaTa'; p.company = 'TaTa · Tecnología Avanzada de Transporte Autónomo';
p.title = 'TaTa · Estado y pedido — octubre 2026';

const OSCURO = '14171C', PANEL = '20242B', CLARO = 'F4F5F7', TINTA = '1A1D23';
const HUM = 'ECEBE6', MUT = '8B949E', MUT2 = '5B6470';
const HAZ = 'F5C518', VERDE = '39D98A', ROJO = 'FF5A52', CIAN = '37C3FF';
const H = 'Cambria', B = 'Calibri';
const W = 13.3, HT = 7.5;

const sombra = () => ({ type: 'outer', color: '000000', blur: 12, offset: 3, angle: 90, opacity: 0.28 });
function fondo(s, dark) { s.background = { color: dark ? OSCURO : CLARO }; }
function chip(s, n, x, y, col) {
  s.addShape(p.ShapeType.ellipse, { x, y, w: 0.42, h: 0.42, fill: { color: col || HAZ } });
  s.addText(String(n), { x, y, w: 0.42, h: 0.42, align: 'center', valign: 'middle',
    fontSize: 15, bold: true, color: OSCURO, fontFace: B, margin: 0 });
}
function titulo(s, txt, dark, sub) {
  s.addText(txt, { x: 0.65, y: 0.42, w: W - 1.3, h: 0.85, fontSize: 34, bold: true,
    color: dark ? HUM : TINTA, fontFace: H, margin: 0 });
  if (sub) s.addText(sub, { x: 0.65, y: 1.24, w: W - 1.3, h: 0.4, fontSize: 13.5,
    color: dark ? MUT : MUT2, fontFace: B, margin: 0 });
}
function tarjeta(s, x, y, w, h, dark, tint) {
  s.addShape(p.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.09,
    fill: { color: tint || (dark ? PANEL : 'FFFFFF') }, shadow: sombra() });
}
function stat(s, x, y, w, valor, etiqueta, col, dark) {
  s.addText(valor, { x, y, w, h: 0.72, fontSize: 38, bold: true, color: col,
    fontFace: H, margin: 0, align: 'left' });
  s.addText(etiqueta, { x, y: y + 0.74, w, h: 0.5, fontSize: 11,
    color: dark ? MUT : MUT2, fontFace: B, margin: 0 });
}
function fila(s, x, y, w, h, cols, dark, head) {
  s.addShape(p.ShapeType.rect, { x, y, w, h, fill: { color: head ? (dark ? PANEL : 'E7E9EC') : (dark ? '1A1E25' : 'FFFFFF') },
    line: { color: dark ? '2C323B' : 'D8DADE', width: 0.6 } });
  let cx = x;
  cols.forEach(c => {
    s.addText(c.t, { x: cx + 0.14, y, w: c.w - 0.28, h, fontSize: c.fs || (head ? 10 : 11),
      bold: head || c.b, color: c.c || (head ? (dark ? MUT : MUT2) : (dark ? HUM : TINTA)),
      fontFace: B, margin: 0, valign: 'middle', align: c.a || 'left' });
    cx += c.w;
  });
}
const money = n => '$' + n.toLocaleString('en-US');

/* ───────── 1 · PORTADA ───────── */
let s = p.addSlide(); fondo(s, true);
s.addShape(p.ShapeType.rect, { x: 0.9, y: 2.35, w: 1.5, h: 0.045, fill: { color: HAZ } });
s.addText('TaTa', { x: 0.9, y: 1.0, w: 6, h: 1.0, fontSize: 54, bold: true, color: HAZ, fontFace: H, margin: 0 });
s.addText('Tecnología Avanzada de Transporte Autónomo · un proyecto de Montasa', { x: 0.93, y: 1.95, w: 10, h: 0.4,
  fontSize: 14, color: MUT, fontFace: B, margin: 0 });
s.addText('Dónde estamos, y lo que\nnecesito para seguir', { x: 0.9, y: 2.6, w: 9.5, h: 1.5,
  fontSize: 32, bold: true, color: HUM, fontFace: H, lineSpacing: 40, margin: 0 });
const port = [['Teleop', '2/3', 'validado en banco', VERDE],
              ['Presupuesto de cómputo', money(500), 'antes ' + money(1400), HAZ],
              ['Para destrabar', '1 equipo', 'reparar el MT 122', CIAN]];
port.forEach((q, i) => {
  const x = 0.9 + i * 3.9;
  tarjeta(s, x, 4.55, 3.6, 1.45, true);
  s.addText(q[0], { x: x + 0.3, y: 4.7, w: 3.1, h: 0.3, fontSize: 10, bold: true, color: q[3], fontFace: B, charSpacing: 1, margin: 0 });
  s.addText(q[1], { x: x + 0.3, y: 5.04, w: 3.1, h: 0.6, fontSize: 28, bold: true, color: HUM, fontFace: H, margin: 0 });
  s.addText(q[2], { x: x + 0.3, y: 5.62, w: 3.1, h: 0.3, fontSize: 10.5, color: MUT, fontFace: B, margin: 0 });
});
s.addText('Preparado para Omar', { x: 0.9, y: 6.5, w: 6, h: 0.35, fontSize: 13, bold: true, color: HUM, fontFace: B, margin: 0 });
s.addText('Octubre 2026 · San Pedro Sula', { x: 0.9, y: 6.85, w: 6, h: 0.3, fontSize: 11, color: MUT, fontFace: B, margin: 0 });
s.addNotes('Seguimiento, no el caso de negocio completo. Tres números arriba: el avance, el presupuesto que baja, y el pedido de un equipo. Abrir diciendo que el software ya está y que lo unico que frena es la maquina.');

/* ───────── 2 · RESUMEN ───────── */
s = p.addSlide(); fondo(s, false);
titulo(s, 'En una página', false, 'Si sólo lees un slide, que sea este');
const rex = [
  ['Lo logrado', 'Leí la computadora del montacargas y logré comandar la marcha y la dirección. Probado en mi mesa. Es 2/3 del teleop, sin gastar un dólar.', VERDE],
  ['El freno', 'Estoy parado: no hay un equipo funcional dedicado. Al que probaba le quitaron la llanta de dirección, y el pedal de hombre-muerto que me iban a traer se lo pusieron a otro equipo.', ROJO],
  ['Lo que pido', 'Reparar el MT 122 (hoy usado como banco de repuestos) para tenerlo en renta y de plataforma; y bajar el presupuesto de cómputo de ' + money(1400) + ' a ' + money(500) + '.', HAZ]];
rex.forEach((r, i) => {
  const y = 1.95 + i * 1.62;
  tarjeta(s, 0.65, y, 12, 1.42, false);
  s.addShape(p.ShapeType.rect, { x: 0.65, y, w: 0.09, h: 1.42, fill: { color: r[2] } });
  s.addText(r[0], { x: 1.0, y: y + 0.18, w: 3.0, h: 0.5, fontSize: 18, bold: true, color: TINTA, fontFace: H, margin: 0 });
  s.addText(r[1], { x: 4.1, y: y + 0.16, w: 8.3, h: 1.1, fontSize: 13, color: MUT2, fontFace: B, margin: 0, valign: 'middle' });
});
s.addNotes('Las tres cajas son la conversacion entera: algo real ya hecho, un freno que no es mio, y dos pedidos concretos.');

/* ───────── 3 · LO LOGRADO ───────── */
s = p.addSlide(); fondo(s, true);
titulo(s, 'Lo que ya está hecho, sin gastar un dólar', true, 'Ingeniería, no compras: descubrir cómo se le habla a este equipo se paga una sola vez');
const log = [
  ['Leí el cerebro del equipo', 'El bus interno del montacargas está mapeado: qué controlador es cada uno y qué dato lleva. Todo en modo lectura, sin tocar nada.'],
  ['Marcha: comandable', 'Logré darle la orden de avanzar por el mismo bus. El equipo respondió pidiendo el pedal de hombre-muerto — señal de que aceptó la orden como real. Probado en banco.'],
  ['Dirección: emulador validado', 'Construí el circuito que reemplaza al sensor del volante y, en mi mesa, reproduce la señal real con exactitud. Listo para enchufar cuando haya equipo.'],
  ['Simuladores y planificador', 'La simulación del almacén, el visor de flota y el planificador de giro ya corren. Es lo que convierte esto de una idea a algo que existe.']];
log.forEach((l, i) => {
  const x = 0.65 + (i % 2) * 6.15, y = 2.0 + Math.floor(i / 2) * 2.35;
  tarjeta(s, x, y, 5.85, 2.1, true);
  s.addText(l[0], { x: x + 0.35, y: y + 0.25, w: 5.2, h: 0.5, fontSize: 16, bold: true, color: HAZ, fontFace: H, margin: 0 });
  s.addText(l[1], { x: x + 0.35, y: y + 0.82, w: 5.2, h: 1.1, fontSize: 12, color: MUT, fontFace: B, margin: 0, valign: 'top' });
});
s.addNotes('El punto para un financiero: esto es NRE, ingenieria que se paga una vez para todo el modelo, no por unidad. Y no costo efectivo.');

/* ───────── 4 · POR QUÉ ESTOY PARADO ───────── */
s = p.addSlide(); fondo(s, false);
titulo(s, 'Por qué estoy parado — y no es el software', false, 'El código está. Lo que falta es una máquina que encienda');
const par = [
  ['Al equipo de prueba le quitaron la llanta de dirección', 'Sin ella no hay cómo ver el timón girar, que es la prueba que vine a hacer.'],
  ['El pedal de hombre-muerto se lo pusieron a otro equipo', 'Era la pieza que faltaba para cerrar el teleop. Me lo iban a traer y se reasignó.']];
par.forEach((q, i) => {
  const y = 2.1 + i * 1.35;
  tarjeta(s, 0.65, y, 12, 1.15, false);
  s.addShape(p.ShapeType.rect, { x: 0.65, y, w: 0.09, h: 1.15, fill: { color: ROJO } });
  s.addText(q[0], { x: 1.0, y: y + 0.18, w: 11.2, h: 0.5, fontSize: 15.5, bold: true, color: TINTA, fontFace: B, margin: 0 });
  s.addText(q[1], { x: 1.0, y: y + 0.68, w: 11.2, h: 0.4, fontSize: 12, color: MUT2, fontFace: B, margin: 0 });
});
tarjeta(s, 0.65, 5.15, 12, 1.0, false, '20242B');
s.addText('El avance ya no depende de más tiempo en la computadora. Depende de un montacargas funcional dedicado al proyecto.',
  { x: 1.05, y: 5.15, w: 11.2, h: 1.0, fontSize: 15, bold: true, color: HAZ, fontFace: B, margin: 0, valign: 'middle' });
s.addNotes('Honestidad: no estoy pidiendo tiempo ni plata para programar mas. Estoy pidiendo la maquina. Es un bloqueo externo, no de ejecucion.');

/* ───────── 5 · PEDIDO 1 · MT 122 ───────── */
s = p.addSlide(); fondo(s, true);
titulo(s, 'Pedido 1 · Reparar el MT 122', true, 'Hoy está detenido y se usa como banco de repuestos');
tarjeta(s, 0.65, 2.0, 12, 1.5, true, PANEL);
s.addText('“Ya agarramos ese equipo como banco de repuestos.”', { x: 1.05, y: 2.15, w: 11.2, h: 0.5, fontSize: 16, italic: true, bold: true, color: HUM, fontFace: H, margin: 0 });
s.addText('— Miguel.  Un equipo dañado no es un cajón de piezas: es un activo detenido. Cada pieza que se le saca lo aleja de volver a generar renta, y encarece repararlo después.',
  { x: 1.05, y: 2.72, w: 11.2, h: 0.7, fontSize: 12.5, color: MUT, fontFace: B, margin: 0, valign: 'top' });
const mt = [
  ['El costo real de canibalizar', 'Cada repuesto que sale del MT 122 es una pieza que luego hay que comprar dos veces: para el equipo que la recibe hoy, y para el MT 122 cuando se quiera revivir.'],
  ['La lista ya debería existir', 'Miguel dice que vos ya deberías tener la lista de lo necesario para repararlo. Se actualiza, se cotiza y se pide.']];
mt.forEach((q, i) => {
  const x = 0.65 + i * 6.15, y = 3.85;
  tarjeta(s, x, y, 5.85, 1.95, true);
  s.addText(q[0], { x: x + 0.35, y: y + 0.25, w: 5.2, h: 0.5, fontSize: 15, bold: true, color: CIAN, fontFace: H, margin: 0 });
  s.addText(q[1], { x: x + 0.35, y: y + 0.82, w: 5.2, h: 1.0, fontSize: 12, color: MUT, fontFace: B, margin: 0, valign: 'top' });
});
s.addText('El pedido: aprobar la reparación del MT 122 y dejar que Miguel actualice la lista para ordenarla.',
  { x: 0.65, y: 6.1, w: 12, h: 0.5, fontSize: 13.5, bold: true, color: HAZ, fontFace: B, margin: 0 });
s.addNotes('Aca es donde se desafia la mentalidad de "un equipo dañado es repuesto gratis". El argumento es de plata, no de principio: canibalizar sale mas caro y mata un activo que podria rentar.');

/* ───────── 6 · DOBLE RETORNO ───────── */
s = p.addSlide(); fondo(s, false);
titulo(s, 'El MT 122 reparado paga dos veces', false, 'Un solo gasto de reparación, dos retornos');
const ret = [
  ['Vuelve a renta', 'Reparado, regresa a la flota y genera ingreso de renta — en vez de $0 detenido ocupando espacio.', VERDE],
  ['Plataforma de TaTa', 'Es el equipo dedicado donde el proyecto avanza, sin tener que sacar de rotación un montacargas que sí está rentando.', CIAN]];
ret.forEach((q, i) => {
  const x = 0.65 + i * 6.15, y = 2.1;
  tarjeta(s, x, y, 5.85, 2.6, false);
  s.addShape(p.ShapeType.rect, { x, y, w: 5.85, h: 0.12, fill: { color: q[2] } });
  s.addText(q[0], { x: x + 0.4, y: y + 0.4, w: 5.1, h: 0.55, fontSize: 20, bold: true, color: TINTA, fontFace: H, margin: 0 });
  s.addText(q[1], { x: x + 0.4, y: y + 1.1, w: 5.1, h: 1.3, fontSize: 13.5, color: MUT2, fontFace: B, margin: 0, valign: 'top' });
});
tarjeta(s, 0.65, 5.15, 12, 1.0, false, '20242B');
s.addText('La misma reparación sirve a la flota y al proyecto. No es un gasto del proyecto: es un activo de Montasa que vuelve a producir.',
  { x: 1.05, y: 5.15, w: 11.2, h: 1.0, fontSize: 15, bold: true, color: HAZ, fontFace: B, margin: 0, valign: 'middle' });
s.addNotes('Clave para Omar: el gasto no se lo cargas al proyecto, se lo cargas a recuperar un activo. El proyecto es el bonus.');

/* ───────── 7 · EL CAMINO TÉCNICO ───────── */
s = p.addSlide(); fondo(s, true);
titulo(s, 'El camino que sigue, por etapas', true, 'Empezamos con lo que el equipo ya trae. El sensor caro se suma sólo si hace falta');
const cam = [
  ['1', 'Odometría', 'Leer velocidad y ángulo del propio bus del equipo — los sensores ya están adentro. Da una posición estimada por “cuánto me moví”.', CIAN],
  ['2', 'Cámara + ArUco', 'Cámaras que leen marcas en los racks y corrigen la deriva de la odometría. Es el posicionamiento principal.', HAZ],
  ['3', 'LiDAR (después)', 'Mapeo en vivo del pasillo. Es expansión futura, no requisito para arrancar. Se agrega cuando el proyecto lo justifique.', MUT]];
cam.forEach((q, i) => {
  const y = 2.0 + i * 1.5;
  tarjeta(s, 0.65, y, 12, 1.3, true);
  chip(s, q[0], 1.0, y + 0.44, q[3]);
  s.addText(q[1], { x: 1.65, y: y + 0.28, w: 3.3, h: 0.5, fontSize: 17, bold: true, color: HUM, fontFace: H, margin: 0 });
  s.addText(q[2], { x: 5.0, y: y + 0.2, w: 7.4, h: 1.0, fontSize: 12.5, color: MUT, fontFace: B, margin: 0, valign: 'middle' });
});
s.addNotes('La historia: no necesitamos el sensor caro para el primer nivel. Odometria + camara alcanzan. El LiDAR es a donde se puede llegar, no por donde se empieza.');

/* ───────── 8 · PEDIDO 2 · PRESUPUESTO ───────── */
s = p.addSlide(); fondo(s, false);
titulo(s, 'Pedido 2 · Bajar el presupuesto de cómputo', false, 'De ' + money(1400) + ' a ' + money(500) + ' — porque con sólo cámaras no hace falta el equipo grande');
fila(s, 0.65, 2.1, 12, 0.5, [{ t: '', w: 4.0 }, { t: 'ANTES', w: 4.0, a: 'left' }, { t: 'AHORA', w: 4.0, a: 'left' }], false, true);
const bud = [
  ['Sensor', 'LiDAR 3D (Unitree L2)', '2 cámaras USB'],
  ['Cómputo', 'Jetson Orin NX · 16 GB', 'Jetson · 8 GB'],
  ['Costo del paquete', money(1400), money(500)]];
bud.forEach((r, i) => {
  const y = 2.6 + i * 0.6, last = i === 2;
  fila(s, 0.65, y, 12, 0.6, [
    { t: r[0], w: 4.0, b: true, c: TINTA },
    { t: r[1], w: 4.0, c: last ? MUT2 : TINTA, b: last },
    { t: r[2], w: 4.0, c: last ? VERDE : TINTA, b: true }], false);
});
tarjeta(s, 0.65, 4.75, 5.85, 1.1, false);
stat(s, 1.0, 4.95, 5.0, '− ' + money(900), 'menos que el plan original', VERDE, false);
tarjeta(s, 6.8, 4.75, 5.85, 1.1, false);
stat(s, 7.15, 4.95, 5.0, '− 64%', 'del presupuesto de cómputo', VERDE, false);
s.addText('El LiDAR no se descarta: pasa a ser expansión opcional. Para el primer nivel, cámaras + Jetson 8 GB alcanzan.',
  { x: 0.65, y: 6.1, w: 12, h: 0.5, fontSize: 13, bold: true, color: MUT2, fontFace: B, margin: 0 });
s.addText('Cifras de cotización, por confirmar antes de comprometer la compra.',
  { x: 0.65, y: 6.95, w: 12, h: 0.35, fontSize: 10.5, italic: true, color: MUT2, fontFace: B, margin: 0 });
s.addNotes('El ahorro es el titular. Y el matiz honesto: no es que el LiDAR no sirva, es que no hace falta para arrancar. Las cifras son cotizacion mia, hay que confirmarlas.');

/* ───────── 9 · EL PEDIDO ───────── */
s = p.addSlide(); fondo(s, true);
titulo(s, 'Lo que necesito de vos', true, 'Tres cosas concretas para destrabar el proyecto');
const ped = [
  ['1', 'Aprobar reparar el MT 122', 'Que Miguel actualice la lista de repuestos y se ordene. Vuelve a renta y queda de plataforma del proyecto.', VERDE],
  ['2', 'Que el MT 118 de Agrolibano pase por acá', 'Cuando venga a mantenimiento: probar multipiloto y timón, y empezar a emular el pedal de hombre-muerto.', CIAN],
  ['3', 'Visto bueno al presupuesto de ' + money(500), 'El paquete reducido (cámaras + Jetson 8 GB). El LiDAR queda para después.', HAZ]];
ped.forEach((q, i) => {
  const y = 2.0 + i * 1.15;
  tarjeta(s, 0.65, y, 12, 0.98, true);
  chip(s, q[0], 1.0, y + 0.28, q[3]);
  s.addText(q[1], { x: 1.62, y: y + 0.15, w: 4.6, h: 0.55, fontSize: 15, bold: true, color: HUM, fontFace: B, margin: 0, valign: 'middle' });
  s.addText(q[2], { x: 6.3, y: y + 0.14, w: 6.1, h: 0.72, fontSize: 11, color: MUT, fontFace: B, margin: 0, valign: 'middle' });
});
tarjeta(s, 0.65, 5.75, 12, 0.95, true, PANEL);
s.addText('El software ya está. Lo único que falta es un equipo que encienda.',
  { x: 1.05, y: 5.75, w: 11.2, h: 0.95, fontSize: 16, bold: true, color: HAZ, fontFace: B, margin: 0, valign: 'middle' });
s.addNotes('Cerrar con la frase. Ninguno de los tres pedidos es un cheque grande: uno recupera un activo, otro es logistica de taller, el tercero es aprobar MENOS plata que antes.');

p.writeFile({ fileName: 'presentaciones/TaTa_Estado_y_Pedido_Omar.pptx' }).then(() => console.log('deck OMAR o3 listo'));
