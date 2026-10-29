// deck_o3.js — TaTa · Estado actual y pedido para Omar (octubre 2026)
// Deck de seguimiento: lo logrado, el cambio de plan (mecanico -> EDR) que nos
// puso on-track, los hitos con fecha, quien financia que (NRE+computo = maje;
// reparar el MT 122 + salario/confianza = inversion de Montasa), y el pedido.
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
  s.addText(txt, { x: 0.65, y: 0.42, w: W - 1.3, h: 0.85, fontSize: 33, bold: true,
    color: dark ? HUM : TINTA, fontFace: H, margin: 0 });
  if (sub) s.addText(sub, { x: 0.65, y: 1.22, w: W - 1.3, h: 0.4, fontSize: 13.5,
    color: dark ? MUT : MUT2, fontFace: B, margin: 0 });
}
function tarjeta(s, x, y, w, h, dark, tint) {
  s.addShape(p.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.09,
    fill: { color: tint || (dark ? PANEL : 'FFFFFF') }, shadow: sombra() });
}
function stat(s, x, y, w, valor, etiqueta, col, dark) {
  s.addText(valor, { x, y, w, h: 0.72, fontSize: 36, bold: true, color: col,
    fontFace: H, margin: 0, align: 'left' });
  s.addText(etiqueta, { x, y: y + 0.72, w, h: 0.5, fontSize: 11,
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
              ['Cómputo + NRE', 'lo pongo yo', 'cómputo bajado a ' + money(500), HAZ],
              ['A Montasa', 'reparar', 'el MT 122', CIAN]];
port.forEach((q, i) => {
  const x = 0.9 + i * 3.9;
  tarjeta(s, x, 4.55, 3.6, 1.45, true);
  s.addText(q[0], { x: x + 0.3, y: 4.7, w: 3.1, h: 0.3, fontSize: 10, bold: true, color: q[3], fontFace: B, charSpacing: 1, margin: 0 });
  s.addText(q[1], { x: x + 0.3, y: 5.04, w: 3.1, h: 0.6, fontSize: 25, bold: true, color: HUM, fontFace: H, margin: 0 });
  s.addText(q[2], { x: x + 0.3, y: 5.64, w: 3.1, h: 0.3, fontSize: 10.5, color: MUT, fontFace: B, margin: 0 });
});
s.addText('Preparado para Omar', { x: 0.9, y: 6.5, w: 6, h: 0.35, fontSize: 13, bold: true, color: HUM, fontFace: B, margin: 0 });
s.addText('Octubre 2026 · San Pedro Sula', { x: 0.9, y: 6.85, w: 6, h: 0.3, fontSize: 11, color: MUT, fontFace: B, margin: 0 });
s.addNotes('Seguimiento, no el caso de negocio completo. El mensaje: el software ya esta, el NRE lo pongo yo, y lo unico que frena es la maquina.');

/* ───────── 2 · RESUMEN ───────── */
s = p.addSlide(); fondo(s, false);
titulo(s, 'En una página', false, 'Si sólo lees un slide, que sea este');
const rex = [
  ['Lo logrado', 'Leí la computadora del montacargas y logré comandar la marcha y la dirección. Probado en banco. Es 2/3 del teleop, y el cambio de plan al EDR nos puso on-track.', VERDE],
  ['El freno', 'Estoy parado: no hay un equipo funcional dedicado. Al que probaba le quitaron la llanta de dirección, y el pedal de hombre-muerto se lo pusieron a otro equipo.', ROJO],
  ['Lo que pido', 'Reparar el MT 122 (hoy banco de repuestos) — un activo de Montasa que vuelve a rentar. El NRE y el cómputo los pongo yo.', HAZ]];
rex.forEach((r, i) => {
  const y = 1.95 + i * 1.62;
  tarjeta(s, 0.65, y, 12, 1.42, false);
  s.addShape(p.ShapeType.rect, { x: 0.65, y, w: 0.09, h: 1.42, fill: { color: r[2] } });
  s.addText(r[0], { x: 1.0, y: y + 0.18, w: 3.0, h: 0.5, fontSize: 18, bold: true, color: TINTA, fontFace: H, margin: 0 });
  s.addText(r[1], { x: 4.1, y: y + 0.16, w: 8.3, h: 1.1, fontSize: 13, color: MUT2, fontFace: B, margin: 0, valign: 'middle' });
});
s.addNotes('Las tres cajas son la conversacion entera: algo real ya hecho, un freno que no es mio, y un solo pedido que ademas recupera un activo suyo.');

/* ───────── 3 · LO LOGRADO ───────── */
s = p.addSlide(); fondo(s, true);
titulo(s, 'Lo que ya está hecho, sin gastar un dólar de Montasa', true, 'Ingeniería, no compras: descubrir cómo se le habla a este equipo se paga una sola vez');
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
s.addNotes('El punto para un financiero: esto es NRE, ingenieria que se paga una vez para todo el modelo, no por unidad. Y cero costo efectivo para Montasa.');

/* ───────── 4 · DOS CAMINOS ───────── */
s = p.addSlide(); fondo(s, false);
titulo(s, 'El cambio de plan no fue un retraso — fue lo que nos puso on-track', false, 'Plan original: un equipo mecánico.  Plan actual: el EDR, eléctrico y con bus abierto');
fila(s, 0.65, 2.0, 12, 0.5, [{ t: '', w: 3.2 }, { t: 'PLAN MECÁNICO (Baoli)', w: 4.4, c: ROJO }, { t: 'EL EDR (el que se tomó)', w: 4.4, c: VERDE }], false, true);
const dc = [
  ['Pasillo de 3.00 m', 'No cabe (pedía 3.82 m)', 'Cabe'],
  ['Dirección', 'Montar un servo sobre la columna', 'EPS: se intercepta eléctrico'],
  ['Reach / elevación / inclinación', 'Fabricar bloque de válvulas y actuadores', 'Mando electrohidráulico de fábrica'],
  ['Freno', 'Actuador mecánico propio', 'Frena solo al soltar'],
  ['Sensores', 'Todos desde cero', 'Ya en el bus CAN — se leen'],
  ['El NRE es…', 'Fabricación mecánica · meses por eje', 'Información: qué señal es cada cable']];
dc.forEach((r, i) => {
  const y = 2.5 + i * 0.5;
  fila(s, 0.65, y, 12, 0.5, [
    { t: r[0], w: 3.2, b: true, c: TINTA },
    { t: r[1], w: 4.4, c: MUT2 },
    { t: r[2], w: 4.4, c: TINTA, b: true }], false);
});
s.addText('Elegimos la arquitectura que convierte meses de fabricación en semanas de ingeniería. Ese fue el acierto que compró el calendario.',
  { x: 0.65, y: 5.7, w: 12, h: 0.6, fontSize: 13.5, bold: true, color: TINTA, fontFace: B, margin: 0 });
s.addNotes('Anticipar "cambiaron de plan, perdieron tiempo". Al reves: el plan mecanico habria seguido fabricando el primer actuador. El EDR ya tiene 2/3 del teleop.');

/* ───────── 5 · LOS HITOS ───────── */
s = p.addSlide(); fondo(s, true);
titulo(s, 'Los hitos que hemos conseguido', true, 'Tres meses desde que se eligió el EDR. On time, on track');
const hit = [
  ['Ago', 'Se descarta el Baoli y se elige el EDR: cabe en el pasillo y es eléctrico', VERDE],
  ['Sep', 'Puerto de servicio abierto · el equipo es un Jungheinrich (manual completo en mano)', HUM],
  ['1–3 Oct', 'El bus interno es CAN — mapeado pin por pin', HUM],
  ['5 Oct', 'Escucha del bus validada con instrumento propio', HUM],
  ['14 Oct', 'Transmisión al bus validada (20/20)', HUM],
  ['22 Oct', 'Marcha comandable — probada: el equipo pidió el hombre-muerto', CIAN],
  ['24 Oct', 'Dirección descifrada: sensor del volante, no CAN', HUM],
  ['27 Oct', 'Emulador de dirección validado en banco', CIAN],
  ['Hoy', '2/3 del teleop · el freno es de hardware (equipo), no de ingeniería', HAZ]];
hit.forEach((q, i) => {
  const x = 0.65 + (i % 3) * 4.05, y = 2.0 + Math.floor(i / 3) * 1.35;
  tarjeta(s, x, y, 3.85, 1.2, true);
  s.addText(q[0], { x: x + 0.3, y: y + 0.16, w: 3.3, h: 0.35, fontSize: 13, bold: true, color: q[2], fontFace: H, margin: 0 });
  s.addText(q[1], { x: x + 0.3, y: y + 0.52, w: 3.3, h: 0.62, fontSize: 10.5, color: MUT, fontFace: B, margin: 0, valign: 'top' });
});
s.addNotes('La linea de tiempo es la prueba de "on track". Dos de los tres canales de mando probados, el bus entero leido, en tres meses.');

/* ───────── 6 · POR QUÉ ESTOY PARADO ───────── */
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
s.addNotes('Honestidad: no pido tiempo ni plata para programar mas. Pido la maquina. Bloqueo externo, no de ejecucion.');

/* ───────── 7 · PEDIDO · MT 122 ───────── */
s = p.addSlide(); fondo(s, true);
titulo(s, 'Reparar el MT 122', true, 'Hoy está detenido y se usa como banco de repuestos');
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
s.addNotes('El argumento es de plata, no de principio: canibalizar sale mas caro y mata un activo que podria rentar.');

/* ───────── 8 · DOBLE RETORNO ───────── */
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
s.addNotes('El gasto no se lo cargas al proyecto, se lo cargas a recuperar un activo. El proyecto es el bonus.');

/* ───────── 9 · QUIÉN PONE QUÉ ───────── */
s = p.addSlide(); fondo(s, true);
titulo(s, 'Quién pone qué', true, 'Pongo mi plata en lo que es mío. A Montasa le pido recuperar un activo suyo');
tarjeta(s, 0.65, 2.0, 5.95, 3.7, true);
s.addShape(p.ShapeType.rect, { x: 0.65, y: 2.0, w: 5.95, h: 0.12, fill: { color: HAZ } });
s.addText('Lo pongo yo', { x: 1.0, y: 2.3, w: 5.3, h: 0.5, fontSize: 19, bold: true, color: HAZ, fontFace: H, margin: 0 });
[['NRE / ingeniería', 'Todo lo comprado en C&D: transceptores, el emulador, el ESP32, componentes.'],
 ['El cómputo (la Jetson)', 'También es parte del NRE. Lo cubro yo.'],
 ['Por qué', 'Es mi idea, mi proyecto, mi sueño. El riesgo de la apuesta es mío.']].forEach((q, i) => {
  const y = 2.95 + i * 0.9;
  s.addText(q[0], { x: 1.0, y, w: 5.3, h: 0.35, fontSize: 13.5, bold: true, color: HUM, fontFace: B, margin: 0 });
  s.addText(q[1], { x: 1.0, y: y + 0.32, w: 5.3, h: 0.55, fontSize: 11, color: MUT, fontFace: B, margin: 0, valign: 'top' });
});
tarjeta(s, 6.85, 2.0, 5.8, 3.7, true);
s.addShape(p.ShapeType.rect, { x: 6.85, y: 2.0, w: 5.8, h: 0.12, fill: { color: CIAN } });
s.addText('Lo pone Montasa', { x: 7.2, y: 2.3, w: 5.1, h: 0.5, fontSize: 19, bold: true, color: CIAN, fontFace: H, margin: 0 });
[['Reparar el MT 122', 'Su propio activo, que vuelve a rentar. No es gasto del proyecto.'],
 ['Salario y confianza', 'Lo que Montasa ya me ha dado. Lo tomo como su inversión en esto.']].forEach((q, i) => {
  const y = 2.95 + i * 1.3;
  s.addText(q[0], { x: 7.2, y, w: 5.1, h: 0.35, fontSize: 13.5, bold: true, color: HUM, fontFace: B, margin: 0 });
  s.addText(q[1], { x: 7.2, y: y + 0.32, w: 5.1, h: 0.75, fontSize: 11, color: MUT, fontFace: B, margin: 0, valign: 'top' });
});
tarjeta(s, 0.65, 6.0, 12, 0.85, true, PANEL);
s.addText('No le pido a Montasa que financie mi sueño. Le pido que recupere una máquina suya — y yo pongo todo lo demás.',
  { x: 1.05, y: 6.0, w: 11.2, h: 0.85, fontSize: 14, bold: true, color: HAZ, fontFace: B, margin: 0, valign: 'middle' });
s.addNotes('Este es el slide que desarma el riesgo para Omar: no se le pide comprar hardware. El NRE y el computo los pone maje. Montasa solo recupera un activo propio.');

/* ───────── 10 · PRESUPUESTO DE CÓMPUTO ───────── */
s = p.addSlide(); fondo(s, false);
titulo(s, 'El cómputo: lo bajé de ' + money(1400) + ' a ' + money(500) + ' — y lo pago yo', false, 'Con sólo cámaras no hace falta el equipo grande ni el LiDAR');
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
stat(s, 1.0, 4.95, 5.0, '− ' + money(900), 'más barato que el plan original', VERDE, false);
tarjeta(s, 6.8, 4.75, 5.85, 1.1, false);
stat(s, 7.15, 4.95, 5.0, money(0), 'que gasta Montasa en cómputo', VERDE, false);
s.addText('El LiDAR no se descarta: pasa a ser expansión opcional. Para el primer nivel, cámaras + Jetson 8 GB alcanzan — y corren por mi cuenta.',
  { x: 0.65, y: 6.1, w: 12, h: 0.5, fontSize: 13, bold: true, color: MUT2, fontFace: B, margin: 0 });
s.addText('Cifras de cotización, por confirmar antes de comprar.',
  { x: 0.65, y: 6.95, w: 12, h: 0.35, fontSize: 10.5, italic: true, color: MUT2, fontFace: B, margin: 0 });
s.addNotes('El ahorro es el titular, y el remate es que lo pago yo: cero riesgo de hardware para Montasa. El LiDAR no se descarta, es expansion.');

/* ───────── 11 · EL PEDIDO ───────── */
s = p.addSlide(); fondo(s, true);
titulo(s, 'Lo que necesito de vos', true, 'Nada de esto es un cheque por hardware');
const ped = [
  ['1', 'Aprobar reparar el MT 122', 'Que Miguel actualice la lista de repuestos y se ordene. Vuelve a renta y queda de plataforma del proyecto.', VERDE],
  ['2', 'Que el MT 118 de Agrolibano pase por acá', 'Cuando venga a mantenimiento: probar multipiloto y timón, y empezar a emular el pedal de hombre-muerto.', CIAN],
  ['3', 'Visto bueno estratégico', 'Que TaTa siga como línea de Montasa. El NRE y el cómputo los pongo yo.', HAZ]];
ped.forEach((q, i) => {
  const y = 2.0 + i * 1.15;
  tarjeta(s, 0.65, y, 12, 0.98, true);
  chip(s, q[0], 1.0, y + 0.28, q[3]);
  s.addText(q[1], { x: 1.62, y: y + 0.15, w: 4.7, h: 0.55, fontSize: 15, bold: true, color: HUM, fontFace: B, margin: 0, valign: 'middle' });
  s.addText(q[2], { x: 6.4, y: y + 0.14, w: 6.0, h: 0.72, fontSize: 11, color: MUT, fontFace: B, margin: 0, valign: 'middle' });
});
tarjeta(s, 0.65, 5.75, 12, 0.95, true, PANEL);
s.addText('El software ya está, y el NRE lo pongo yo. Lo único que falta es un equipo que encienda.',
  { x: 1.05, y: 5.75, w: 11.2, h: 0.95, fontSize: 16, bold: true, color: HAZ, fontFace: B, margin: 0, valign: 'middle' });
s.addNotes('Cerrar con la frase. Los tres pedidos: uno recupera un activo, otro es logistica de taller, el tercero no cuesta nada. Ninguno es comprar hardware.');

p.writeFile({ fileName: 'presentaciones/TaTa_Estado_y_Pedido_Omar.pptx' }).then(() => console.log('deck OMAR o3 listo'));
