// deck_o3.js — TaTa · Estado actual y pedido para Omar (octubre 2026)
// Deck de seguimiento: lo logrado, el cambio de plan (mecanico -> EDR), los hitos
// con detalle de agosto (investigacion+simulacion) y septiembre (el muro del DB9,
// con diagrama de pines), el 1-oct como punto de inflexion, el bloqueo (piezas
// quitadas), el camino que sigue, El Aula, computo por etapas, y el pedido.
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
  s.addText(txt, { x: 0.65, y: 0.42, w: W - 1.3, h: 0.85, fontSize: 32, bold: true,
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

// ─── un pin de DB9 (circulo con numero, coloreado por funcion) ───
function pin(s, cx, cy, n, role) {
  const col = role ? role[1] : '2A2F39';
  s.addShape(p.ShapeType.ellipse, { x: cx, y: cy, w: 0.3, h: 0.3, fill: { color: col }, line: { color: '0B0E12', width: 0.5 } });
  s.addText(String(n), { x: cx, y: cy, w: 0.3, h: 0.3, align: 'center', valign: 'middle',
    fontSize: 10, bold: true, color: role ? '0B0E12' : MUT, fontFace: B, margin: 0 });
}
// ─── un DB9 esquematico (shell + 9 pines) con roles {n:[label,color]} ───
function db9(s, x, y, title, roles) {
  const W9 = 2.95, H9 = 1.15;
  s.addText(title, { x, y: y - 0.34, w: W9, h: 0.3, align: 'center', fontSize: 11.5, bold: true, color: TINTA, fontFace: B, margin: 0 });
  s.addShape(p.ShapeType.roundRect, { x, y, w: W9, h: H9, rectRadius: 0.14, fill: { color: '0F1218' }, line: { color: MUT2, width: 1.2 } });
  const px0 = x + 0.36, dx = 0.52;
  for (let i = 0; i < 5; i++) pin(s, px0 + i * dx, y + 0.26, i + 1, roles[i + 1]);   // 1..5 arriba
  for (let i = 0; i < 4; i++) pin(s, px0 + 0.26 + i * dx, y + 0.68, i + 6, roles[i + 6]); // 6..9 abajo
}
/* ───────── 1 · PORTADA ───────── */
let s = p.addSlide(); fondo(s, true);
s.addShape(p.ShapeType.rect, { x: 0.9, y: 2.35, w: 1.5, h: 0.045, fill: { color: HAZ } });
s.addText('TaTa', { x: 0.9, y: 1.0, w: 6, h: 1.0, fontSize: 54, bold: true, color: HAZ, fontFace: H, margin: 0 });
s.addText('Tecnología Avanzada de Transporte Autónomo · un proyecto de Montasa', { x: 0.93, y: 1.95, w: 10, h: 0.4,
  fontSize: 14, color: MUT, fontFace: B, margin: 0 });
s.addText('Dónde estamos, y lo que\nnecesito para seguir', { x: 0.9, y: 2.6, w: 9.5, h: 1.5,
  fontSize: 32, bold: true, color: HUM, fontFace: H, lineSpacing: 40, margin: 0 });
const port = [['Teleop', '2/3', 'validado en banco', VERDE],
              ['Cómputo + NRE', 'lo pongo yo', 'es mi proyecto', HAZ],
              ['A Montasa', 'un equipo', 'reparar el MT 122', CIAN]];
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
  ['El freno', 'Estoy parado: no hay un equipo funcional dedicado. Le quitaron, para otros equipos, la dirección, la hidráulica del pantógrafo, la cámara y el sensor del pedal — justo lo que necesito para probar.', ROJO],
  ['Lo que pido', 'Reparar el MT 122 (o, si no, permiso de pruebas reversibles en mantenimiento para la etapa de odometría), y reorganizar estantes para El Aula. El NRE y el cómputo los pongo yo.', HAZ]];
rex.forEach((r, i) => {
  const y = 1.95 + i * 1.62;
  tarjeta(s, 0.65, y, 12, 1.42, false);
  s.addShape(p.ShapeType.rect, { x: 0.65, y, w: 0.09, h: 1.42, fill: { color: r[2] } });
  s.addText(r[0], { x: 1.0, y: y + 0.18, w: 3.0, h: 0.5, fontSize: 18, bold: true, color: TINTA, fontFace: H, margin: 0 });
  s.addText(r[1], { x: 4.1, y: y + 0.14, w: 8.3, h: 1.15, fontSize: 12.5, color: MUT2, fontFace: B, margin: 0, valign: 'middle' });
});
s.addNotes('Algo real ya hecho, un freno que no es mio, y un pedido que recupera un activo suyo + reorganizar estantes.');

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
s.addNotes('Esto es NRE, ingenieria que se paga una vez para todo el modelo, no por unidad. Y cero costo efectivo para Montasa.');

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
s.addNotes('Anticipar "cambiaron de plan, perdieron tiempo". Al reves: el plan mecanico habria seguido fabricando el primer actuador.');

/* ───────── 5 · LOS HITOS ───────── */
s = p.addSlide(); fondo(s, true);
titulo(s, 'Los hitos que hemos conseguido', true, 'Tres meses desde que se eligió el EDR. On time, on track');
const hit = [
  ['Ago', 'Medición de campo, geometría corregida, simuladores y planificador de giro', VERDE],
  ['Ago', 'Se descarta el Baoli y se elige el EDR: cabe en el pasillo y es eléctrico', VERDE],
  ['Sep', 'Puerto de servicio abierto · el equipo es un Jungheinrich (manual completo)', HUM],
  ['Sep', 'El muro del DB9: el cable del técnico era RS232 y no servía (ver adelante)', ROJO],
  ['1 Oct', 'Punto de inflexión: el bus es CAN. Desde acá, volando', HAZ],
  ['5–14 Oct', 'Escucha del bus y transmisión validadas con instrumento propio (20/20)', HUM],
  ['22 Oct', 'Marcha comandable — probada: el equipo pidió el hombre-muerto', CIAN],
  ['24–27 Oct', 'Dirección descifrada (sensor del volante) y emulador validado en banco', CIAN],
  ['Hoy', '2/3 del teleop · el freno es de hardware (equipo), no de ingeniería', HAZ]];
hit.forEach((q, i) => {
  const x = 0.65 + (i % 3) * 4.05, y = 2.0 + Math.floor(i / 3) * 1.35;
  tarjeta(s, x, y, 3.85, 1.2, true);
  s.addText(q[0], { x: x + 0.3, y: y + 0.16, w: 3.3, h: 0.35, fontSize: 13, bold: true, color: q[2], fontFace: H, margin: 0 });
  s.addText(q[1], { x: x + 0.3, y: y + 0.52, w: 3.3, h: 0.62, fontSize: 10.5, color: MUT, fontFace: B, margin: 0, valign: 'top' });
});
s.addNotes('El 1-oct es el quiebre. Antes: meses de puerto. Despues: en 3 semanas marcha y direccion. Detalle de ago y sep en los dos slides siguientes.');

/* ───────── 6 · AGOSTO: INVESTIGACIÓN Y SIMULACIÓN ───────── */
s = p.addSlide(); fondo(s, false);
titulo(s, 'Agosto — lo que no se ve: investigación y simulación', false, 'Meses de ingeniería antes de tocar un fierro, para llegar a la máquina sabiendo qué probar');
const ago = [
  ['Medición de campo', 'Se corrigió la geometría real del equipo y se confirmó, con el planificador Hybrid A*, que el giro cargado entra en el pasillo de 3.00 m.'],
  ['Simuladores', 'Visor del sector A con máquina de estados y consola de flota, simulación de la secuencia completa, y arreglos de la simulación física (Isaac Sim).'],
  ['Análisis de localización', 'Cómo se ubica el equipo: cámaras + ArUco + odometría. Se estudió también dónde el LiDAR degenera y dónde no.'],
  ['La decisión del EDR', 'Se descarta el Baoli (no cabe, es hidráulico) y se elige el EDR: cabe y es eléctrico. El acierto que ordenó todo lo demás.']];
ago.forEach((q, i) => {
  const x = 0.65 + (i % 2) * 6.15, y = 2.0 + Math.floor(i / 2) * 2.2;
  tarjeta(s, x, y, 5.85, 1.95, false);
  s.addShape(p.ShapeType.rect, { x, y, w: 5.85, h: 0.1, fill: { color: VERDE } });
  s.addText(q[0], { x: x + 0.35, y: y + 0.26, w: 5.2, h: 0.45, fontSize: 15, bold: true, color: TINTA, fontFace: H, margin: 0 });
  s.addText(q[1], { x: x + 0.35, y: y + 0.78, w: 5.2, h: 1.05, fontSize: 12, color: MUT2, fontFace: B, margin: 0, valign: 'top' });
});
s.addNotes('Esto contesta "y que hiciste en agosto". No se gasto nada y se de-riskeo casi todo lo de geometria, giro y localizacion.');

/* ───────── 7 · SEPTIEMBRE: EL MURO DEL DB9 ───────── */
s = p.addSlide(); fondo(s, true);
titulo(s, 'Septiembre — el muro del DB9', true, 'Un puerto de servicio que no hablaba. Un mes de pared, cero daño al equipo');
const sep = [
  ['Un puerto que no respondía', 'El técnico controlaba el equipo por un puerto de servicio (DB9) con una herramienta de concesionario. No respondía. Se investigaron varias hipótesis: serie, CAN, adaptador roto, video.', ROJO],
  ['Se probó con un fusible de menos', 'El equipo tenía un fusible faltante; se trabajó así un tiempo. Y aun metiéndole cables de diagnóstico que no eran los correctos, por disciplina de seguridad nunca se dañó nada: todo reversible, con paro, sin cortar.', HAZ],
  ['El cable, confirmado', 'Se confirmó que el cable del técnico era RS232 (serie) — y que ese camino no servía: sus señales no coinciden con el bus real del equipo. El porqué, en el diagrama de pines que sigue.', CIAN]];
sep.forEach((q, i) => {
  const y = 2.0 + i * 1.5;
  tarjeta(s, 0.65, y, 12, 1.3, true);
  s.addShape(p.ShapeType.rect, { x: 0.65, y, w: 0.1, h: 1.3, fill: { color: q[2] } });
  s.addText(q[0], { x: 1.05, y: y + 0.18, w: 11.1, h: 0.45, fontSize: 15.5, bold: true, color: HUM, fontFace: H, margin: 0 });
  s.addText(q[1], { x: 1.05, y: y + 0.6, w: 11.1, h: 0.65, fontSize: 11.5, color: MUT, fontFace: B, margin: 0, valign: 'top' });
});
s.addNotes('La historia de septiembre: pared, pero con disciplina. Nunca se cago en el equipo de nadie, aun probando cables que no eran. Y se confirmo que el serie no era.');

/* ───────── 8 · POR QUÉ ESE CABLE NUNCA CONECTÓ (pines) ───────── */
s = p.addSlide(); fondo(s, false);
titulo(s, 'Por qué ese cable nunca iba a conectar', false, 'Mismo conector físico (DB9), funciones distintas en cada pin');
db9(s, 1.5, 2.2, 'Cable del técnico — RS232 (serie)',
  { 2: ['RXD', CIAN], 3: ['TXD', CIAN], 5: ['GND', MUT2] });
db9(s, 8.85, 2.2, 'DB9 del equipo — bus CAN',
  { 3: ['CAN_L', VERDE], 8: ['CAN_H', VERDE], 6: ['+24 V', ROJO] });
s.addText('Serie: datos (2, 3) + tierra (5)', { x: 1.5, y: 3.55, w: 2.95, h: 0.3, align: 'center', fontSize: 10, color: MUT2, fontFace: B, margin: 0 });
s.addText('CAN: par diferencial (3 + 8) + 24 V (6)', { x: 8.85, y: 3.55, w: 2.95, h: 0.3, align: 'center', fontSize: 10, color: MUT2, fontFace: B, margin: 0 });
fila(s, 2.1, 4.05, 9.1, 0.44, [{ t: 'Pin', w: 1.0 }, { t: 'Cable RS232', w: 3.1 }, { t: 'DB9 del equipo (CAN)', w: 3.3 }, { t: '¿Sirve?', w: 1.7, a: 'center' }], false, true);
const pinrows = [
  ['3', 'TXD — transmite', 'CAN_L', 'no · otra función'],
  ['8', 'CTS', 'CAN_H', 'no'],
  ['5', 'GND — tierra', 'no es tierra', 'no'],
  ['6', '(sin uso)', '+24 V', '⚠ riesgo'],
  ['2', 'RXD — recibe', '— (no hay CAN)', 'no']];
pinrows.forEach((r, i) => {
  fila(s, 2.1, 4.49 + i * 0.44, 9.1, 0.44, [
    { t: r[0], w: 1.0, b: true, c: TINTA },
    { t: r[1], w: 3.1, c: MUT2 },
    { t: r[2], w: 3.3, c: TINTA, b: true },
    { t: r[3], w: 1.7, a: 'center', c: r[3][0] === '⚠' ? ROJO : MUT2 }], false);
});
s.addText('El cable serie no coincide con ninguna señal del bus, y el CAN necesita el PAR 3+8 juntos — que el serie ni toca. Por eso no conectaba "de manera simple".',
  { x: 0.65, y: 6.75, w: 12, h: 0.5, fontSize: 12.5, bold: true, color: TINTA, fontFace: B, margin: 0 });
s.addNotes('El diagrama que pidio maje. Los colores muestran que el MISMO pin tiene funcion distinta en cada lado. Pin 3 = TXD de un lado, CAN_L del otro.');

/* ───────── 9 · 1 DE OCTUBRE: EL PUNTO DE INFLEXIÓN ───────── */
s = p.addSlide(); fondo(s, true);
titulo(s, '1 de octubre — el punto de inflexión', true, 'Desde que leímos el bus CAN, volando');
tarjeta(s, 0.65, 2.0, 12, 1.25, true, PANEL);
s.addText('Descartado el serie, medimos de nuevo y el puerto resultó ser CAN. Desde que leímos el bus, el trabajo se aceleró muchísimo — de ahí en adelante, volando.',
  { x: 1.05, y: 2.0, w: 11.2, h: 1.25, fontSize: 15.5, bold: true, color: HUM, fontFace: B, margin: 0, valign: 'middle' });
const vuelo = [
  ['Antes', 'Meses descifrando el puerto, contra una pared.', ROJO],
  ['Después', 'En 3 semanas: bus leído, marcha y dirección comandadas.', VERDE],
  ['El único freno propio', 'Una semana buscando un transceptor CAN que funcionara (el primero era una unidad mala; el nuevo pasó 20/20).', HAZ]];
vuelo.forEach((q, i) => {
  const x = 0.65 + i * 4.05, y = 3.55;
  tarjeta(s, x, y, 3.8, 2.2, true);
  s.addShape(p.ShapeType.rect, { x, y, w: 3.8, h: 0.11, fill: { color: q[2] } });
  s.addText(q[0], { x: x + 0.35, y: y + 0.3, w: 3.1, h: 0.5, fontSize: 16, bold: true, color: HUM, fontFace: H, margin: 0 });
  s.addText(q[1], { x: x + 0.35, y: y + 0.95, w: 3.15, h: 1.1, fontSize: 12, color: MUT, fontFace: B, margin: 0, valign: 'top' });
});
s.addNotes('Reencuadre del "punto de impulso" como punto de inflexion. El mensaje: leer el CAN destrabo todo; desde ahi, velocidad. La unica demora propia fue el transceptor.');

/* ───────── 10 · POR QUÉ ESTOY PARADO ───────── */
s = p.addSlide(); fondo(s, false);
titulo(s, 'Por qué estoy parado — todo lo que le quitaron al equipo', false, 'Cada faltante bloquea una prueba de algo que YA está resuelto en banco');
const quit = [
  ['Hidráulica del pantógrafo', 'Le quitaron la línea hidráulica de la torre/pantógrafo (para otro equipo). Bloquea probar las funciones del multipiloto que ya descifré: elevar, extender.'],
  ['Cámara y su cable', 'No tiene la cámara ni su cable. Ese camino ya está descifrado y sé cómo leerlo cuando lo tenga — pero no puedo probarlo.'],
  ['Sensor del pedal de hombre-muerto', 'El sensor que me iban a dar para empezar a descifrar cómo emularlo se lo pusieron a otro equipo — y el que le faltaba a mi equipo también se fue a otro.'],
  ['Rodillos de dirección y la llanta directriz', 'Le quitaron los rodillos y la rueda que el timón direcciona. Por eso no puedo probar el emulador del timón que ya está validado en banco.']];
quit.forEach((q, i) => {
  const x = 0.65 + (i % 2) * 6.15, y = 2.0 + Math.floor(i / 2) * 2.05;
  tarjeta(s, x, y, 5.85, 1.8, false);
  s.addShape(p.ShapeType.rect, { x, y, w: 0.09, h: 1.8, fill: { color: ROJO } });
  s.addText(q[0], { x: x + 0.3, y: y + 0.2, w: 5.4, h: 0.5, fontSize: 14.5, bold: true, color: TINTA, fontFace: H, margin: 0 });
  s.addText(q[1], { x: x + 0.3, y: y + 0.72, w: 5.4, h: 1.0, fontSize: 11.5, color: MUT2, fontFace: B, margin: 0, valign: 'top' });
});
s.addText('No es que falte ingeniería: falta una máquina completa donde probar lo que ya resolví.',
  { x: 0.65, y: 6.3, w: 12, h: 0.5, fontSize: 13.5, bold: true, color: TINTA, fontFace: B, margin: 0 });
s.addNotes('Las 4 piezas que le sacaron, cada una a otro equipo. Todas bloquean PRUEBAS de cosas ya resueltas, no el trabajo de resolverlas.');

/* ───────── 11 · REPARAR EL MT 122 ───────── */
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
s.addNotes('Canibalizar sale mas caro y mata un activo que podria rentar. Reparar recupera ese activo.');

/* ───────── 12 · DOBLE RETORNO ───────── */
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

/* ───────── 13 · EL CAMINO QUE SIGUE ───────── */
s = p.addSlide(); fondo(s, true);
titulo(s, 'El camino que sigue', true, 'El siguiente paso es odometría + Kalman con ArUco. El LiDAR sigue en el plan, después de formalizar');
const cam = [
  ['1', 'Odometría', 'El equipo ya reporta velocidad de tracción y ángulo de dirección en su bus. Integrando ambos se estima el desplazamiento: la base de la posición, sin sensores nuevos.', CIAN],
  ['2', 'Fusión Kalman + ArUco', 'Un filtro de Kalman fusiona esa odometría con la pose de los ArUco en los racks: la odometría da continuidad, el ArUco corrige la deriva y fija la posición absoluta. Siguiente paso, solo cámaras.', HAZ],
  ['3', 'LiDAR / SLAM', 'Mapeo en vivo del pasillo y detección de obstáculos. Suma robustez y una capa de seguridad. Sigue en el plan; entra después de formalizar, no se descarta.', VERDE]];
cam.forEach((q, i) => {
  const y = 2.0 + i * 1.5;
  tarjeta(s, 0.65, y, 12, 1.3, true);
  chip(s, q[0], 1.0, y + 0.44, q[3]);
  s.addText(q[1], { x: 1.65, y: y + 0.28, w: 3.3, h: 0.5, fontSize: 16, bold: true, color: HUM, fontFace: H, margin: 0 });
  s.addText(q[2], { x: 5.0, y: y + 0.16, w: 7.4, h: 1.05, fontSize: 11.5, color: MUT, fontFace: B, margin: 0, valign: 'middle' });
});
s.addNotes('Reescrito sin "cuanto me movi". Mismo largo, mas tecnico. El LiDAR sigue en el plan, despues de formalizar.');

/* ───────── 14 · EL AULA ───────── */
s = p.addSlide(); fondo(s, false);
titulo(s, 'El Aula — el banco de pruebas', false, 'En una etapa más adelante, dentro del taller');
const aula = [
  ['Reconfigurar espacio muerto', 'En el taller hay espacio muerto ocupado por equipamiento que no se usa y por racks. Reorganizándolo se libera un espacio de 3.0 m de ancho × 6.0 m de largo — sin deshacer el taller.', CIAN],
  ['Un ambiente cerrado y real', 'Es un ambiente cerrado, como el de cualquier almacén de verdad —incluido RETHINK—. Reproduce las condiciones reales donde el equipo va a operar.', HAZ],
  ['La luz inestable juega a favor', 'La iluminación inestable que tendríamos no es un problema: probar con luz imperfecta hace la visión (ArUco) y la robótica más robustas para el campo.', VERDE]];
aula.forEach((q, i) => {
  const y = 1.95 + i * 1.5;
  tarjeta(s, 0.65, y, 12, 1.3, false);
  s.addShape(p.ShapeType.rect, { x: 0.65, y, w: 0.09, h: 1.3, fill: { color: q[2] } });
  s.addText(q[0], { x: 1.0, y: y + 0.2, w: 11.3, h: 0.45, fontSize: 17, bold: true, color: TINTA, fontFace: H, margin: 0 });
  s.addText(q[1], { x: 1.0, y: y + 0.66, w: 11.3, h: 0.6, fontSize: 13, color: MUT2, fontFace: B, margin: 0, valign: 'top' });
});
s.addText('En esta etapa se prueba el ciclo con el pantógrafo (sin uñas) + un sensor de altura calibrado.',
  { x: 0.65, y: 6.5, w: 12, h: 0.4, fontSize: 11.5, italic: true, color: MUT2, fontFace: B, margin: 0 });
s.addNotes('Se quito el plano a pedido. El Aula = reconfigurar espacio muerto (equipo no usado + racks) para un espacio 3x6, ambiente cerrado como RETHINK, y la luz inestable ayuda a la robustez.');

/* ───────── 15 · QUIÉN PONE QUÉ ───────── */
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
s.addNotes('Desarma el riesgo para Omar: no se le pide comprar hardware. El NRE y el computo los pone maje.');

/* ───────── 16 · CÓMPUTO POR ETAPAS ───────── */
s = p.addSlide(); fondo(s, false);
titulo(s, 'El cómputo, por etapas — según la inversión de cada una', false, 'Las cámaras no reemplazan al LiDAR: arrancan barato; el LiDAR agrega seguridad, mapeo y robustez');
const et = [
  ['Etapa 1 · Odometría + Kalman/ArUco', 'Jetson Orin 8 GB + 2 webcams que ya tengo. La pongo yo. Más difícil (sin la red de seguridad del LiDAR), pero suficiente para localizar y autofinanciada.', CIAN],
  ['Etapa 2 · LiDAR (tras formalizar)', 'El Unitree L2 que ya definimos. Suma SLAM, mapeo en vivo y detección de obstáculos: robótica más robusta y una capa de seguridad. El L2 no cambia.', VERDE]];
et.forEach((q, i) => {
  const x = 0.65 + i * 6.15, y = 2.0;
  tarjeta(s, x, y, 5.85, 2.5, false);
  s.addShape(p.ShapeType.rect, { x, y, w: 5.85, h: 0.12, fill: { color: q[2] } });
  s.addText(q[0], { x: x + 0.35, y: y + 0.32, w: 5.2, h: 0.75, fontSize: 15, bold: true, color: TINTA, fontFace: H, margin: 0 });
  s.addText(q[1], { x: x + 0.35, y: y + 1.12, w: 5.2, h: 1.25, fontSize: 12, color: MUT2, fontFace: B, margin: 0, valign: 'top' });
});
tarjeta(s, 0.65, 4.75, 12, 1.0, false, 'F3EEDC');
s.addText('A decidir: el cómputo del LiDAR — 8 GB vs 16 GB de GPU.', { x: 1.0, y: 4.85, w: 11.3, h: 0.35, fontSize: 13, bold: true, color: TINTA, fontFace: B, margin: 0 });
s.addText('El L2 no cambia; la pregunta es cuánta GPU para correrlo. (La simulación Isaac Sim es aparte: corre en una PC, no en la Jetson del equipo.)',
  { x: 1.0, y: 5.2, w: 11.3, h: 0.5, fontSize: 11.5, color: MUT2, fontFace: B, margin: 0, valign: 'top' });
s.addText('Sin LiDAR es más barato pero se pierde una capa de seguridad y el mapeo. Con LiDAR: más robusto, más seguro — y sigue siendo el plan.',
  { x: 0.65, y: 6.05, w: 12, h: 0.6, fontSize: 12.5, bold: true, color: MUT2, fontFace: B, margin: 0 });
s.addNotes('Por etapas, no "camaras reemplazan LiDAR". Etapa 1 autofinanciada 8GB+webcams. Etapa 2 el L2. Pendiente: 8 vs 16 GB para el LiDAR. Isaac Sim es problema de PC, aparte.');

/* ───────── 17 · EL PEDIDO ───────── */
s = p.addSlide(); fondo(s, true);
titulo(s, 'Lo que necesito de vos', true, 'Nada de esto es un cheque por hardware');
const ped = [
  ['1', 'Reparar el MT 122 — o permiso de pruebas', 'Reparar el 122 para tenerlo de plataforma. Si no se puede ya: permiso para pruebas reversibles en equipos de mantenimiento preventivo, solo para la odometría. Nada se corta ni se mueve; van y vuelven igual.', VERDE],
  ['2', 'Mi propio equipo para la etapa fuerte', 'Pasada la odometría: el 122 para pruebas extensivas de Kalman + ArUco, instalar el cómputo y el LiDAR, diseñar la caja 3D del circuito y formalizar.', CIAN],
  ['3', 'El Aula — reorganizar estantes', 'Liberar un pasillo de 3 × 6 m reorganizando estantes. No deshace el taller.', HAZ]];
ped.forEach((q, i) => {
  const y = 1.95 + i * 1.3;
  tarjeta(s, 0.65, y, 12, 1.15, true);
  chip(s, q[0], 1.0, y + 0.36, q[3]);
  s.addText(q[1], { x: 1.62, y: y + 0.16, w: 4.9, h: 0.85, fontSize: 14.5, bold: true, color: HUM, fontFace: B, margin: 0, valign: 'middle' });
  s.addText(q[2], { x: 6.65, y: y + 0.14, w: 5.75, h: 0.9, fontSize: 10.5, color: MUT, fontFace: B, margin: 0, valign: 'middle' });
});
tarjeta(s, 0.65, 5.9, 12, 0.85, true, PANEL);
s.addText('El software ya está y el NRE lo pongo yo. Lo que pido es un lugar y un equipo donde probarlo.',
  { x: 1.05, y: 5.9, w: 11.2, h: 0.85, fontSize: 15.5, bold: true, color: HAZ, fontFace: B, margin: 0, valign: 'middle' });
s.addNotes('Pedido reestructurado: 122 (o permiso de pruebas reversibles en mantenimiento para odometria), luego equipo propio para la etapa fuerte, y El Aula = reorganizar estantes.');

p.writeFile({ fileName: 'presentaciones/TaTa_Estado_y_Pedido_Omar.pptx' }).then(() => console.log('deck OMAR o3 listo'));
