// Renderiza o palco (telas do iPhone + cartões) quadro a quadro, sem perder nada:
// só tira foto quando algo mudou; quadros parados repetem a última foto (lista para o concat do ffmpeg).
// Uso: node renderizar.js linha-do-tempo.json pasta-saida [fps=30] [escala=2] [inicio_s] [fim_s]
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
(async () => {
  const [tlArq, saida, fpsA, escA, iniA, fimA] = process.argv.slice(2);
  const fps = +(fpsA || 30), esc = +(escA || 2);
  const tl = JSON.parse(fs.readFileSync(tlArq, 'utf8'));
  const total = tl.duracao, ini = +(iniA || 0), fim = Math.min(+(fimA || total), total);
  fs.mkdirSync(saida, { recursive: true });
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: esc });
  await pg.goto('file://' + path.resolve(__dirname, process.env.PALCO || 'palco.html'));
  await pg.evaluate(() => document.fonts.ready);
  await pg.waitForTimeout(500);
  await pg.evaluate(l => window.iniciar(l), tl.acoes);
  const lista = []; let n = 0, ultimaFoto = null, repet = 0;
  const N = Math.round(fim * fps);
  // avança o relógio até o início sem fotografar
  for (let i = 0; i < Math.round(ini * fps); i++) await pg.evaluate(t => window.render(t), i / fps);
  let sujoAntes = true;
  for (let i = Math.round(ini * fps); i < N; i++) {
    const t = i / fps;
    const mudou = await pg.evaluate(t => window.render(t), t);
    if (mudou || sujoAntes || !ultimaFoto) {
      if (ultimaFoto) lista.push({ f: ultimaFoto, d: repet / fps });
      ultimaFoto = `q${String(n++).padStart(6, '0')}.jpg`;
      await pg.screenshot({ path: path.join(saida, ultimaFoto), type: 'jpeg', quality: 93 });
      repet = 1;
    } else repet++;
    sujoAntes = mudou;
    if (i % 600 === 0) console.log(`t=${t.toFixed(0)}s fotos=${n}`);
  }
  if (ultimaFoto) lista.push({ f: ultimaFoto, d: repet / fps });
  let txt = 'ffconcat version 1.0\n';
  for (const q of lista) txt += `file ${q.f}\nduration ${q.d.toFixed(6)}\n`;
  txt += `file ${lista[lista.length - 1].f}\n`;
  fs.writeFileSync(path.join(saida, 'lista.txt'), txt);
  console.log('fotos', n, 'quadros', N - Math.round(ini * fps));
  await b.close();
})();
