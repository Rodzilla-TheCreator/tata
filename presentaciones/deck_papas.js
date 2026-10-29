// deck_papas.js — TaTa · En qué estoy trabajando (versión para mis papás)
// Lenguaje llano, sin jerga. Honesto: qué construí, por qué es difícil, por qué
// ahora estoy esperando una máquina (no es falta de trabajo). Genera TaTa_Para_mis_papas.pptx
const pptx = require('pptxgenjs');
const p = new pptx();
p.layout = 'LAYOUT_WIDE';
p.author = 'TaTa'; p.title = 'TaTa · En qué estoy trabajando';

const OSCURO = '14171C', CLARO = 'F7F6F2', TINTA = '1A1D23';
const HUM = 'ECEBE6', MUT = '8B949E', MUT2 = '5B6470';
const HAZ = 'E0A82E', VERDE = '2FA866', AZUL = '2E6FB0';
const H = 'Cambria', B = 'Calibri';
const W = 13.3, HT = 7.5;

const sombra = () => ({ type: 'outer', color: '000000', blur: 10, offset: 2, angle: 90, opacity: 0.18 });
function fondo(s, dark) { s.background = { color: dark ? OSCURO : CLARO }; }
function titulo(s, txt, dark, sub) {
  s.addText(txt, { x: 0.7, y: 0.5, w: W - 1.4, h: 0.9, fontSize: 32, bold: true,
    color: dark ? HUM : TINTA, fontFace: H, margin: 0 });
  if (sub) s.addText(sub, { x: 0.7, y: 1.35, w: W - 1.4, h: 0.45, fontSize: 15,
    color: dark ? MUT : MUT2, fontFace: B, margin: 0 });
}
function tarjeta(s, x, y, w, h, dark, tint) {
  s.addShape(p.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.1,
    fill: { color: tint || (dark ? '20242B' : 'FFFFFF') }, shadow: sombra() });
}

/* ───────── 1 · PORTADA ───────── */
let s = p.addSlide(); fondo(s, true);
s.addShape(p.ShapeType.rect, { x: 1.0, y: 3.15, w: 1.6, h: 0.05, fill: { color: HAZ } });
s.addText('En qué estoy\ntrabajando', { x: 0.95, y: 1.7, w: 11, h: 2.2, fontSize: 48, bold: true, color: HUM, fontFace: H, lineSpacing: 54, margin: 0 });
s.addText('Un proyecto de ingeniería dentro de Montasa', { x: 1.0, y: 3.45, w: 11, h: 0.5, fontSize: 18, color: HAZ, fontFace: B, margin: 0 });
s.addText('Hacer que los montacargas de un almacén se manejen solos — sin comprar máquinas nuevas.',
  { x: 1.0, y: 4.2, w: 10.5, h: 0.8, fontSize: 15, color: MUT, fontFace: B, margin: 0 });
s.addNotes('Para mis papas. Tono tranquilo y concreto. La idea que se lleven: esto es trabajo real de ingenieria, con una empresa de respaldo.');

/* ───────── 2 · QUÉ ES ───────── */
s = p.addSlide(); fondo(s, false);
titulo(s, 'Qué es, en una frase', false);
tarjeta(s, 0.7, 2.0, 11.9, 1.9, false);
s.addText('Agarro un montacargas que un almacén ya usa todos los días, y le instalo un kit que lo vuelve capaz de moverse y acomodar la carga solo — por etapas, empezando por lo simple.',
  { x: 1.1, y: 2.0, w: 11.1, h: 1.9, fontSize: 19, color: TINTA, fontFace: B, margin: 0, valign: 'middle', lineSpacing: 28 });
const qe = [
  ['No es comprar un robot', 'Se adapta la máquina que ya tienen. Es mucho más barato.', VERDE],
  ['Es dentro de Montasa', 'La empresa donde trabaja la familia. No es un invento suelto.', AZUL]];
qe.forEach((q, i) => {
  const x = 0.7 + i * 6.15, y = 4.3;
  tarjeta(s, x, y, 5.75, 1.7, false);
  s.addShape(p.ShapeType.rect, { x, y, w: 5.75, h: 0.1, fill: { color: q[2] } });
  s.addText(q[0], { x: x + 0.4, y: y + 0.3, w: 5.0, h: 0.5, fontSize: 17, bold: true, color: TINTA, fontFace: H, margin: 0 });
  s.addText(q[1], { x: x + 0.4, y: y + 0.9, w: 5.0, h: 0.7, fontSize: 13.5, color: MUT2, fontFace: B, margin: 0 });
});

/* ───────── 3 · POR QUÉ ES DIFÍCIL ───────── */
s = p.addSlide(); fondo(s, true);
titulo(s, 'Por qué es ingeniería de verdad', true, 'Y no algo que se baja de internet');
const dif = [
  ['Hay que “hablarle” a la máquina', 'El montacargas tiene una computadora interna cerrada. Tuve que descubrir, midiendo con instrumentos, cómo darle órdenes. Nadie lo había hecho en estos equipos.'],
  ['Cada cable es un misterio', 'Averiguar qué hace cada señal eléctrica es el trabajo lento y caro. Una vez resuelto, sirve para todas las máquinas iguales.'],
  ['La seguridad es seria', 'Mover una máquina de 2 toneladas sola exige hacerlo bien. Trabajo con la máquina frenada, con un botón de paro en la mano, paso por paso.']];
dif.forEach((q, i) => {
  const y = 2.05 + i * 1.55;
  tarjeta(s, 0.7, y, 11.9, 1.35, true);
  s.addText(q[0], { x: 1.1, y: y + 0.2, w: 11.1, h: 0.5, fontSize: 16, bold: true, color: HAZ, fontFace: H, margin: 0 });
  s.addText(q[1], { x: 1.1, y: y + 0.68, w: 11.1, h: 0.6, fontSize: 13, color: MUT, fontFace: B, margin: 0, valign: 'top' });
});

/* ───────── 4 · QUÉ YA LOGRÉ ───────── */
s = p.addSlide(); fondo(s, false);
titulo(s, 'Lo que ya logré', false, 'Sin gastar dinero de la empresa');
const log = [
  ['Entendí la computadora del equipo', 'Ya sé leer lo que piensa el montacargas por dentro.', VERDE],
  ['Lo hago avanzar con una orden', 'Logré darle la orden de moverse, y la máquina la aceptó. Probado en mi mesa.', VERDE],
  ['Reemplacé el volante', 'Hice un circuito que imita el sensor del volante para manejar la dirección. Funciona.', VERDE],
  ['Construí los simuladores', 'Programas que muestran el almacén y la máquina trabajando, para probar sin riesgo.', VERDE]];
log.forEach((l, i) => {
  const x = 0.7 + (i % 2) * 6.15, y = 2.0 + Math.floor(i / 2) * 2.0;
  tarjeta(s, x, y, 5.75, 1.75, false);
  s.addShape(p.ShapeType.ellipse, { x: x + 0.35, y: y + 0.32, w: 0.4, h: 0.4, fill: { color: VERDE } });
  s.addText('✓', { x: x + 0.35, y: y + 0.32, w: 0.4, h: 0.4, align: 'center', valign: 'middle', fontSize: 16, bold: true, color: 'FFFFFF', fontFace: B, margin: 0 });
  s.addText(l[0], { x: x + 0.95, y: y + 0.28, w: 4.6, h: 0.5, fontSize: 15, bold: true, color: TINTA, fontFace: H, margin: 0, valign: 'middle' });
  s.addText(l[1], { x: x + 0.4, y: y + 0.9, w: 5.1, h: 0.75, fontSize: 12.5, color: MUT2, fontFace: B, margin: 0, valign: 'top' });
});

/* ───────── 5 · POR QUÉ PARECE LENTO ───────── */
s = p.addSlide(); fondo(s, true);
titulo(s, 'Por qué ahora estoy esperando', true, 'Y por qué no depende de mí');
tarjeta(s, 0.7, 2.1, 11.9, 1.7, true);
s.addText('Para el siguiente paso necesito un montacargas que encienda y esté dedicado al proyecto. El que estaba usando le quitaron piezas para reparar otros, y el repuesto que esperaba se lo pusieron a otra máquina.',
  { x: 1.1, y: 2.1, w: 11.1, h: 1.7, fontSize: 16, color: HUM, fontFace: B, margin: 0, valign: 'middle', lineSpacing: 24 });
tarjeta(s, 0.7, 4.1, 11.9, 1.9, true, '20242B');
s.addText('No es falta de trabajo.', { x: 1.1, y: 4.35, w: 11.1, h: 0.5, fontSize: 20, bold: true, color: HAZ, fontFace: H, margin: 0 });
s.addText('El trabajo de ingeniería está hecho. Lo que falta es que la empresa me dé una máquina funcional — y eso ya lo estoy gestionando con el dueño de Montasa.',
  { x: 1.1, y: 4.95, w: 11.1, h: 0.9, fontSize: 14.5, color: MUT, fontFace: B, margin: 0, valign: 'top' });
s.addNotes('Este es el slide que mas les importa a ellos. Dejar claro: no esta parado por vagancia ni por no saber. Esta esperando una maquina, y ya movio la gestion.');

/* ───────── 6 · HACIA DÓNDE VA ───────── */
s = p.addSlide(); fondo(s, false);
titulo(s, 'Hacia dónde va', false, 'Y con el respaldo de la empresa');
const via = [
  ['Ahora', 'Reparar una máquina para usarla de plataforma y terminar de probar lo que ya construí.', AZUL],
  ['Después', 'Que el montacargas se ubique solo en el pasillo, con cámaras, y mueva la carga sin chofer.', HAZ],
  ['La meta', 'Un kit que Montasa pueda vender e instalar en los montacargas de sus clientes.', VERDE]];
via.forEach((q, i) => {
  const x = 0.7 + i * 4.05, y = 2.2;
  tarjeta(s, x, y, 3.8, 3.0, false);
  s.addShape(p.ShapeType.rect, { x, y, w: 3.8, h: 0.12, fill: { color: q[2] } });
  s.addText(q[0], { x: x + 0.35, y: y + 0.4, w: 3.2, h: 0.5, fontSize: 19, bold: true, color: TINTA, fontFace: H, margin: 0 });
  s.addText(q[1], { x: x + 0.35, y: y + 1.1, w: 3.15, h: 1.7, fontSize: 13.5, color: MUT2, fontFace: B, margin: 0, valign: 'top', lineSpacing: 20 });
});
tarjeta(s, 0.7, 5.5, 11.9, 0.95, false, 'ECE7DA');
s.addText('El dueño de Montasa ya está al tanto y me dio el visto bueno para seguir.',
  { x: 1.1, y: 5.5, w: 11.1, h: 0.95, fontSize: 15, bold: true, color: TINTA, fontFace: B, margin: 0, valign: 'middle' });

/* ───────── 7 · NO ES UN PROYECTO CUALQUIERA ───────── */
s = p.addSlide(); fondo(s, false);
titulo(s, 'Esto no es un proyecto cualquiera', false, 'Es experiencia de ingeniería que vale en el mercado laboral del mundo');
tarjeta(s, 0.7, 1.95, 11.9, 1.0, false);
s.addText('Lo que estoy aprendiendo haciendo esto es exactamente lo que buscan las empresas de ingeniería — en Europa y donde sea.',
  { x: 1.1, y: 1.95, w: 11.1, h: 1.0, fontSize: 15.5, bold: true, color: TINTA, fontFace: B, margin: 0, valign: 'middle' });
const sk = [
  ['Ingeniería inversa de sistemas', 'Leerle y hablarle al bus de una máquina cerrada.'],
  ['Sistemas embebidos y firmware', 'Programar los microcontroladores que mandan.'],
  ['Control y automatización', 'Manejar maquinaria pesada con seguridad.'],
  ['Robótica autónoma', 'Sensores, cámaras y ubicación en el espacio.']];
sk.forEach((q, i) => {
  const x = 0.7 + (i % 2) * 6.15, y = 3.2 + Math.floor(i / 2) * 1.25;
  tarjeta(s, x, y, 5.75, 1.1, false);
  s.addShape(p.ShapeType.rect, { x, y, w: 0.09, h: 1.1, fill: { color: AZUL } });
  s.addText(q[0], { x: x + 0.35, y: y + 0.18, w: 5.3, h: 0.4, fontSize: 14, bold: true, color: TINTA, fontFace: H, margin: 0 });
  s.addText(q[1], { x: x + 0.35, y: y + 0.58, w: 5.3, h: 0.45, fontSize: 12, color: MUT2, fontFace: B, margin: 0 });
});
s.addText('Pocos ingenieros recién salidos las tienen — y menos aún las han hecho con sus manos en una máquina real.',
  { x: 0.7, y: 5.9, w: 11.9, h: 0.5, fontSize: 13, italic: true, color: MUT2, fontFace: B, margin: 0 });

/* ───────── 8 · EL PLAN TIENE RED ───────── */
s = p.addSlide(); fondo(s, true);
titulo(s, 'El plan tiene red', true, 'Pase lo que pase con el proyecto, esta experiencia ya me abrió una puerta');
const red = [
  ['Si sale', 'Levanto mi empresa, vendo el primer TaTa, consigo el Aula — y sigo construyendo esto acá.', VERDE],
  ['Si no sale', 'Esta misma experiencia me abre un trabajo de ingeniería en una empresa en Europa.', HAZ],
  ['De cualquier forma', 'No es una apuesta de todo o nada. Gano experiencia que vale tenga o no éxito el proyecto.', AZUL]];
red.forEach((q, i) => {
  const x = 0.7 + i * 4.05, y = 2.2;
  tarjeta(s, x, y, 3.8, 2.9, true);
  s.addShape(p.ShapeType.rect, { x, y, w: 3.8, h: 0.12, fill: { color: q[2] } });
  s.addText(q[0], { x: x + 0.35, y: y + 0.4, w: 3.2, h: 0.5, fontSize: 18, bold: true, color: HUM, fontFace: H, margin: 0 });
  s.addText(q[1], { x: x + 0.35, y: y + 1.1, w: 3.15, h: 1.6, fontSize: 13, color: MUT, fontFace: B, margin: 0, valign: 'top', lineSpacing: 20 });
});
tarjeta(s, 0.7, 5.45, 11.9, 1.0, true, '20242B');
s.addText('Esto no es alejarme de conseguir trabajo. Es cómo consigo uno — y uno que pocos pueden hacer.',
  { x: 1.1, y: 5.45, w: 11.1, h: 1.0, fontSize: 16, bold: true, color: HAZ, fontFace: B, margin: 0, valign: 'middle' });
s.addNotes('Este slide contesta directo la angustia de "conseguia trabajo". La respuesta: esto ES el camino al trabajo, y a uno mejor.');

/* ───────── 9 · POR QUÉ NO NOS ENTENDEMOS ───────── */
s = p.addSlide(); fondo(s, false);
titulo(s, 'Por qué a veces no nos entendemos', false);
tarjeta(s, 0.7, 1.9, 11.9, 1.2, false);
s.addText('Que no entiendan lo que hago no significa que no tenga sentido. Significa que hablamos lenguajes distintos — y este todavía no lo compartimos.',
  { x: 1.1, y: 1.9, w: 11.1, h: 1.2, fontSize: 16, bold: true, color: TINTA, fontFace: B, margin: 0, valign: 'middle', lineSpacing: 24 });
tarjeta(s, 0.7, 3.35, 11.9, 1.3, false);
s.addText('No soy un genio que lo sabe todo. Ustedes tampoco están equivocados. Es solo un idioma que yo aprendí y ustedes no — como el que no sabe de motores no entiende al mecánico, y no por eso el mecánico está loco.',
  { x: 1.1, y: 3.35, w: 11.1, h: 1.3, fontSize: 14.5, color: MUT2, fontFace: B, margin: 0, valign: 'middle', lineSpacing: 22 });
tarjeta(s, 0.7, 4.9, 11.9, 1.55, false, 'ECE7DA');
s.addText('Lo que a veces se ve como que “me cuesta arrancar” es, en realidad, estar metido de lleno en algo que nadie más aquí está haciendo. Les pido confianza mientras lo cierro. El trabajo habla por mí — y aquí está.',
  { x: 1.1, y: 4.9, w: 11.1, h: 1.55, fontSize: 15, bold: true, color: TINTA, fontFace: B, margin: 0, valign: 'middle', lineSpacing: 23 });
s.addNotes('El slide delicado. Puente, no reclamo: valida lo mio sin acusar. La analogia del mecanico aterriza en esta familia. Pedir confianza, no razon.');

/* ───────── 10 · CIERRE ───────── */
s = p.addSlide(); fondo(s, true);
s.addShape(p.ShapeType.rect, { x: 1.0, y: 2.75, w: 1.6, h: 0.05, fill: { color: HAZ } });
s.addText('Esto es lo que estoy\nconstruyendo.', { x: 0.95, y: 1.75, w: 11, h: 1.6, fontSize: 36, bold: true, color: HUM, fontFace: H, lineSpacing: 44, margin: 0 });
s.addText('Toma tiempo porque nadie lo ha hecho antes en estos equipos. Pero ya funciona en mi mesa, la empresa está detrás, y si no sale, me abre otra puerta.',
  { x: 1.0, y: 3.75, w: 10.8, h: 1.2, fontSize: 16, color: MUT, fontFace: B, margin: 0, lineSpacing: 24 });
s.addText('De cualquier forma, no es tiempo perdido.', { x: 1.0, y: 5.0, w: 10.8, h: 0.5, fontSize: 17, bold: true, color: HAZ, fontFace: B, margin: 0 });
s.addNotes('Cerrar tranquilo. No prometer fechas. El mensaje: trabajo real, respaldado, con red, en progreso.');

p.writeFile({ fileName: 'presentaciones/TaTa_Para_mis_papas.pptx' }).then(() => console.log('deck PAPAS listo'));
