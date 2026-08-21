const pptx = require('pptxgenjs');
const p = new pptx();
p.layout = 'LAYOUT_WIDE';               // 13.3 x 7.5
p.author = 'TaTa'; p.company = 'TaTa · Tecnología Avanzada de Transporte Autónomo';
p.title = 'TaTa · Automatización de montacargas — RETHINK / ELCATEX';

const OSCURO = '14171C', PANEL = '20242B', CLARO = 'F4F5F7', TINTA = '1A1D23';
const HUM = 'ECEBE6', MUT = '8B949E', MUT2 = '5B6470';
const HAZ = 'F5C518', VERDE = '39D98A', ROJO = 'FF5A52', CIAN = '37C3FF';
const H = 'Cambria', B = 'Calibri';
const W = 13.3, HT = 7.5;

const sombra = () => ({ type: 'outer', color: '000000', blur: 12, offset: 3, angle: 90, opacity: 0.28 });

function fondo(s, dark) { s.background = { color: dark ? OSCURO : CLARO }; }

// chip numerado: el motivo que se repite en todo el deck
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
  s.addText(valor, { x, y, w, h: 0.72, fontSize: 40, bold: true, color: col,
    fontFace: H, margin: 0, align: 'left' });
  s.addText(etiqueta, { x, y: y + 0.72, w, h: 0.5, fontSize: 11.5,
    color: dark ? MUT : MUT2, fontFace: B, margin: 0 });
}

/* ───────── 1 · PORTADA ───────── */
let s = p.addSlide(); fondo(s, true);
s.addImage({ path: 'im_general.jpg', x: 0, y: 0, w: W, h: HT, sizing: { type: 'cover', w: W, h: HT }, transparency: 74 });
s.addShape(p.ShapeType.rect, { x: 0, y: 0, w: W, h: HT, fill: { color: OSCURO, transparency: 14 } });
s.addShape(p.ShapeType.rect, { x: 0.75, y: 2.12, w: 1.5, h: 0.045, fill: { color: HAZ } });
s.addText('TaTa', { x: 0.75, y: 0.75, w: 6, h: 1.0, fontSize: 54, bold: true, color: HAZ, fontFace: H, margin: 0 });
s.addText('Tecnología Avanzada de Transporte Autónomo', { x: 0.78, y: 1.72, w: 8, h: 0.4,
  fontSize: 14, color: MUT, fontFace: B, margin: 0 });
s.addText('Sus montacargas, manejándose solos.\nSin comprar montacargas nuevos.', { x: 0.75, y: 2.25,
  w: 8.6, h: 1.5, fontSize: 27, bold: true, color: HUM, fontFace: H, lineSpacing: 34, margin: 0 });
s.addText('RETHINK · ELCATEX', { x: 0.75, y: 6.35, w: 6, h: 0.4, fontSize: 15, bold: true, color: HAZ, fontFace: B, margin: 0 });
s.addText('Lo que encontramos en su almacén', { x: 0.75, y: 6.75, w: 6, h: 0.35,
  fontSize: 12, color: MUT, fontFace: B, margin: 0 });
s.addNotes('Arrancar dando las gracias por el acceso al plano y por la visita. Tono de plática, no de pitch. La idea: venimos a contarles lo que vimos, no a venderles.');

/* ───────── 2 · AGENDA ───────── */
s = p.addSlide(); fondo(s, true);
titulo(s, 'De qué vamos a platicar', true, 'Cuatro cosas, y la tercera la manejan ustedes');
const ag = [
  ['Nos metimos en su plano', 'Lo reconstruimos en 3D para poder caminarlo', HAZ],
  ['Encontramos tres cosas', 'Ninguna es mala noticia, pero hay que decidirlas antes de automatizar', ROJO],
  ['Se lo trajimos para que lo manejen', 'Su almacén, en una simulación, con un montacargas de verdad', CIAN],
  ['Y así es como se vería', 'El kit, lo que cuesta y por dónde empezaríamos', VERDE],
];
ag.forEach((a, i) => {
  const y = 2.05 + i * 1.18;
  tarjeta(s, 0.65, y, W - 1.3, 1.0, true);
  chip(s, i + 1, 1.0, y + 0.29, a[2]);
  s.addText(a[0], { x: 1.62, y: y + 0.17, w: 6.2, h: 0.35, fontSize: 16, bold: true, color: HUM, fontFace: B, margin: 0 });
  s.addText(a[1], { x: 1.62, y: y + 0.53, w: 10.3, h: 0.35, fontSize: 12, color: MUT, fontFace: B, margin: 0 });
});
s.addNotes('Marcar el orden en voz alta: primero lo suyo, al final lo nuestro. Si se invierte el orden, esto se vuelve una visita de vendedor.');

/* ───────── 3 · LO QUE HICIMOS ───────── */
s = p.addSlide(); fondo(s, false);
titulo(s, 'Nos metimos en su plano', false,
  'Agarramos el RETHINK_2026.dwg y lo volvimos un almacén 3D que se puede caminar');
s.addImage({ path: 'im_general.jpg', x: 6.55, y: 1.95, w: 6.15, h: 3.46, sizing: { type: 'cover', w: 6.15, h: 3.46 }, shadow: sombra() });
const st3 = [['2,138', 'ubicaciones de rack, contadas una por una', HAZ, 0.65, 1.95],
             ['29', 'filas de rack en 5 bloques', TINTA, 3.55, 1.95],
             ['1,142', 'pedazos de muro extraídos', TINTA, 0.65, 3.55],
             ['9.20 m', 'a cumbrera, según su propio plano', TINTA, 3.55, 3.55]];
st3.forEach(v => stat(s, v[3], v[4], 2.7, v[0], v[1], v[2], false));
tarjeta(s, 0.65, 5.55, 12, 1.35, false);
s.addText('Todo lo que van a ver hoy salió de su archivo. No estamos suponiendo nada de cómo trabajan: lo medimos.',
  { x: 1.1, y: 5.55, w: 11.1, h: 1.35, fontSize: 14, italic: true, color: TINTA, fontFace: H, margin: 0, valign: 'middle' });
s.addNotes('Este slide es el que compra credibilidad. Decirlo simple: no les preguntamos, lo medimos. Si preguntan cómo, contar que el DWG no abría ni en su laptop y hubo que convertirlo.');

/* ───────── 4 · TRES SECTORES ───────── */
s = p.addSlide(); fondo(s, false);
titulo(s, 'Su plano no es un piso: son tres propuestas',
  false, 'Están dibujadas una al lado de la otra en el mismo archivo. Las separamos para poder hablar de cada una.');
s.addImage({ path: 'im_sectores.jpg', x: 0.65, y: 1.95, w: 12, h: 2.5, sizing: { type: 'cover', w: 12, h: 2.5 }, shadow: sombra() });
const sec = [['A · Actual', 'LAYOUT RETHINK, 1er nivel (nov-2024)', '930 ubicaciones', CIAN],
             ['B · Ampliación', 'Naves L4-A/B/C, 1,736.64 m² proyectados', '1,208 ubicaciones', HAZ],
             ['C · Propuesta IT', 'Planta primer nivel — bodega sin racks', 'Sin diseñar', VERDE]];
sec.forEach((c, i) => {
  const x = 0.65 + i * 4.06;
  tarjeta(s, x, 4.7, 3.82, 2.2, false);
  s.addShape(p.ShapeType.ellipse, { x: x + 0.3, y: 4.98, w: 0.3, h: 0.3, fill: { color: c[3] } });
  s.addText(c[0], { x: x + 0.72, y: 4.96, w: 3, h: 0.35, fontSize: 14, bold: true, color: TINTA, fontFace: B, margin: 0 });
  s.addText(c[1], { x: x + 0.3, y: 5.5, w: 3.3, h: 0.6, fontSize: 11, color: MUT2, fontFace: B, margin: 0, valign: 'top' });
  s.addText(c[2], { x: x + 0.3, y: 6.15, w: 3.3, h: 0.45, fontSize: 16, bold: true, color: c[3], fontFace: H, margin: 0 });
});
s.addNotes('Aquí toca preguntar de frente: ¿cuál de las tres es la que se va a construir? Todo lo demás depende de eso. Si no lo saben todavía, ese ya es un hallazgo.');

/* ───────── 5 · HALLAZGO 1 · MAXICUBOS ───────── */
s = p.addSlide(); fondo(s, false);
chip(s, 1, 0.65, 0.46, HAZ);
s.addText('Ustedes no mueven tarimas, mueven maxicubos', { x: 1.27, y: 0.42, w: 11.4, h: 0.6,
  fontSize: 29, bold: true, color: TINTA, fontFace: H, margin: 0 });
s.addText('Su plano lo dice con todas sus letras: "RACK MAXICUBOS A 4 Y 5 NIVELES". Y hay lavado, sucios y limpios.',
  { x: 1.27, y: 1.12, w: 11.4, h: 0.4, fontSize: 13.5, color: MUT2, fontFace: B, margin: 0 });
s.addImage({ path: 'im_maxicubos.jpg', x: 8.15, y: 1.85, w: 4.5, h: 4.92, sizing: { type: 'cover', w: 4.5, h: 4.92 }, shadow: sombra() });
const mx = [['1.00 × 1.20 m', 'Esa es su unidad de carga. No es una tarima americana ni europea.'],
            ['470 en el primer nivel', 'Contados uno por uno en el plano, no estimados.'],
            ['Los vacíos también viajan', 'Lavado, limpios, sucios. Hay un circuito de retorno, no solo de producto.']];
mx.forEach((m, i) => {
  const y = 1.95 + i * 1.28;
  s.addText(m[0], { x: 0.65, y, w: 7.1, h: 0.45, fontSize: 20, bold: true, color: HAZ, fontFace: H, margin: 0 });
  s.addText(m[1], { x: 0.65, y: y + 0.5, w: 7.1, h: 0.62, fontSize: 13, color: TINTA, fontFace: B, margin: 0, valign: 'top' });
});
tarjeta(s, 0.65, 5.95, 7.1, 0.85, false, TINTA);
s.addText('Cualquier robot que les vendan tiene que saber manejar el retorno de vacíos, no solo el producto.',
  { x: 1.0, y: 5.95, w: 6.5, h: 0.85, fontSize: 12.5, bold: true, color: HAZ, fontFace: B, margin: 0, valign: 'middle' });
s.addNotes('Esto los sorprende. Nadie llega a una reunión sabiendo que manejan maxicubos. Sirve para probar que sí leímos el plano en serio.');

/* ───────── 6 · HALLAZGO 2 · PASILLOS ───────── */
s = p.addSlide(); fondo(s, true);
chip(s, 2, 0.65, 0.46, ROJO);
s.addText('Los pasillos no dan para un contrabalanceado', { x: 1.27, y: 0.42, w: 11.4, h: 0.6,
  fontSize: 29, bold: true, color: HUM, fontFace: H, margin: 0 });
s.addText('Medimos los 29 pasillos sobre su plano y los comparamos contra la ficha de fábrica del equipo.',
  { x: 1.27, y: 1.12, w: 11.4, h: 0.4, fontSize: 13.5, color: MUT, fontFace: B, margin: 0 });
tarjeta(s, 0.65, 1.85, 6.4, 2.87, true);
s.addText('25 de sus 29 pasillos miden', { x: 1.0, y: 2.05, w: 5.7, h: 0.35, fontSize: 12.5, color: MUT, fontFace: B, margin: 0 });
s.addText('3.07 – 3.35 m', { x: 1.0, y: 2.4, w: 5.7, h: 0.75, fontSize: 40, bold: true, color: HUM, fontFace: H, margin: 0 });
s.addText('Lo que un Baoli KBE 20 necesita para girar a 90° con carga (Ast, ficha VDI 2198)',
  { x: 1.0, y: 3.2, w: 5.7, h: 0.5, fontSize: 12, color: MUT, fontFace: B, margin: 0, valign: 'top' });
s.addText('3.82 m', { x: 1.0, y: 3.8, w: 5.7, h: 0.7, fontSize: 38, bold: true, color: ROJO, fontFace: H, margin: 0 });
s.addImage({ path: 'im_pasillo.jpg', x: 7.55, y: 1.85, w: 5.1, h: 2.87, sizing: { type: 'cover', w: 5.1, h: 2.87 }, shadow: sombra() });
const eq = [['Baoli KBE 20 · 2.0 t', '3.82 m', 'no entra en ninguno de los 25', ROJO],
            ['Baoli KBE 18 · 1.75 t', '3.55 m', 'tampoco, ni en el más ancho', HAZ],
            ['Reach truck típico', '~2.80 m', 'entra con holgura de sobra', VERDE]];
eq.forEach((e, i) => {
  const y = 4.95 + i * 0.66;
  tarjeta(s, 0.65, y, 12, 0.56, true);
  s.addText(e[0], { x: 1.0, y, w: 3.5, h: 0.56, fontSize: 12.5, bold: true, color: HUM, fontFace: B, margin: 0, valign: 'middle' });
  s.addText(e[1], { x: 4.9, y, w: 1.6, h: 0.56, fontSize: 13.5, bold: true, color: e[3], fontFace: H, margin: 0, valign: 'middle' });
  s.addText(e[2], { x: 6.7, y, w: 5.6, h: 0.56, fontSize: 12, color: MUT, fontFace: B, margin: 0, valign: 'middle' });
});
s.addNotes('El slide de la reunión. Pausa larga aquí. No es opinión nuestra: es la ficha del fabricante contra la geometría de su plano. Dejar que ellos hablen primero.');

/* ───────── 7 · EL DATO FINO ───────── */
s = p.addSlide(); fondo(s, false);
titulo(s, 'Pero ojo, no todos los pasillos son iguales', false,
  'Antes de que alguien nos diga "no es cierto, por ahí sí pasan" — tienen razón, y aquí está el detalle');
const dist = [['3.07 m', 'el más angosto', ROJO], ['3.17 m', 'la mediana de los 29', TINTA],
               ['25 de 29', 'entre 3.07 y 3.35 m', TINTA], ['4', 'pasillos de 4.40 a 4.48 m', VERDE]];
dist.forEach((v, i) => stat(s, 0.65 + (i % 2) * 3.1, 1.95 + Math.floor(i / 2) * 1.6, 2.9, v[0], v[1], v[2], false));
s.addImage({ path: 'im_prop.jpg', x: 6.9, y: 1.95, w: 5.75, h: 3.2, sizing: { type: 'cover', w: 5.75, h: 3.2 }, shadow: sombra() });
tarjeta(s, 0.65, 5.35, 12, 1.55, false, TINTA);
s.addText('Sí hay cuatro corredores donde un KBE 20 entra bien. Son de circulación, no de almacenaje.\nEl almacén se puede recorrer. Lo que no se puede es estibar en las filas.',
  { x: 1.1, y: 5.35, w: 11.1, h: 1.55, fontSize: 14, bold: true, color: HAZ, fontFace: B, margin: 0, valign: 'middle', lineSpacing: 22 });
s.addNotes('Este slide es el que evita que nos tumben el argumento. Alguien siempre dice "pero por ese pasillo sí pasa el montacargas". Adelantarse: sí, por esos cuatro. Por los otros 25 no.');

/* ───────── 8 · TRES CAMINOS ───────── */
s = p.addSlide(); fondo(s, true);
titulo(s, 'Eso les abre tres caminos', true, 'Ninguno es malo. Lo malo sería automatizar sin escoger.');
const cam = [['Medir y salir de dudas', 'Con cinta, hoy mismo. Si el pasillo real da 3.9 y el plano dice 3.17, entonces el plano está mal acotado y hay que revisar todo lo demás.', CIAN],
             ['Cambiar de equipo', 'Un reach truck opera con holgura en 3.1 m. Cambia la inversión, pero también les sube la altura de servicio: el rack llega a 7 m.', HAZ],
             ['Rediseñar el layout', 'Aplica al sector C, que todavía no tiene racks dibujados. Ahí sí se puede hacer bien desde cero.', VERDE]];
cam.forEach((c, i) => {
  const x = 0.65 + i * 4.06;
  tarjeta(s, x, 2.15, 3.82, 3.25, true);
  chip(s, i + 1, x + 0.32, 2.48, c[2]);
  s.addText(c[0], { x: x + 0.32, y: 3.1, w: 3.2, h: 0.5, fontSize: 19, bold: true, color: c[2], fontFace: H, margin: 0 });
  s.addText(c[1], { x: x + 0.32, y: 3.68, w: 3.2, h: 1.5, fontSize: 12.5, color: MUT, fontFace: B, margin: 0, valign: 'top' });
});
tarjeta(s, 0.65, 5.95, 12, 0.8, true, PANEL);
s.addText('Se lo decimos de frente: el kit TaTa no arregla un pasillo angosto. Preferimos decírselo antes de venderles nada.',
  { x: 1.0, y: 5.95, w: 11.3, h: 0.8, fontSize: 14, bold: true, color: HAZ, fontFace: B, margin: 0, valign: 'middle' });
s.addNotes('Este es el slide que nos separa de un vendedor. Decirlo en voz alta y sin adornos: preferimos perder la venta a venderles algo que no va a funcionar.');

/* ───────── 9 · HALLAZGO 3 ───────── */
s = p.addSlide(); fondo(s, false);
chip(s, 3, 0.65, 0.46, ROJO);
s.addText('Y hay racks a los que no se puede llegar', { x: 1.27, y: 0.42, w: 11.4, h: 0.6,
  fontSize: 29, bold: true, color: TINTA, fontFace: H, margin: 0 });
s.addText('Estos dos los encontramos manejando la simulación, no mirando el plano. Es la mejor prueba de para qué sirve.',
  { x: 1.27, y: 1.12, w: 11.4, h: 0.4, fontSize: 13.5, color: MUT2, fontFace: B, margin: 0 });
const h3 = [['El muro que parte el sector IT',
             'Hay un muro en x≈868 que divide la bodega en dos naves. La nave oeste queda encerrada: el único paso está por detrás de las filas de rack.',
             'O se le abre acceso propio, o se tumba el muro'],
            ['Pasillos sin salida',
             'Si las filas van de pared a pared sin un corredor transversal, no hay forma de pasar de un pasillo al de al lado. El operador tendría que salir 25 metros en reversa.',
             'Todo layout necesita transversal, aunque cueste ubicaciones']];
h3.forEach((c, i) => {
  const y = 1.95 + i * 2.42;
  tarjeta(s, 0.65, y, 12, 2.15, false);
  s.addText(c[0], { x: 1.0, y: y + 0.22, w: 11.3, h: 0.42, fontSize: 18, bold: true, color: TINTA, fontFace: H, margin: 0 });
  s.addText(c[1], { x: 1.0, y: y + 0.72, w: 11.3, h: 0.72, fontSize: 13, color: MUT2, fontFace: B, margin: 0, valign: 'top' });
  s.addText(c[2], { x: 1.0, y: y + 1.52, w: 11.3, h: 0.42, fontSize: 13, bold: true, color: ROJO, fontFace: B, margin: 0 });
});
s.addText('Un rack al que no se puede llegar no es capacidad. Es un dibujo.',
  { x: 0.65, y: 6.85, w: 12, h: 0.45, fontSize: 15, bold: true, italic: true, color: TINTA, fontFace: H, margin: 0 });
s.addNotes('Contarlo como anécdota: estábamos manejando en la simulación y nos quedamos encerrados. Ahí caímos. Suena mucho mejor que presentarlo como auditoría.');

/* ───────── 10 · SIMULADOR ───────── */
s = p.addSlide(); fondo(s, true);
s.addImage({ path: 'im_botoni.jpg', x: 0, y: 0, w: W, h: HT, sizing: { type: 'cover', w: W, h: HT }, transparency: 55 });
s.addShape(p.ShapeType.rect, { x: 0, y: 0, w: W, h: HT, fill: { color: OSCURO, transparency: 18 } });
tarjeta(s, 0.65, 1.5, 6.4, 3.45, true);
s.addText('AHORA MANÉJENLO USTEDES', { x: 1.0, y: 1.8, w: 5.7, h: 0.35, fontSize: 11.5, bold: true, color: HAZ, fontFace: B, charSpacing: 2, margin: 0 });
s.addText('Su almacén, jugable', { x: 1.0, y: 2.18, w: 5.7, h: 0.6, fontSize: 30, bold: true, color: HUM, fontFace: H, margin: 0, valign: 'top' });
s.addText([
  { text: 'Es un Baoli KBE 20 con las cotas de fábrica, no un cubo genérico', options: { bullet: true, breakLine: true } },
  { text: 'Agarren y dejen maxicubos en las ubicaciones, con su código', options: { bullet: true, breakLine: true } },
  { text: 'Intenten el giro de 90° en su propio pasillo. A ver si les sale.', options: { bullet: true, breakLine: true } },
  { text: 'Y véanlo con tres unidades coordinándose sin chocarse', options: { bullet: true } },
], { x: 1.0, y: 3.05, w: 5.7, h: 2.35, fontSize: 13, color: HUM, fontFace: B, paraSpaceAfter: 9, margin: 0, valign: 'top' });
s.addNotes('Pantalla completa y control USB listo antes de entrar. Que lo maneje alguien de ellos, de preferencia un operador. Vale más que diez slides. Si se traban en el pasillo, no decir nada: que lo descubran.');

/* ───────── 11 · PROPUESTA SECTOR C ───────── */
s = p.addSlide(); fondo(s, false);
titulo(s, 'Y así se vería el sector IT bien hecho', false,
  'La bodega que hoy está vacía, dibujada para que un montacargas de verdad pueda trabajar ahí');
s.addImage({ path: 'im_prop.jpg', x: 6.35, y: 1.9, w: 6.3, h: 4.27, sizing: { type: 'cover', w: 6.3, h: 4.27 }, shadow: sombra() });
const pr = [['790', 'ubicaciones nuevas, en 2 naves', VERDE],
            ['5.54 m', 'de pasillo en la nave este', TINTA],
            ['6.34 m', 'de pasillo en la nave oeste', TINTA],
            ['4.50 m', 'de corredor transversal', TINTA]];
pr.forEach((v, i) => stat(s, 0.65 + (i % 2) * 3.1, 1.9 + Math.floor(i / 2) * 1.6, 2.9, v[0], v[1], v[2], false));
tarjeta(s, 0.65, 5.2, 5.75, 1.5, false, TINTA);
s.addText('Contra los 3.82 m que pide el KBE 20 les sobra metro y medio. El giro sale de una sola pasada, sin maniobrar.',
  { x: 1.0, y: 5.2, w: 5.1, h: 1.5, fontSize: 12.5, bold: true, color: VERDE, fontFace: B, margin: 0, valign: 'middle' });
s.addNotes('Aclarar que el diseño es paramétrico: si nos dan las medidas reales de esa bodega, se los regeneramos en minutos ahí mismo. Eso impresiona más que el dibujo.');

/* ───────── 12 · KIT ───────── */
s = p.addSlide(); fondo(s, false);
titulo(s, 'Bueno, y ¿qué es el kit TaTa?', false,
  'Un solo hardware que se instala una vez. La autonomía se prende por software cuando ustedes quieran.');
const kit = [['TaTa Watch', 'Nivel 1 · Ve y avisa', CIAN, ['El operador sigue manejando', 'Alerta y frena en emergencia', 'El inventario se registra solo', 'Reporta ciclos y casi-accidentes'], '$8,548'],
             ['TaTa Assist', 'Nivel 2 · Se maneja solo, con supervisión', HAZ, ['Todo lo de Watch', 'Se traslada solo de punto a punto', 'Agarra y deja asistido', 'Recibe tareas del WMS'], '$14,538'],
             ['TaTa Auto', 'Nivel 3 · Sin nadie arriba', VERDE, ['Todo lo de Assist', 'Opera desatendido', 'Escáneres certificables PL d', 'Turnos sin personal'], '$23,738']];
kit.forEach((k, i) => {
  const x = 0.65 + i * 4.06;
  tarjeta(s, x, 1.95, 3.82, 4.35, false);
  s.addText(k[0], { x: x + 0.32, y: 2.15, w: 3.2, h: 0.45, fontSize: 20, bold: true, color: TINTA, fontFace: H, margin: 0 });
  s.addText(k[1], { x: x + 0.32, y: 2.62, w: 3.2, h: 0.35, fontSize: 11, bold: true, color: k[2], fontFace: B, charSpacing: 0.6, margin: 0 });
  s.addText(k[3].map((t, j) => ({ text: t, options: { bullet: true, breakLine: j < k[3].length - 1 } })),
    { x: x + 0.32, y: 3.15, w: 3.2, h: 1.5, fontSize: 11.5, color: MUT2, fontFace: B, paraSpaceAfter: 5, margin: 0, valign: 'top' });
  s.addText(k[4], { x: x + 0.32, y: 5.4, w: 3.2, h: 0.6, fontSize: 26, bold: true, color: TINTA, fontFace: H, margin: 0 });
  s.addText('en hardware, por montacargas', { x: x + 0.32, y: 5.95, w: 3.2, h: 0.3, fontSize: 10, color: MUT2, fontFace: B, margin: 0 });
});
s.addText('Son costos de hardware, sin impuestos, flete, instalación ni ingeniería. La infraestructura del almacén va aparte: $14,288, una sola vez por sitio.',
  { x: 0.65, y: 6.5, w: 12, h: 0.4, fontSize: 11.5, italic: true, color: MUT2, fontFace: B, margin: 0 });
s.addNotes('No esconder que son costos, no precio de venta. Esa honestidad compra la conversación de precio que viene después. Si preguntan el precio final, decir que sale cuando tengamos las cinco respuestas.');

/* ───────── 13 · MONTAJE ───────── */
s = p.addSlide(); fondo(s, false);
titulo(s, 'Qué se le monta encima al montacargas', false,
  'Dibujado sobre las cotas del Baoli KBE 20: 3.36 m de largo, techo de protección a 2.177 m');
s.addImage({ path: 'im_kit.jpg', x: 0.65, y: 1.95, w: 7.5, h: 3.07, sizing: { type: 'cover', w: 7.5, h: 3.07 }, shadow: sombra() });
const mod = [['Cómo se ubica', 'Un LiDAR 3D en el techo y los encoders de tracción y dirección — o el bus CAN, si el Baoli lo deja', CIAN],
             ['Cómo ve', '3 cámaras. La del mástil sube con el carro y lee la ubicación a 6 m de altura', VERDE],
             ['Cómo agarra', 'Altura de uñas, presión hidráulica y una fotocélula que confirma que sí trae carga', HAZ],
             ['Cómo no atropella', 'Escáneres certificables PL d y controlador de seguridad — sólo en el nivel Auto', ROJO]];
mod.forEach((m, i) => {
  const y = 1.95 + i * 1.24;
  tarjeta(s, 8.45, y, 4.2, 1.08, false);
  s.addShape(p.ShapeType.ellipse, { x: 8.72, y: y + 0.16, w: 0.28, h: 0.28, fill: { color: m[2] } });
  s.addText(m[0], { x: 9.12, y: y + 0.13, w: 3.3, h: 0.32, fontSize: 13, bold: true, color: TINTA, fontFace: B, margin: 0 });
  s.addText(m[1], { x: 8.72, y: y + 0.48, w: 3.7, h: 0.55, fontSize: 10, color: MUT2, fontFace: B, margin: 0, valign: 'top' });
});
tarjeta(s, 0.65, 5.25, 7.5, 1.55, false, TINTA);
s.addText('La cámara de mástil es la pieza que convierte esto en inventario y no solo en navegación. Es lo que hace que el nivel 1 valga la pena desde el primer día.',
  { x: 1.0, y: 5.25, w: 6.9, h: 1.55, fontSize: 12.5, bold: true, color: HAZ, fontFace: B, margin: 0, valign: 'middle' });
s.addNotes('Si preguntan por el CAN del Baoli: decir la verdad, que hay que validarlo en el equipo real antes de cerrar el diseño. Nunca inventar ahí.');

/* ───────── 14 · INFRAESTRUCTURA ───────── */
s = p.addSlide(); fondo(s, false);
titulo(s, 'Y qué se le monta al almacén', false,
  'Calculado sobre la geometría de su plano, no sobre un estándar genérico');
s.addImage({ path: 'im_sensores.jpg', x: 0.65, y: 1.9, w: 12, h: 2.62, sizing: { type: 'cover', w: 12, h: 2.62 }, shadow: sombra() });
const inf = [['13', 'cámaras en el techo'], ['56', 'marcadores en los racks'], ['7', 'puntos de acceso'], ['1', 'estación de carga']];
inf.forEach((v, i) => {
  const x = 0.65 + i * 3.08;
  tarjeta(s, x, 4.75, 2.85, 1.35, false);
  s.addText(v[0], { x: x + 0.3, y: 4.9, w: 2.3, h: 0.6, fontSize: 30, bold: true, color: HAZ, fontFace: H, margin: 0 });
  s.addText(v[1], { x: x + 0.3, y: 5.5, w: 2.3, h: 0.4, fontSize: 11, color: MUT2, fontFace: B, margin: 0 });
});
s.addText('Esto se instala una sola vez y sirve para toda la flota: $14,288. La estación de carga va justo donde su plano ya dice "Carga de montacargas".',
  { x: 0.65, y: 6.3, w: 12, h: 0.45, fontSize: 13.5, bold: true, color: TINTA, fontFace: B, margin: 0 });
s.addNotes('Señalar lo de la estación de carga: respetamos lo que ellos ya habían pensado. Es un detalle chiquito que cae muy bien.');

/* ───────── 15 · CÓMO EMPEZAMOS ───────── */
s = p.addSlide(); fondo(s, true);
titulo(s, 'Y esto cómo arrancaría', true, 'No es plug and play, y no se lo vamos a vender así');
const fases = [['Vamos y medimos', 'Pasillos, alturas y red. Salen con el modelo 3D de su bodega aunque no nos compren nada.', HAZ],
               ['Revisamos el equipo', 'Confirmamos el bus CAN, la dirección y dónde cabe el kit. Los soportes se fabrican a la medida.', HAZ],
               ['Instalamos y mapeamos', '3 a 5 días por unidad la primera vez. El kit recorre el almacén y arma su mapa.', HAZ],
               ['Fase Watch', 'Semanas operando en asistencia, juntando datos reales de ciclos y de dónde se traba.', VERDE],
               ['Autonomía, ruta por ruta', 'Empezando por la más repetitiva. Nunca todo de golpe.', HAZ]];
fases.forEach((f, i) => {
  const y = 2.0 + i * 0.96;
  chip(s, i + 1, 0.75, y, f[2]);
  s.addText(f[0], { x: 1.42, y: y - 0.02, w: 3.6, h: 0.4, fontSize: 15, bold: true, color: HUM, fontFace: B, margin: 0 });
  s.addText(f[1], { x: 5.1, y: y + 0.02, w: 7.5, h: 0.6, fontSize: 12, color: MUT, fontFace: B, margin: 0, valign: 'top' });
});
s.addText('El paso 4 es el que importa: con sus propios datos ustedes deciden si el paso 5 vale la pena. No nosotros.',
  { x: 0.65, y: 6.85, w: 12, h: 0.45, fontSize: 14, bold: true, color: VERDE, fontFace: B, margin: 0 });
s.addNotes('Vender la Fase Watch, no la autonomía. Es barata, es rápida y genera el dato que justifica todo lo demás. Si sólo se llevan una idea de la reunión, que sea esta.');

/* ───────── 16 · LO QUE NECESITAMOS ───────── */
s = p.addSlide(); fondo(s, false);
titulo(s, 'Lo que necesitamos de ustedes', false, 'Cinco respuestas y les podemos cotizar en firme');
const q = [['¿Cuál de las tres propuestas se va a construir?', 'De eso depende todo el dimensionamiento'],
           ['¿Con qué equipo trabajan hoy? Marca, modelo y ficha', 'Para saber si el pasillo real le sirve'],
           ['¿Podemos medir un pasillo con cinta?', 'Confirma o descarta que el plano esté mal acotado'],
           ['¿Cómo sirven los niveles 4 y 5 del rack?', 'El KBE estándar eleva 3.0 m y el rack llega a ~7 m'],
           ['¿El controlador del Baoli deja hablarle por CAN?', 'De eso depende el diseño de actuación y su costo']];
q.forEach((c, i) => {
  const y = 1.95 + i * 0.97;
  tarjeta(s, 0.65, y, 12, 0.82, false);
  chip(s, i + 1, 1.0, y + 0.2, HAZ);
  s.addText(c[0], { x: 1.62, y: y + 0.13, w: 10.6, h: 0.35, fontSize: 14.5, bold: true, color: TINTA, fontFace: B, margin: 0 });
  s.addText(c[1], { x: 1.62, y: y + 0.47, w: 10.6, h: 0.3, fontSize: 11.5, color: MUT2, fontFace: B, margin: 0 });
});
s.addText('Con eso en la mano, la cotización sale en una semana.',
  { x: 0.65, y: 6.95, w: 12, h: 0.45, fontSize: 14, bold: true, color: TINTA, fontFace: B, margin: 0 });
s.addNotes('Anotar las respuestas ahí mismo, delante de ellos. Salir de la reunión con estas cinco contestadas es el objetivo real del día.');

/* ───────── 17 · CIERRE ───────── */
s = p.addSlide(); fondo(s, true);
s.addImage({ path: 'im_prop.jpg', x: 0, y: 0, w: W, h: HT, sizing: { type: 'cover', w: W, h: HT }, transparency: 82 });
s.addShape(p.ShapeType.rect, { x: 0, y: 0, w: W, h: HT, fill: { color: OSCURO, transparency: 10 } });
s.addShape(p.ShapeType.rect, { x: 0.9, y: 2.08, w: 1.5, h: 0.045, fill: { color: HAZ } });
s.addText('No les estamos vendiendo un montacargas nuevo.', { x: 0.9, y: 2.25, w: 11.5, h: 0.8,
  fontSize: 32, bold: true, color: HUM, fontFace: H, margin: 0 });
s.addText('Les vendemos el cerebro, los ojos y las manos\nque le faltan al que ya tienen trabajando en la bodega.',
  { x: 0.9, y: 3.1, w: 11.5, h: 1.4, fontSize: 24, color: HAZ, fontFace: H, lineSpacing: 32, margin: 0 });
s.addText('Gracias · ¿Qué les quedó dando vueltas?', { x: 0.9, y: 5.6, w: 8, h: 0.5, fontSize: 18, bold: true, color: MUT, fontFace: B, margin: 0 });
s.addText('TaTa · Tecnología Avanzada de Transporte Autónomo', { x: 0.9, y: 6.4, w: 8, h: 0.4,
  fontSize: 13, bold: true, color: HUM, fontFace: B, margin: 0 });
s.addNotes('Cerrar volviendo a la Fase Watch y a las cinco preguntas. Proponer fecha concreta para el levantamiento antes de que se paren de la silla.');

p.writeFile({ fileName: 'TaTa_Presentacion_RETHINK.pptx' }).then(() => console.log('deck RETHINK listo'));
