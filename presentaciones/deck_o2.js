const pptx = require('pptxgenjs');
const p = new pptx();
p.layout = 'LAYOUT_WIDE';               // 13.3 x 7.5
p.author = 'TaTa'; p.company = 'TaTa · Tecnología Avanzada de Transporte Autónomo';
p.title = 'TaTa · Caso de negocio interno — aprobación de prototipo';

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

// fila de tabla reutilizable
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
const NARANJA_ = 'D95926';

/* ───────── 1 · PORTADA ───────── */

/* ───────── 1 · PORTADA ───────── */
let s = p.addSlide(); fondo(s, true);
s.addShape(p.ShapeType.rect, { x: 0.9, y: 2.55, w: 1.5, h: 0.045, fill: { color: HAZ } });
s.addText('TaTa', { x: 0.9, y: 1.15, w: 6, h: 1.0, fontSize: 54, bold: true, color: HAZ, fontFace: H, margin: 0 });
s.addText('Tecnología Avanzada de Transporte Autónomo · un proyecto de Montasa', { x: 0.93, y: 2.1, w: 9, h: 0.4,
  fontSize: 14, color: MUT, fontFace: B, margin: 0 });
s.addText('Tres caminos para construir\nel primer montacargas autónomo', { x: 0.9, y: 2.85, w: 9.5, h: 1.6,
  fontSize: 30, bold: true, color: HUM, fontFace: H, lineSpacing: 38, margin: 0 });
const port = [['Fase 0 · Validación', 3000, CIAN], ['Fase 1 · Producto', 10000, HAZ], ['Fase 2 · Certificado', 25000, VERDE]];
port.forEach((q, i) => {
  const x = 0.9 + i * 3.5;
  tarjeta(s, x, 4.75, 3.2, 1.35, true);
  s.addText(q[0], { x: x + 0.3, y: 4.9, w: 2.9, h: 0.3, fontSize: 10, bold: true, color: q[2], fontFace: B, charSpacing: 1, margin: 0 });
  s.addText(money(q[1]), { x: x + 0.3, y: 5.24, w: 2.6, h: 0.6, fontSize: 26, bold: true, color: HUM, fontFace: H, margin: 0 });
});
s.addText('Preparado para Omar', { x: 0.9, y: 6.55, w: 6, h: 0.35, fontSize: 13, bold: true, color: HUM, fontFace: B, margin: 0 });
s.addText('Agosto 2026 · San Pedro Sula', { x: 0.9, y: 6.9, w: 6, h: 0.3, fontSize: 11, color: MUT, fontFace: B, margin: 0 });
s.addNotes('Abrir con los tres números. Que sepa desde el segundo uno que la conversación es de miles, no de cientos de miles.');

/* ───────── 2 · RESUMEN EJECUTIVO ───────── */
s = p.addSlide(); fondo(s, false);
titulo(s, 'Resumen ejecutivo', false, 'Todo el documento, en una página');
const rex = [
  ['La oportunidad', 'Montasa vende y da servicio a montacargas Baoli. TaTa es un kit que se instala sobre esos mismos montacargas y los vuelve autónomos por etapas.', HAZ],
  ['Por qué ahora', 'Un contrabalanceado autónomo de fábrica cuesta $85,000–$120,000. Nuestro kit completo cuesta $22,978 de hardware sobre una máquina que el cliente ya tiene.', CIAN],
  ['Qué ya está hecho', 'Almacén de un cliente real reconstruido y medido, BOM de 39 componentes con precios verificados, simulador 3D navegable y banco de pruebas. Todo sin desembolso.', VERDE],
  ['Qué se pide', 'Elegir uno de tres caminos: ' + money(3000) + ', ' + money(10000) + ' o ' + money(25000) + '. Más un montacargas de demo prestado por 4 meses.', HAZ],
  ['La recomendación', 'Empezar por el de ' + money(3000) + '. Prueba la parte difícil —percepción y navegación— y deja la decisión cara para cuando haya datos.', VERDE],
];
rex.forEach((r, i) => {
  const y = 1.9 + i * 1.02;
  tarjeta(s, 0.65, y, 12, 0.88, false);
  s.addShape(p.ShapeType.rect, { x: 0.65, y, w: 0.07, h: 0.88, fill: { color: r[2] } });
  s.addText(r[0], { x: 0.95, y, w: 2.5, h: 0.88, fontSize: 13, bold: true, color: TINTA, fontFace: B, margin: 0, valign: 'middle' });
  s.addText(r[1], { x: 3.5, y, w: 8.9, h: 0.88, fontSize: 11.5, color: MUT2, fontFace: B, margin: 0, valign: 'middle' });
});
s.addNotes('Si Omar sólo lee un slide, que sea este.');

/* ───────── 3 · QUÉ ES TATA ───────── */
s = p.addSlide(); fondo(s, false);
titulo(s, 'Qué es TaTa, en concreto', false, 'No es un montacargas. Es lo que se le monta encima a uno que ya existe.');
tarjeta(s, 0.65, 1.95, 5.9, 2.3, false, TINTA);
s.addText('El problema del cliente', { x: 1.0, y: 2.15, w: 5.2, h: 0.35, fontSize: 11, bold: true, color: HAZ, fontFace: B, charSpacing: 1.4, margin: 0 });
s.addText('Un almacén paga tres turnos de operadores, sufre para contratarlos, y aun así se le pierde inventario y se le pegan los racks. Automatizar significa hoy comprar máquinas nuevas y tirar las que tiene.',
  { x: 1.0, y: 2.55, w: 5.2, h: 1.5, fontSize: 12.5, color: HUM, fontFace: B, margin: 0, valign: 'top' });
tarjeta(s, 6.75, 1.95, 5.9, 2.3, false);
s.addText('Lo que hacemos', { x: 7.1, y: 2.15, w: 5.2, h: 0.35, fontSize: 11, bold: true, color: MUT2, fontFace: B, charSpacing: 1.4, margin: 0 });
s.addText('Un kit de sensores, cómputo y actuación que se instala sobre el montacargas que el cliente ya opera. Se instala una vez; la autonomía se habilita por software, por etapas, cuando el cliente esté listo.',
  { x: 7.1, y: 2.55, w: 5.2, h: 1.5, fontSize: 12.5, color: TINTA, fontFace: B, margin: 0, valign: 'top' });
const niv = [['1', 'Watch', 'El operador maneja. El kit ve, alerta, frena en emergencia y registra el inventario solo.', money(8548), CIAN],
             ['2', 'Assist', 'La máquina se traslada sola y agarra carga asistida, con una persona supervisando.', money(14538), HAZ],
             ['3', 'Auto', 'Sin nadie arriba. Seguridad redundante certificable para operar desatendido.', money(22978), VERDE]];
fila(s, 0.65, 4.55, 12, 0.42, [{t:'NIVEL',w:1.5},{t:'QUÉ HACE',w:7.4},{t:'HARDWARE POR UNIDAD',w:3.1,a:'right'}], false, true);
niv.forEach((n, i) => {
  fila(s, 0.65, 4.97 + i * 0.62, 12, 0.62, [
    { t: n[0] + ' · ' + n[1], w: 1.5, b: true, c: n[4] },
    { t: n[2], w: 7.4, fs: 10.5, c: MUT2 },
    { t: n[3], w: 3.1, b: true, a: 'right', fs: 13 },
  ], false);
});
s.addText('Costos de hardware, sin impuestos, flete, instalación ni ingeniería. La infraestructura del almacén va aparte: ' + money(14288) + ' una sola vez por sitio.',
  { x: 0.65, y: 6.95, w: 12, h: 0.4, fontSize: 10.5, italic: true, color: MUT2, fontFace: B, margin: 0 });
s.addNotes('El nivel 1 es el que se vende primero y el que hace dinero. Los niveles 2 y 3 son a dónde puede llegar, no por dónde se empieza.');

/* ───────── 4 · POR QUÉ RETROFIT ───────── */
s = p.addSlide(); fondo(s, true);
titulo(s, 'Por qué retrofit y no vender autónomos de fábrica', true,
  'La diferencia de precio es la tesis entera del producto');
const comp = [['Contrabalanceado autónomo de fábrica', '85,000 – 120,000', 'Máquina nueva. El cliente tira o revende la que ya tiene.', ROJO],
              ['Reach truck autónomo de fábrica', '90,000 – 130,000', 'Mismo problema, otro formato.', ROJO],
              ['Montacargas eléctrico nuevo, sin automatizar', '15,000 – 30,000', 'Lo que el cliente compra hoy. Sigue necesitando un operador por turno.', MUT],
              ['Kit TaTa nivel 3, sobre su propia máquina', '22,978', 'Sin comprar máquina. El activo que ya tiene sigue trabajando.', VERDE]];
fila(s, 0.65, 2.05, 12, 0.44, [{t:'OPCIÓN',w:5.2},{t:'USD POR UNIDAD',w:2.6,a:'right'},{t:'QUÉ IMPLICA',w:4.2}], true, true);
comp.forEach((c, i) => {
  fila(s, 0.65, 2.49 + i * 0.78, 12, 0.78, [
    { t: c[0], w: 5.2, b: i === 3, fs: 12 },
    { t: c[1], w: 2.6, a: 'right', b: true, c: c[3], fs: 14 },
    { t: c[2], w: 4.2, fs: 10, c: MUT },
  ], true);
});
tarjeta(s, 0.65, 5.85, 12, 1.05, true, PANEL);
s.addText('El comparable correcto es la máquina autónoma de fábrica, no el montacargas nuevo. Pero el cliente va a comparar con el montacargas nuevo, y hay que estar listos para esa conversación.',
  { x: 1.05, y: 5.85, w: 11.2, h: 1.05, fontSize: 13, bold: true, color: HAZ, fontFace: B, margin: 0, valign: 'middle' });
s.addText('Rangos de mercado consultados en agosto 2026.', { x: 0.65, y: 7.0, w: 12, h: 0.3, fontSize: 9.5, italic: true, color: MUT, fontFace: B, margin: 0 });
s.addNotes('Anticipar la objeción antes de que Omar la haga: sí, $22,978 se parece al precio de un montacargas nuevo. Por eso el que se vende primero es el nivel 1.');

/* ───────── 5 · POR QUÉ EN MONTASA ───────── */
s = p.addSlide(); fondo(s, false);
titulo(s, 'Por qué esto tiene que vivir dentro de Montasa', false,
  'Un tercero tendría que comprar todo esto. Nosotros ya lo tenemos.');
const vent = [['Las máquinas', 'Para desarrollar el kit hay que tener montacargas. Nosotros los tenemos en el piso.', HAZ],
              ['El taller', 'Técnicos que ya conocen el Baoli por dentro. Un tercero contrata y entrena desde cero.', HAZ],
              ['Los clientes', 'La base instalada de Montasa es el canal de venta. No hay que construirlo.', VERDE],
              ['La relación con Baoli', 'Abre la puerta para resolver el acceso al controlador, que es el riesgo técnico principal.', CIAN],
              ['El servicio', 'Un kit autónomo necesita mantenimiento. Ya existe la red que lo puede dar.', HAZ],
              ['Defiende la línea', 'El kit no compite con vender montacargas: le da a Montasa un argumento que el competidor no tiene.', VERDE]];
vent.forEach((v, i) => {
  const x = 0.65 + (i % 3) * 4.06, y = 2.05 + Math.floor(i / 3) * 2.3;
  tarjeta(s, x, y, 3.82, 2.05, false);
  s.addShape(p.ShapeType.rect, { x: x + 0.32, y: y + 0.32, w: 0.6, h: 0.045, fill: { color: v[2] } });
  s.addText(v[0], { x: x + 0.32, y: y + 0.5, w: 3.2, h: 0.4, fontSize: 16, bold: true, color: TINTA, fontFace: H, margin: 0 });
  s.addText(v[1], { x: x + 0.32, y: y + 0.98, w: 3.2, h: 0.95, fontSize: 11.5, color: MUT2, fontFace: B, margin: 0, valign: 'top' });
});
s.addText('El último punto es el importante: si un competidor le vende al cliente un montacargas con kit y nosotros no, perdemos la máquina, no sólo el kit.',
  { x: 0.65, y: 6.85, w: 12, h: 0.45, fontSize: 13, bold: true, color: TINTA, fontFace: B, margin: 0 });
s.addNotes('El argumento que le cierra a un jefe: no es un negocio nuevo separado, es un diferenciador para el negocio que ya existe.');

/* ───────── 6 · LO QUE YA ESTÁ HECHO ───────── */
s = p.addSlide(); fondo(s, false);
titulo(s, 'Lo que ya está hecho, sin gastar un dólar', false,
  'No pedimos dinero para empezar a pensar. Lo pedimos para construir.');
s.addImage({ path: 'im_botoni.jpg', x: 6.9, y: 1.95, w: 5.75, h: 3.23, sizing: { type: 'cover', w: 5.75, h: 3.23 }, shadow: sombra() });
const hecho = [['Almacén de un cliente real, medido', 'El plano de RETHINK reconstruido en 3D: 2,138 ubicaciones, 29 filas de rack y 1,142 segmentos de muro.'],
               ['BOM completo de 39 componentes', 'Con modelo, proveedor, precio verificado y alternativa más barata para cada línea.'],
               ['Simulador navegable', 'El almacén del cliente, manejable con un Baoli a cotas de fábrica. Ya está en línea y funcionando.'],
               ['Banco de pruebas de sensores', 'La bodega exportada a Isaac Sim y el análisis que dice qué LiDAR hace falta antes de comprarlo.']];
hecho.forEach((h, i) => {
  const y = 1.95 + i * 0.86;
  s.addShape(p.ShapeType.ellipse, { x: 0.65, y: y + 0.08, w: 0.26, h: 0.26, fill: { color: VERDE } });
  s.addText(h[0], { x: 1.08, y: y + 0.02, w: 5.5, h: 0.34, fontSize: 13.5, bold: true, color: TINTA, fontFace: B, margin: 0 });
  s.addText(h[1], { x: 1.08, y: y + 0.36, w: 5.5, h: 0.5, fontSize: 10.5, color: MUT2, fontFace: B, margin: 0, valign: 'top' });
});
tarjeta(s, 0.65, 5.6, 12, 1.3, false, TINTA);
s.addText('El simulador ya encontró dos errores de circulación en el layout del cliente que no se ven mirando el plano. Esa herramienta queda como activo de Montasa para cualquier cliente que siga.',
  { x: 1.05, y: 5.6, w: 11.2, h: 1.3, fontSize: 13, bold: true, color: HAZ, fontFace: B, margin: 0, valign: 'middle' });
s.addNotes('Mostrar el simulador en vivo si hay tiempo. Es lo que convierte esto de una idea a algo que ya existe.');

/* ───────── 7 · LOS TRES CAMINOS ───────── */
s = p.addSlide(); fondo(s, true);
titulo(s, 'Tres fases, no tres calidades', true, 'La misma máquina y el mismo software. Lo que cambia es qué pregunta contesta cada una.');
const cam = [
  ['Validación', money(3000), CIAN, 'Probar que la idea funciona',
   ['LiDAR 3D Livox Mid-360 de verdad', 'Jetson Orin Nano · cómputo real', 'Cámara de mástil para inventario', 'Teleoperado, sin actuación'],
   'No aguanta un año de vibración. No hace falta: su trabajo es contestar una pregunta.'],
  ['Producto', money(10000), HAZ, 'El kit que se le vende al cliente',
   ['Grado industrial y sellado IP', 'Jetson Orin NX · carrier -40/+85', 'Cámara Basler de mástil', 'Es el nivel 1 Watch, ya vendible'],
   'Aguanta la operación diaria. No se maneja solo todavía.'],
  ['Certificado', money(25000), VERDE, 'Autonomía completa certificable',
   ['Todo lo del Producto', 'Actuación: dirección, freno, hidráulica', 'Escáneres SICK PL d certificados', 'Opera sin nadie arriba'],
   'El producto terminado. El 40% del costo es la capa de seguridad.'],
];
cam.forEach((c, i) => {
  const x = 0.65 + i * 4.06;
  tarjeta(s, x, 1.95, 3.82, 4.55, true);
  s.addShape(p.ShapeType.rect, { x: x + 0.32, y: 2.22, w: 0.62, h: 0.045, fill: { color: c[2] } });
  s.addText(c[0], { x: x + 0.32, y: 2.4, w: 3.2, h: 0.42, fontSize: 19, bold: true, color: c[2], fontFace: H, margin: 0 });
  s.addText(c[1], { x: x + 0.32, y: 2.86, w: 3.2, h: 0.6, fontSize: 30, bold: true, color: HUM, fontFace: H, margin: 0 });
  s.addText(c[3], { x: x + 0.32, y: 3.5, w: 3.2, h: 0.32, fontSize: 11, bold: true, color: MUT, fontFace: B, margin: 0 });
  s.addText(c[4].map((t, j) => ({ text: t, options: { bullet: true, breakLine: j < c[4].length - 1 } })),
    { x: x + 0.32, y: 3.95, w: 3.2, h: 1.5, fontSize: 10.5, color: HUM, fontFace: B, paraSpaceAfter: 5, margin: 0, valign: 'top' });
  s.addText(c[5], { x: x + 0.32, y: 5.6, w: 3.2, h: 0.75, fontSize: 10, italic: true, color: MUT, fontFace: B, margin: 0, valign: 'top' });
});
tarjeta(s, 0.65, 6.6, 12, 0.75, true, PANEL);
s.addText('Los tres llevan LiDAR 3D. Sin él no se prueba nada, y es la parte que no se puede fingir.',
  { x: 1.05, y: 6.6, w: 11.2, h: 0.75, fontSize: 13, bold: true, color: HAZ, fontFace: B, margin: 0, valign: 'middle' });
s.addNotes('Este es el slide de la decisión. Dejar que Omar pregunte. La recomendación viene en el siguiente.');

/* ───────── 8 · COMPARACIÓN DE COSTOS ───────── */
s = p.addSlide(); fondo(s, false);
titulo(s, 'Tres formas de mover un maxicubo', false,
  '3 montacargas · 2 turnos · operador certificado cargado a ' + money(10309) + ' al año');
const cmp = [
  ['Seguir con operadores', '0', money(61853), money(185560), 'Los montacargas ya los tienen. Nada que invertir.', NARANJA_],
  ['Autónomos de fábrica', money(352500), money(12750), money(390750), '3 unidades nuevas + instalación + integración.', CIAN],
  ['Kit TaTa nivel 3', money(97009), money(12000), money(133009), 'Sobre sus propias máquinas + infraestructura del sitio.', VERDE],
];
fila(s, 0.65, 2.0, 12, 0.44, [{t:'OPCIÓN',w:3.0},{t:'INVERSIÓN',w:1.9,a:'right'},
  {t:'COSTO ANUAL',w:1.9,a:'right'},{t:'A 3 AÑOS',w:1.9,a:'right'},{t:'QUÉ IMPLICA',w:3.3}], false, true);
cmp.forEach((c, i) => fila(s, 0.65, 2.44 + i * 0.78, 12, 0.78, [
  { t: c[0], w: 3.0, b: true, fs: 12, c: c[5] },
  { t: c[1], w: 1.9, a: 'right', b: true, fs: 12.5 },
  { t: c[2], w: 1.9, a: 'right', fs: 11.5 },
  { t: c[3], w: 1.9, a: 'right', b: true, fs: 13, c: c[5] },
  { t: c[4], w: 3.3, fs: 9.5, c: MUT2 }], false));
const kpi = [['1.9 años', 'en pagarse contra seguir con operadores', VERDE],
             ['3.6×', 'más barato que comprar autónomos de fábrica', CIAN],
             ['7.2 años', 'tardaría en pagarse un autónomo de fábrica', ROJO]];
kpi.forEach((k, i) => {
  const x = 0.65 + i * 4.06;
  tarjeta(s, x, 5.05, 3.82, 1.5, false);
  s.addText(k[0], { x: x + 0.3, y: 5.18, w: 3.2, h: 0.62, fontSize: 28, bold: true, color: k[2], fontFace: H, margin: 0 });
  s.addText(k[1], { x: x + 0.3, y: 5.82, w: 3.2, h: 0.55, fontSize: 10.5, color: MUT2, fontFace: B, margin: 0, valign: 'top' });
});
s.addText('Salario mínimo de manufactura en Honduras 2026 (150+ trabajadores): L 12,349/mes. Operador certificado estimado en L 18,000 más 27% de cargas sociales. Tipo de cambio 26.61.',
  { x: 0.65, y: 6.75, w: 12, h: 0.5, fontSize: 10, italic: true, color: MUT2, fontFace: B, margin: 0, valign: 'top' });
s.addNotes('El número que importa: 1.9 años. Y el contraste: el autónomo de fábrica tarda 7.2 años en pagarse, o sea nunca dentro de un ciclo de inversión normal.');

/* ───────── 9 · LA CURVA ───────── */
s = p.addSlide(); fondo(s, true);
titulo(s, 'Dónde se cruzan las curvas', true, 'El costo acumulado de las tres opciones, a cinco años');
s.addImage({ path: 'retorno_5anios.png', x: 1.35, y: 1.85, w: 10.6, h: 4.35,
  sizing: { type: 'contain', w: 10.6, h: 4.35 } });
tarjeta(s, 0.65, 6.35, 12, 0.85, true, PANEL);
s.addText('Los operadores arrancan gratis y se vuelven caros. El kit arranca caro y se aplana. El autónomo de fábrica arranca carísimo y también se aplana — pero desde tres veces más arriba.',
  { x: 1.05, y: 6.35, w: 11.2, h: 0.85, fontSize: 12.5, bold: true, color: HAZ, fontFace: B, margin: 0, valign: 'middle' });
s.addNotes('Dejar el slide en pantalla mientras habla. La imagen se explica sola; no hay que narrarla renglón por renglón.');

/* ───────── 10 · LA HONESTA ───────── */
s = p.addSlide(); fondo(s, false);
titulo(s, 'Pero ojo: en Honduras la mano de obra es barata', false,
  'Eso debilita el argumento laboral, y hay que decirlo antes de que lo diga el cliente');
const hon = [['1 turno', '3 operadores', money(18927), '5.1 años', ROJO],
             ['2 turnos', '6 operadores', money(49854), '1.9 años', HAZ],
             ['3 turnos', '9 operadores', money(80781), '1.2 años', VERDE]];
fila(s, 0.65, 2.0, 7.4, 0.44, [{t:'OPERACIÓN',w:1.8},{t:'PERSONAL',w:1.8},
  {t:'AHORRO/AÑO',w:1.9,a:'right'},{t:'RETORNO',w:1.9,a:'right'}], false, true);
hon.forEach((h, i) => fila(s, 0.65, 2.44 + i * 0.66, 7.4, 0.66, [
  { t: h[0], w: 1.8, b: true, fs: 12 }, { t: h[1], w: 1.8, fs: 11, c: MUT2 },
  { t: h[2], w: 1.9, a: 'right', fs: 11.5 },
  { t: h[3], w: 1.9, a: 'right', b: true, fs: 13, c: h[4] }], false));
tarjeta(s, 8.35, 2.0, 4.3, 2.42, false, TINTA);
s.addText('El mismo kit en EE.UU.', { x: 8.7, y: 2.18, w: 3.6, h: 0.32, fontSize: 10.5, bold: true, color: HAZ, fontFace: B, charSpacing: 1.2, margin: 0 });
s.addText('0.3 años', { x: 8.7, y: 2.55, w: 3.6, h: 0.6, fontSize: 30, bold: true, color: HUM, fontFace: H, margin: 0 });
s.addText('Con un operador cargado a $55,000 al año, el mismo kit se paga en cuatro meses. Aquí tarda seis veces más.',
  { x: 8.7, y: 3.22, w: 3.6, h: 1.05, fontSize: 11, color: MUT, fontFace: B, margin: 0, valign: 'top' });
const real = [['Exactitud de inventario', 'El kit registra cada movimiento solo. Hoy eso se paga con conteos cíclicos y producto perdido.', VERDE],
              ['Daño a rack y producto', 'Un pasillo de 3.17 m con un equipo que pide 3.82 m produce golpes. El kit los cuenta y los evita.', HAZ],
              ['Turnos que hoy no se cubren', 'No es reemplazar al operador del día: es poder operar la noche sin contratar a nadie.', CIAN]];
s.addText('Entonces el retorno de verdad no es el salario:', { x: 0.65, y: 4.75, w: 12, h: 0.35,
  fontSize: 13, bold: true, color: TINTA, fontFace: B, margin: 0 });
real.forEach((r, i) => {
  const x = 0.65 + i * 4.06;
  tarjeta(s, x, 5.2, 3.82, 1.75, false);
  s.addShape(p.ShapeType.rect, { x: x + 0.3, y: 5.42, w: 0.55, h: 0.045, fill: { color: r[2] } });
  s.addText(r[0], { x: x + 0.3, y: 5.58, w: 3.2, h: 0.35, fontSize: 13, bold: true, color: TINTA, fontFace: B, margin: 0 });
  s.addText(r[1], { x: x + 0.3, y: 5.97, w: 3.2, h: 0.9, fontSize: 10, color: MUT2, fontFace: B, margin: 0, valign: 'top' });
});
s.addNotes('Este slide es el que da credibilidad. Si le vendés a Omar el cuento gringo del retorno en cuatro meses, lo va a descubrir solo y pierde confianza en todo lo demás. Decilo vos primero.');

/* ───────── 11 · LA RECOMENDACIÓN ───────── */
s = p.addSlide(); fondo(s, false);
titulo(s, 'La recomendación: empezar por la Fase 0', false,
  'No por tacañería. Porque es el que retira más riesgo por dólar.');
const rec = [['Prueba lo que no sabemos', 'Si el kit se ubica en el pasillo y lee una ubicación de rack a 6 m, el proyecto vive. Eso se contesta con hardware barato.', VERDE],
             ['No prueba lo que ya sabemos', 'Que un sensor industrial aguanta polvo y vibración no hay que demostrarlo: viene en la hoja de datos.', CIAN],
             ['Deja la decisión cara para después', 'Los ' + money(7000) + ' de escáneres certificados se compran cuando haya un cliente firmado, no antes.', HAZ]];
rec.forEach((r, i) => {
  const y = 1.95 + i * 1.35;
  tarjeta(s, 0.65, y, 12, 1.18, false);
  s.addShape(p.ShapeType.rect, { x: 0.65, y, w: 0.07, h: 1.18, fill: { color: r[2] } });
  s.addText(r[0], { x: 1.0, y: y + 0.16, w: 11.3, h: 0.4, fontSize: 16, bold: true, color: TINTA, fontFace: H, margin: 0 });
  s.addText(r[1], { x: 1.0, y: y + 0.6, w: 11.3, h: 0.5, fontSize: 12, color: MUT2, fontFace: B, margin: 0, valign: 'top' });
});
tarjeta(s, 0.65, 6.0, 12, 1.25, false, TINTA);
s.addText('Y si el de ' + money(3000) + ' falla, perdimos ' + money(3000) + '.\nSi hubiéramos empezado por el de ' + money(25000) + ', perdíamos ' + money(25000) + ' para aprender lo mismo.',
  { x: 1.05, y: 6.0, w: 11.2, h: 1.25, fontSize: 14, bold: true, color: HAZ, fontFace: B, margin: 0, valign: 'middle', lineSpacing: 22 });
s.addNotes('Este es el argumento que convence a un financiero: el barato no es peor, es el que compra información más rápido.');

/* ───────── 12 · LA CAPA DE SEGURIDAD VA APARTE ───────── */
s = p.addSlide(); fondo(s, false);
titulo(s, 'Por qué la seguridad no va en las dos primeras fases', false,
  'No es un recorte. Es que por norma esa capa vive separada del resto del sistema');
tarjeta(s, 0.65, 1.95, 5.9, 2.65, false);
s.addText('CÓMO FUNCIONA UN ESCÁNER CERTIFICADO', { x: 1.0, y: 2.15, w: 5.2, h: 0.3, fontSize: 10, bold: true, color: MUT2, fontFace: B, charSpacing: 1.2, margin: 0 });
s.addText([
  { text: 'Barre un plano a 15 cm del piso y define zonas de protección y de aviso', options: { bullet: true, breakLine: true } },
  { text: 'Si algo entra en la zona, sus dos salidas OSSD caen en menos de 80 ms', options: { bullet: true, breakLine: true } },
  { text: 'Esas salidas van cableadas al relé de seguridad, que corta la tracción', options: { bullet: true, breakLine: true } },
  { text: 'Doble canal: una falla sola no anula la función. Se autodiagnostica.', options: { bullet: true } },
], { x: 1.0, y: 2.55, w: 5.2, h: 1.9, fontSize: 11.5, color: TINTA, fontFace: B, paraSpaceAfter: 7, margin: 0, valign: 'top' });
tarjeta(s, 6.75, 1.95, 5.9, 2.65, false, TINTA);
s.addText('LO QUE NO HACE', { x: 7.1, y: 2.15, w: 5.2, h: 0.3, fontSize: 10, bold: true, color: HAZ, fontFace: B, charSpacing: 1.2, margin: 0 });
s.addText([
  { text: 'No alimenta el filtro de Kalman', options: { bullet: true, breakLine: true } },
  { text: 'No participa en la localización ni en el SLAM', options: { bullet: true, breakLine: true } },
  { text: 'No planifica rutas ni corrige la pose', options: { bullet: true, breakLine: true } },
  { text: 'No pasa por la computadora de navegación', options: { bullet: true } },
], { x: 7.1, y: 2.55, w: 5.2, h: 1.9, fontSize: 11.5, color: HUM, fontFace: B, paraSpaceAfter: 7, margin: 0, valign: 'top' });
tarjeta(s, 0.65, 4.85, 12, 1.15, false, TINTA);
s.addText('La norma exige que las dos capas estén aisladas: la salida de seguridad es certificada, el dato de navegación es sólo informativo. La computadora puede colgarse, el SLAM puede perderse, el software puede tener un bug — y la máquina se detiene igual.',
  { x: 1.05, y: 4.85, w: 11.2, h: 1.15, fontSize: 12.5, bold: true, color: HAZ, fontFace: B, margin: 0, valign: 'middle' });
s.addText('Por eso se puede desarrollar el 100% de la navegación sin los escáneres y montarlos después sin tocar una sola línea de la matemática, ni un solo parámetro de sintonización. Son paro de emergencia, no percepción.',
  { x: 0.65, y: 6.2, w: 12, h: 0.8, fontSize: 12.5, color: TINTA, fontFace: B, margin: 0, valign: 'top' });
s.addNotes('Este es el slide que contesta "¿por qué no traen seguridad desde el principio?". La respuesta es que la norma manda separarlas, así que agregarlas después no es deuda técnica: es la arquitectura correcta. Referencias: ISO 3691-4:2023, IEC 61496, ISO 13850.');

/* ───────── 13 · LA ÚNICA COSA QUE SÍ HAY QUE DISEÑAR DESDE HOY ───────── */
s = p.addSlide(); fondo(s, true);
titulo(s, 'La única cosa que sí hay que decidir desde hoy', true,
  'El escáner es un accesorio, pero su zona de protección dicta a qué velocidad puede andar la máquina');
const cp = [['0.5 m/s', '0.33 m', VERDE], ['1.0 m/s', '0.68 m', VERDE],
            ['1.5 m/s', '1.16 m', HAZ], ['2.0 m/s', '1.76 m', HAZ], ['3.3 m/s', '3.91 m', ROJO]];
fila(s, 0.65, 2.1, 7.0, 0.44, [{t:'VELOCIDAD',w:2.4},{t:'ZONA DE PROTECCIÓN MÍNIMA',w:4.6,a:'right'}], true, true);
cp.forEach((c, i) => fila(s, 0.65, 2.54 + i * 0.62, 7.0, 0.62, [
  { t: c[0], w: 2.4, b: true, fs: 13 },
  { t: c[1], w: 4.6, a: 'right', b: true, fs: 14, c: c[2] }], true));
tarjeta(s, 8.05, 2.1, 4.6, 3.68, true, PANEL);
s.addText('El tope físico', { x: 8.4, y: 2.32, w: 3.9, h: 0.3, fontSize: 10.5, bold: true, color: HAZ, fontFace: B, charSpacing: 1.2, margin: 0 });
s.addText('A 3.3 m/s la zona de protección tendría que medir 3.91 m — más de lo que mide de ancho el pasillo actual.',
  { x: 8.4, y: 2.72, w: 3.9, h: 1.1, fontSize: 12, color: HUM, fontFace: B, margin: 0, valign: 'top' });
s.addText('Por eso ningún montacargas autónomo del mundo anda a velocidad de catálogo bajo techo. Todos operan entre 1 y 1.5 m/s.',
  { x: 8.4, y: 3.85, w: 3.9, h: 1.2, fontSize: 12, color: MUT, fontFace: B, margin: 0, valign: 'top' });
s.addText('Diseñamos para 1.5 m/s desde la Fase 0.', { x: 8.4, y: 5.1, w: 3.9, h: 0.5,
  fontSize: 13, bold: true, color: VERDE, fontFace: B, margin: 0, valign: 'top' });
tarjeta(s, 0.65, 6.0, 12, 1.15, true, PANEL);
s.addText('Reacción total 330 ms: 80 del escáner, 50 del controlador y del contactor, 200 de respuesta del freno. Más la distancia de frenado. Si fijamos hoy el sobre de velocidad, el escáner de la Fase 2 entra sin rediseñar nada.',
  { x: 1.05, y: 6.0, w: 11.2, h: 1.15, fontSize: 12.5, bold: true, color: HAZ, fontFace: B, margin: 0, valign: 'middle' });
s.addNotes('El matiz honesto: el hardware es add-on, pero el sobre de velocidad no. Si desarrollamos a 3 m/s y después metemos el escáner, hay que rehacer el control. Por eso se fija ahora, y no cuesta nada fijarlo.');

/* ───────── 14 · MENOS HARDWARE, MÁS SOFTWARE ───────── */
s = p.addSlide(); fondo(s, false);
titulo(s, 'Menos hardware, más software', false,
  'Es la lección que nos dejó el proyecto de graduación, y es también dónde está el negocio');
tarjeta(s, 0.65, 1.95, 12, 1.35, false, TINTA);
s.addText('"No lo necesitan. Menos hardware, más software."',
  { x: 1.1, y: 2.1, w: 11.1, h: 0.5, fontSize: 18, bold: true, italic: true, color: HAZ, fontFace: H, margin: 0 });
s.addText('Lo dijo el profesor cuando el equipo quería agregarle otra cámara al robot. Salió adelante con una Jetson de $250 sobre un PuzzleBot. Lo que se pide aquí es hardware sustancialmente mejor que aquello.',
  { x: 1.1, y: 2.62, w: 11.1, h: 0.6, fontSize: 12, color: MUT, fontFace: B, margin: 0, valign: 'top' });
const arg = [['El hardware pone el techo', 'El software decide cuánto de ese techo alcanzás. Los proyectos de robótica no fracasan por sensores baratos: fracasan por software flojo.', CIAN],
             ['Cada sensor es un modo de falla', 'Una calibración más, un cable más, una superficie más que se ensucia. Menos piezas es más confiable, no menos capaz.', HAZ],
             ['El sensor es commodity', 'Cualquiera compra un LiDAR. Lo que Montasa sería dueña es del software que lo hace funcionar en pasillos de 3.17 m con maxicubos.', VERDE]];
arg.forEach((a, i) => {
  const x = 0.65 + i * 4.06;
  tarjeta(s, x, 3.55, 3.82, 2.35, false);
  s.addShape(p.ShapeType.rect, { x: x + 0.32, y: 3.8, w: 0.6, h: 0.045, fill: { color: a[2] } });
  s.addText(a[0], { x: x + 0.32, y: 3.98, w: 3.2, h: 0.7, fontSize: 15, bold: true, color: TINTA, fontFace: H, margin: 0, valign: 'top' });
  s.addText(a[1], { x: x + 0.32, y: 4.72, w: 3.2, h: 1.05, fontSize: 11, color: MUT2, fontFace: B, margin: 0, valign: 'top' });
});
tarjeta(s, 0.65, 6.15, 12, 1.05, false, TINTA);
s.addText('Con aquel hardware alcanzó. Con este, la pregunta ya no es si el hardware da — es si el software da. Y esa pregunta se responde con ' + money(3000) + ', no con ' + money(25000) + '.',
  { x: 1.05, y: 6.15, w: 11.2, h: 1.05, fontSize: 13.5, bold: true, color: HAZ, fontFace: B, margin: 0, valign: 'middle' });
s.addNotes('Contar la anécdota del profesor en voz alta, corta. Y rematar con el argumento de negocio: el foso no es el sensor, es el software. Si Omar entiende eso, entiende por qué la Fase 0 es suficiente para decidir.');

/* ───────── 15 · QUÉ LLEVA LA FASE 0 ───────── */
s = p.addSlide(); fondo(s, false);
titulo(s, 'Qué lleva la Fase 0 · Validación', false, '25 componentes. El LiDAR es el 25% del presupuesto, y va completo.');
const b3 = [['Navegación', 'LiDAR 3D Livox Mid-360 · IMU · encoders de tracción y dirección · marcadores', 1049, CIAN],
            ['Cómputo', 'Jetson Orin Nano 8 GB · NVMe · caja IP54 · alimentación y protección', 769, HAZ],
            ['Visión', 'Cámara de uñas · cámara de mástil 5 MP para leer ubicaciones', 330, VERDE],
            ['Carga', 'Altura de uñas por láser · presión hidráulica · fotocélula', 330, HAZ],
            ['Interfaz y red', 'Router · antenas · tablet · barra de estado · torreta y luces', 400, MUT2],
            ['Montaje', 'Arnés y soportes armados en el taller · consumibles', 315, MUT2]];
fila(s, 0.65, 2.0, 12, 0.44, [{t:'MÓDULO',w:2.3},{t:'QUÉ INCLUYE',w:7.5},{t:'USD',w:2.2,a:'right'}], false, true);
b3.forEach((r, i) => fila(s, 0.65, 2.44 + i * 0.62, 12, 0.62, [
  { t: r[0], w: 2.3, b: true, c: r[3], fs: 11.5 },
  { t: r[1], w: 7.5, fs: 10, c: MUT2 },
  { t: money(r[2]), w: 2.2, a: 'right', b: true, fs: 12.5 }], false));
fila(s, 0.65, 6.16, 12, 0.66, [{ t: 'TOTAL HARDWARE', w: 9.8, b: true, fs: 13 },
  { t: money(3033), w: 2.2, a: 'right', b: true, fs: 16, c: HAZ }], false);
s.addText('El montacargas lo presta Montasa. La mano de obra la pone el equipo. Herramienta de taller no incluida: se compra una vez y se queda.',
  { x: 0.65, y: 6.95, w: 12, h: 0.4, fontSize: 10.5, italic: true, color: MUT2, fontFace: B, margin: 0 });
s.addNotes('Si pregunta por qué un LiDAR de $749 en un prototipo barato: porque sin él no se prueba la navegación, que es justamente lo que no sabemos.');

/* ───────── 10 · ECONOMÍA DEL PILOTO ───────── */
s = p.addSlide(); fondo(s, false);
titulo(s, 'Economía del primer piloto', false, '3 unidades a nivel 1, más la infraestructura del sitio');
const eco = [['Hardware de 3 unidades', 25644], ['Infraestructura del almacén', 14288], ['Flete e importación, 20%', 7986]];
fila(s, 0.65, 2.0, 6.0, 0.42, [{t:'COSTO DE MATERIALES',w:4.2},{t:'USD',w:1.8,a:'right'}], false, true);
eco.forEach((r, i) => fila(s, 0.65, 2.42 + i * 0.55, 6.0, 0.55,
  [{ t: r[0], w: 4.2, fs: 11 }, { t: money(r[1]), w: 1.8, a: 'right', b: true, fs: 12 }], false));
fila(s, 0.65, 4.07, 6.0, 0.6, [{ t: 'TOTAL MATERIALES', w: 4.2, b: true, fs: 12 },
  { t: money(47918), w: 1.8, a: 'right', b: true, fs: 14, c: ROJO }], false);
s.addText('La instalación la absorbe el taller de Montasa: 3 a 5 días por unidad la primera vez.',
  { x: 0.65, y: 4.8, w: 6.0, h: 0.6, fontSize: 10.5, italic: true, color: MUT2, fontFace: B, margin: 0, valign: 'top' });
const esc = [['Piloto a costo', 50000, 2082, '4%', MUT2], ['Conservador', 70000, 22082, '32%', CIAN],
             ['Base', 82000, 34082, '42%', VERDE], ['Alto', 94000, 46082, '49%', HAZ]];
fila(s, 7.05, 2.0, 5.6, 0.42, [{t:'ESCENARIO',w:1.7},{t:'PRECIO',w:1.35,a:'right'},{t:'MARGEN',w:1.35,a:'right'},{t:'%',w:1.2,a:'right'}], false, true);
esc.forEach((e, i) => fila(s, 7.05, 2.42 + i * 0.62, 5.6, 0.62, [
  { t: e[0], w: 1.7, b: true, fs: 11, c: e[4] },
  { t: money(e[1]), w: 1.35, a: 'right', fs: 11 },
  { t: money(e[2]), w: 1.35, a: 'right', fs: 11 },
  { t: e[3], w: 1.2, a: 'right', b: true, fs: 12, c: e[4] }], false));
tarjeta(s, 7.05, 5.0, 5.6, 1.25, false, TINTA);
s.addText('Con el escenario base, el piloto devuelve los ' + money(3000) + ' del prototipo más de diez veces.',
  { x: 7.4, y: 5.0, w: 4.9, h: 1.25, fontSize: 12, bold: true, color: VERDE, fontFace: B, margin: 0, valign: 'middle' });
s.addText('Margen bruto sobre materiales. No descuenta horas de ingeniería ni instalación. Los precios de venta son una decisión pendiente, no un compromiso.',
  { x: 0.65, y: 6.6, w: 12, h: 0.6, fontSize: 10.5, italic: true, color: MUT2, fontFace: B, margin: 0, valign: 'top' });
s.addNotes('En el primer cliente vale más el caso de referencia que el margen. Pero la decisión es de Omar.');

/* ───────── 11 · EL NEGOCIO RECURRENTE ───────── */
s = p.addSlide(); fondo(s, true);
titulo(s, 'Dónde está el negocio de verdad', true,
  'La venta de hardware abre la puerta. El ingreso recurrente es lo que sostiene el producto.');
const rc = [['Hardware', 'Una vez por unidad', 'Margen alto, pero no se repite', money(8548) + ' de costo', ROJO],
            ['Instalación e integración', 'Una vez por sitio', 'La cobra el taller que ya existe', 'Capacidad instalada', HAZ],
            ['Software y monitoreo', 'Todos los años, por unidad', 'Es lo que hace escalable el negocio', '$3,000 – $5,500 por unidad/año', VERDE]];
rc.forEach((r, i) => {
  const x = 0.65 + i * 4.06;
  tarjeta(s, x, 2.05, 3.82, 2.8, true);
  s.addShape(p.ShapeType.rect, { x: x + 0.32, y: 2.35, w: 0.6, h: 0.045, fill: { color: r[4] } });
  s.addText(r[0], { x: x + 0.32, y: 2.52, w: 3.2, h: 0.42, fontSize: 18, bold: true, color: HUM, fontFace: H, margin: 0 });
  s.addText(r[1], { x: x + 0.32, y: 2.98, w: 3.2, h: 0.3, fontSize: 10.5, bold: true, color: r[4], fontFace: B, margin: 0 });
  s.addText(r[2], { x: x + 0.32, y: 3.35, w: 3.2, h: 0.72, fontSize: 11.5, color: MUT, fontFace: B, margin: 0, valign: 'top' });
  s.addText(r[3], { x: x + 0.32, y: 4.22, w: 3.2, h: 0.4, fontSize: 12, bold: true, color: HUM, fontFace: B, margin: 0 });
});
tarjeta(s, 0.65, 5.25, 12, 1.6, true, PANEL);
s.addText('Tres unidades en el primer cliente son unos $12,000 al año de ingreso recurrente. Si en 12 meses hay tres sitios operando, son cerca de $36,000 anuales que no dependen de vender hardware nuevo.',
  { x: 1.05, y: 5.25, w: 11.2, h: 1.6, fontSize: 13.5, bold: true, color: HAZ, fontFace: B, margin: 0, valign: 'middle' });
s.addNotes('Un negocio de hardware puro no le interesa a un financiero; uno con cola recurrente sí.');

/* ───────── 12 · MATRIZ DE RIESGOS ───────── */
s = p.addSlide(); fondo(s, false);
titulo(s, 'Matriz de riesgos', false, 'Ocho riesgos identificados, cada uno con su mitigación');
const R = [['Técnico', 'El controlador del Baoli no expone comunicación abierta', 'Media', 'Alto', 'Validar en un equipo del taller antes de comprar', ROJO],
           ['Comercial', 'El layout del cliente no admite contrabalanceado', 'Alta', 'Medio', 'Se resuelve en la visita de levantamiento', HAZ],
           ['Legal', 'Responsabilidad civil por operación desatendida', 'Baja', 'Muy alto', 'No vender nivel 3 sin escáneres certificados. Política escrita.', ROJO],
           ['Financiero', 'Volatilidad de precios de componentes', 'Alta', 'Medio', 'Cotizaciones con validez de 30 días y segunda fuente de cómputo', HAZ],
           ['Concentración', 'Depender de un solo cliente para el caso de referencia', 'Media', 'Alto', 'La base instalada de Montasa da alternativas', HAZ],
           ['Ejecución', 'Sobre-prometer plazos de instalación', 'Alta', 'Medio', 'La primera instalación se cotiza al triple del tiempo estimado', HAZ],
           ['Competitivo', 'Que el fabricante lance un retrofit oficial', 'Baja', 'Alto', 'Velocidad, y la relación de Montasa con Baoli', CIAN],
           ['Organizacional', 'Equipo pequeño, dependencia de una persona', 'Alta', 'Alto', 'Documentar desde el día uno y repartir el conocimiento', ROJO]];
fila(s, 0.65, 1.95, 12, 0.4, [{t:'TIPO',w:1.55},{t:'RIESGO',w:4.3},{t:'PROB.',w:0.95,a:'center'},{t:'IMPACTO',w:1.1,a:'center'},{t:'MITIGACIÓN',w:4.1}], false, true);
R.forEach((r, i) => fila(s, 0.65, 2.35 + i * 0.58, 12, 0.58, [
  { t: r[0], w: 1.55, b: true, fs: 10, c: r[5] }, { t: r[1], w: 4.3, fs: 10 },
  { t: r[2], w: 0.95, a: 'center', fs: 10, c: MUT2 },
  { t: r[3], w: 1.1, a: 'center', b: true, fs: 10, c: r[5] },
  { t: r[4], w: 4.1, fs: 9.5, c: MUT2 }], false));
s.addText('Ningún riesgo de la lista requiere desembolso adicional para mitigarse. El más caro se resuelve con dos horas de taller.',
  { x: 0.65, y: 7.05, w: 12, h: 0.35, fontSize: 11.5, bold: true, color: TINTA, fontFace: B, margin: 0 });
s.addNotes('Un jefe financiero desconfía más de una presentación sin riesgos que de una con ocho.');

/* ───────── 13 · LOS TRES QUE IMPORTAN ───────── */
s = p.addSlide(); fondo(s, true);
titulo(s, 'Los tres riesgos que de verdad pueden matar esto', true, 'Y qué se hace con cada uno, en concreto');
const R3 = [['El Baoli no habla', 'Si el controlador Curtis o ZAPI no expone el bus, hay que poner actuadores mecánicos sobre los pedales y la dirección.',
             'Cuesta ' + money(3400) + ' más por unidad y unas 8 semanas de ingeniería adicional.',
             'Se valida esta semana, gratis, en un equipo del taller. Antes de comprar un solo componente.', ROJO],
            ['El cliente equivocado', 'Si el cliente opera reach trucks y no contrabalanceados, el kit hay que diseñarlo para otra máquina.',
             'No mata el producto, pero mueve el calendario unos dos meses.',
             'Se resuelve en la visita de levantamiento, antes de comprometer diseño.', HAZ],
            ['La primera instalación', 'Todo proyecto primerizo tarda el triple de lo estimado. Si le prometemos al cliente una fecha optimista, quemamos la referencia.',
             'El daño no es el costo: es perder el caso de éxito que justifica todo lo demás.',
             'Cotizar plazos al triple y comunicar la Fase Watch como el entregable, no la autonomía.', ROJO]];
R3.forEach((r, i) => {
  const y = 2.0 + i * 1.66;
  tarjeta(s, 0.65, y, 12, 1.48, true);
  s.addShape(p.ShapeType.rect, { x: 0.65, y, w: 0.07, h: 1.48, fill: { color: r[4] } });
  s.addText(r[0], { x: 1.0, y: y + 0.14, w: 3.0, h: 0.4, fontSize: 15, bold: true, color: r[4], fontFace: H, margin: 0 });
  s.addText(r[1], { x: 1.0, y: y + 0.58, w: 3.1, h: 0.8, fontSize: 9.5, color: MUT, fontFace: B, margin: 0, valign: 'top' });
  s.addText('SI PASA', { x: 4.35, y: y + 0.16, w: 3.6, h: 0.25, fontSize: 8.5, bold: true, color: MUT, fontFace: B, charSpacing: 1.4, margin: 0 });
  s.addText(r[2], { x: 4.35, y: y + 0.45, w: 3.6, h: 0.9, fontSize: 10.5, color: HUM, fontFace: B, margin: 0, valign: 'top' });
  s.addText('QUÉ SE HACE', { x: 8.2, y: y + 0.16, w: 4.1, h: 0.25, fontSize: 8.5, bold: true, color: VERDE, fontFace: B, charSpacing: 1.4, margin: 0 });
  s.addText(r[3], { x: 8.2, y: y + 0.45, w: 4.1, h: 0.9, fontSize: 10.5, color: HUM, fontFace: B, margin: 0, valign: 'top' });
});
s.addNotes('Los tres se mitigan con información, no con dinero. Por eso la visita al cliente y la prueba de taller van antes del desembolso.');

/* ───────── 14 · CALENDARIO ───────── */
s = p.addSlide(); fondo(s, false);
titulo(s, 'Calendario y puertas de decisión', false,
  'Tres puntos donde se puede parar sin haber perdido lo invertido');
const cal = [['Mes 0', 'Validación en taller', 'Se prueba el bus CAN en un Baoli. Sin costo.', 'PUERTA 1 · si no hay bus, se recotiza antes de comprar', ROJO],
             ['Mes 1–3', 'Fase 0 · Validación', 'Se compra el hardware y se monta el primer kit sobre un demo.', '', CIAN],
             ['Mes 3', 'Prueba de aceptación', 'El kit debe ubicarse en el pasillo y leer una ubicación de rack a 6 m.', 'PUERTA 2 · si no lo logra, se para aquí', ROJO],
             ['Mes 4–6', 'Fase 1 · Producto', 'Con la prueba pasada, se pide el resto y se arma el kit vendible.', 'PUERTA 3 · sólo si la Puerta 2 salió limpia', HAZ],
             ['Mes 6–8', 'Piloto en el cliente', 'Instalación de 3 unidades más la infraestructura del sitio.', '', HAZ],
             ['Mes 8–12', 'Fase Watch en operación', 'Datos reales de ciclos, conflictos y exactitud de inventario.', '', VERDE]];
cal.forEach((c, i) => {
  const y = 1.95 + i * 0.86;
  s.addShape(p.ShapeType.rect, { x: 0.65, y: y + 0.06, w: 0.06, h: 0.62, fill: { color: c[4] } });
  s.addText(c[0], { x: 0.88, y: y + 0.04, w: 1.15, h: 0.34, fontSize: 12, bold: true, color: c[4], fontFace: B, margin: 0 });
  s.addText(c[1], { x: 2.1, y: y + 0.04, w: 3.0, h: 0.34, fontSize: 12.5, bold: true, color: TINTA, fontFace: B, margin: 0 });
  s.addText(c[2], { x: 5.2, y: y + 0.06, w: 4.0, h: 0.6, fontSize: 10, color: MUT2, fontFace: B, margin: 0, valign: 'top' });
  if (c[3]) s.addText(c[3], { x: 9.35, y: y + 0.06, w: 3.3, h: 0.6, fontSize: 9.5, bold: true, color: c[4], fontFace: B, margin: 0, valign: 'top' });
});
s.addText('El desembolso grande sólo ocurre después de la Puerta 2, que cuesta ' + money(3000) + '. Hasta ahí, lo arriesgado es tiempo.',
  { x: 0.65, y: 7.05, w: 12, h: 0.35, fontSize: 12, bold: true, color: TINTA, fontFace: B, margin: 0 });
s.addNotes('Las puertas le dan tranquilidad al financiero: no es un cheque en blanco, son tres decisiones con criterio definido.');

/* ───────── 15 · EL PEDIDO ───────── */
s = p.addSlide(); fondo(s, true);
titulo(s, 'Lo que necesito de vos', true, 'Cuatro cosas, y sólo una involucra dinero');
const ped = [['1', money(3000) + ' en materiales', 'Fase 0 · Validación. El primer kit, con LiDAR 3D de verdad.', CIAN],
             ['2', 'Un montacargas de demo', 'Prestado por unos 4 meses. Sin costo en efectivo, pero sale de rotación.', HAZ],
             ['3', 'Visto bueno estratégico', 'Que TaTa siga como línea de producto de Montasa y no como proyecto suelto.', VERDE],
             ['4', 'Autorización de las puertas', 'Que las tres decisiones de paro queden acordadas por escrito desde hoy.', HAZ]];
ped.forEach((q, i) => {
  const y = 2.05 + i * 1.12;
  tarjeta(s, 0.65, y, 12, 0.95, true);
  chip(s, q[0], 1.0, y + 0.27, q[3]);
  s.addText(q[1], { x: 1.62, y: y + 0.16, w: 4.3, h: 0.4, fontSize: 15, bold: true, color: HUM, fontFace: B, margin: 0 });
  s.addText(q[2], { x: 6.0, y: y + 0.18, w: 6.3, h: 0.6, fontSize: 11, color: MUT, fontFace: B, margin: 0, valign: 'top' });
});
tarjeta(s, 0.65, 6.6, 12, 0.75, true, PANEL);
s.addText('Si el prototipo no pasa la Puerta 2, la pérdida máxima es ' + money(3000) + '. Eso es lo que cuesta saber si esto funciona.',
  { x: 1.05, y: 6.6, w: 11.2, h: 0.75, fontSize: 13, bold: true, color: HAZ, fontFace: B, margin: 0, valign: 'middle' });
s.addNotes('Cerrar con la pérdida máxima cuantificada. Es la frase que un jefe financiero necesita oír para decir que sí.');

/* ───────── 16 · ANEXO ───────── */
s = p.addSlide(); fondo(s, false);
titulo(s, 'Anexo · Supuestos y fuentes', false, 'Lo que hay que revalidar antes de convertir esto en un compromiso');
const sup = [['Precios de hardware', 'Precios de lista públicos consultados en agosto 2026, sin descuento por volumen. NVIDIA subió el módulo de cómputo 67% en julio 2026: es el renglón más volátil.'],
             ['Flete e importación', 'Estimado en 20% del valor del hardware. Debe confirmarse con el agente aduanal de Montasa.'],
             ['Horas de ingeniería', 'No están incluidas en ninguno de los tres montos. Son horas del equipo.'],
             ['Precios de venta', 'Los escenarios del piloto son ilustrativos. No se ha comunicado ningún precio al cliente.'],
             ['Comparables de mercado', 'Rangos de montacargas autónomos de fábrica y de mantenimiento anual tomados de publicaciones del sector, agosto 2026.'],
             ['Geometría del almacén', 'Medida sobre el archivo DWG del cliente, confirmado en metros. Pendiente de verificar con cinta en sitio.']];
sup.forEach((a, i) => {
  const y = 1.95 + i * 0.83;
  s.addShape(p.ShapeType.rect, { x: 0.65, y: y + 0.08, w: 0.05, h: 0.55, fill: { color: MUT } });
  s.addText(a[0], { x: 0.92, y: y + 0.02, w: 2.9, h: 0.34, fontSize: 12, bold: true, color: TINTA, fontFace: B, margin: 0 });
  s.addText(a[1], { x: 3.9, y: y + 0.04, w: 8.7, h: 0.66, fontSize: 10.5, color: MUT2, fontFace: B, margin: 0, valign: 'top' });
});
s.addText('El detalle línea por línea está en TaTa_Kit_BOM.xlsx, con proveedor y alternativa más barata para cada componente.',
  { x: 0.65, y: 6.95, w: 12, h: 0.4, fontSize: 11, italic: true, color: MUT2, fontFace: B, margin: 0 });
s.addNotes('Tener el BOM abierto en la laptop por si Omar pide ver una línea.');

p.writeFile({ fileName: 'TaTa_Caso_Negocio_Omar.pptx' }).then(() => console.log('deck OMAR v2 listo'));
