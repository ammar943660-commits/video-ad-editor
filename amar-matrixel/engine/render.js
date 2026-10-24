#!/usr/bin/env node
/* ═══ render.js — يرسم مشروع وصفة AMAR Matrixel بكروم بلا واجهة ═══
   node render.js <projectDir> [--scale 0.5] [--frames 0-59] [--out dir] [--workers 2] [--no-encode] [--still 1.5]
   المخرجات (داخل <projectDir>/renders أو --out):
     frames/00000.png   طبقة RGBA شفافة (أو JPEG للـplates)
     overlay.mov        ProRes 4444 + ألفا (للبريمير/AE)
     overlay.webm       VP9 + ألفا
     preview.mp4        الطبقة فوق اللقطة (لو project.plate موجودة) + صوت لو sfx.wav موجود
     meta.json          بيانات إضافية من الوصفة (مثل Ground Truth) */
const fs = require('fs'), path = require('path'), http = require('http'), { spawnSync } = require('child_process');
const ROOT = path.resolve(__dirname, '..'), REPO = path.resolve(ROOT, '..');
const VENDOR = path.join(REPO, 'video-ad-editor/motion/vendor/three'), FONTS = path.join(REPO, 'video-ad-editor/motion/fonts');
const CHROME = process.env.CHROME || ['/opt/pw-browsers/chromium-1243/chrome-linux64/chrome', '/usr/bin/chromium', '/usr/bin/google-chrome', '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'].find(p => fs.existsSync(p));
const puppeteer = require('puppeteer-core');
const argv = process.argv.slice(2);
const flag = (n, d) => { const i = argv.indexOf('--' + n); if (i < 0) return d; const v = argv[i + 1]; return v === undefined || v.startsWith('--') ? true : v; };
const PROJ = path.resolve(argv.find(a => !a.startsWith('--') && (argv.indexOf(a) === 0 || !argv[argv.indexOf(a) - 1].startsWith('--'))) || '.');
if (!fs.existsSync(path.join(PROJ, 'project.json'))) { console.error('❌ no project.json in ' + PROJ); process.exit(2); }
const SCALE = parseFloat(flag('scale', '1')), WORKERS = parseInt(flag('workers', '2')), NOENC = !!flag('no-encode', false);
const OUT = path.resolve(flag('out', path.join(PROJ, 'renders')));
const proj = JSON.parse(fs.readFileSync(path.join(PROJ, 'project.json'), 'utf8'));
const TYPES = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.mjs': 'text/javascript', '.json': 'application/json', '.ttf': 'font/ttf', '.png': 'image/png', '.jpg': 'image/jpeg' };
const MAP = [['/three/', VENDOR], ['/fonts/', FONTS], ['/engine/', __dirname], ['/proj/', PROJ]];
function serve() { return new Promise(res => { const srv = http.createServer((req, rsp) => {
  const u = decodeURIComponent(req.url.split('?')[0]); let file = null;
  if (u === '/stage.html') file = path.join(__dirname, 'stage.html'); else for (const [p, d] of MAP) if (u.startsWith(p)) { file = path.join(d, u.slice(p.length)); break; }
  if (!file) { rsp.writeHead(404); return rsp.end(); }
  fs.readFile(file, (e, data) => { if (e) { rsp.writeHead(404); return rsp.end('404'); } rsp.writeHead(200, { 'Content-Type': TYPES[path.extname(file)] || 'application/octet-stream', 'Cache-Control': 'no-store' }); rsp.end(data); });
}); srv.listen(0, '127.0.0.1', () => res(srv)); }); }
async function open(browser, port) {
  const page = await browser.newPage(); await page.setViewport({ width: 400, height: 400 });
  page.on('pageerror', e => console.log('  [page error] ' + e.message));
  page.on('console', m => { if (m.type() === 'error') console.log('  [console] ' + m.text()); });
  await page.goto(`http://127.0.0.1:${port}/stage.html?scale=${SCALE}`);
  await page.waitForFunction('window.AMX && (window.AMX.ready || window.AMX.error)', { timeout: 120000 });
  const err = await page.evaluate('window.AMX.error'); if (err) throw new Error('boot failed:\n' + err);
  return page;
}
(async () => {
  const srv = await serve(), port = srv.address().port;
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--no-sandbox', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--enable-webgl', '--disable-dev-shm-usage', '--font-render-hinting=none'] });
  const pages = []; for (let i = 0; i < WORKERS; i++) pages.push(await open(browser, port));
  const info = await pages[0].evaluate('window.AMX.info');
  let [a, b] = String(flag('frames', '0-' + (info.frames - 1))).split('-').map(Number); if (flag('still', false)) { a = b = Math.round(parseFloat(flag('still')) * info.fps); }
  const ext = info.output === 'opaque' ? 'jpg' : 'png', FR = path.join(OUT, 'frames'); fs.rmSync(FR, { recursive: true, force: true }); fs.mkdirSync(FR, { recursive: true });
  const idx = []; for (let i = a; i <= b; i++) idx.push(i);
  const t0 = Date.now(); let done = 0;
  await Promise.all(pages.map(async (pg, w) => { for (let k = w; k < idx.length; k += WORKERS) { const i = idx[k]; const b64 = await pg.evaluate(i => window.AMX.frame(i), i); fs.writeFileSync(path.join(FR, String(i).padStart(5, '0') + '.' + ext), Buffer.from(b64, 'base64')); if (++done % 20 === 0) process.stdout.write(`\r  ${done}/${idx.length} frames (${((Date.now() - t0) / 1000).toFixed(0)}s)`); } }));
  const logs = (await Promise.all(pages.map(pg => pg.evaluate('window.AMX.log ? window.AMX.log() : []')))).flat(); if (logs.length) fs.writeFileSync(path.join(OUT, 'frame-log.json'), JSON.stringify(logs));
  const meta = await pages[0].evaluate('window.AMX.meta && window.AMX.meta()'); if (meta) fs.writeFileSync(path.join(OUT, 'meta.json'), JSON.stringify(meta));
  fs.writeFileSync(path.join(OUT, 'render-info.json'), JSON.stringify({ ...info, first: a, last: b, scale: SCALE, ms: Date.now() - t0 }));
  console.log(`\n✓ ${idx.length} frames ${info.W}×${info.H} in ${((Date.now() - t0) / 1000).toFixed(1)}s → ${FR}`);
  await browser.close(); srv.close();
  if (NOENC || a === b) return;
  const fps = info.fps, inp = ['-framerate', String(fps), '-start_number', String(a), '-i', path.join(FR, '%05d.' + ext)];
  const ff = args => { const r = spawnSync('ffmpeg', ['-v', 'error', '-y', ...args], { encoding: 'utf8' }); if (r.status) console.log('  ffmpeg:', r.stderr.slice(0, 400)); return !r.status; };
  if (info.output === 'opaque') { ff([...inp, '-c:v', 'libx264', '-crf', '14', '-pix_fmt', 'yuv420p', path.join(OUT, 'plate.mp4')]); console.log('✓ plate.mp4'); return; }
  ff([...inp, '-c:v', 'prores_ks', '-profile:v', '4444', '-pix_fmt', 'yuva444p10le', path.join(OUT, 'overlay.mov')]);
  ff([...inp, '-c:v', 'libvpx-vp9', '-pix_fmt', 'yuva420p', '-b:v', '0', '-crf', '28', '-auto-alt-ref', '0', path.join(OUT, 'overlay.webm')]);
  console.log('✓ overlay.mov (ProRes 4444 α) + overlay.webm (VP9 α)');
  if (proj.plate && fs.existsSync(path.join(PROJ, proj.plate))) {
    const sfx = path.join(PROJ, 'sfx.wav'), hasA = fs.existsSync(sfx);
    const args = ['-i', path.join(PROJ, proj.plate), ...inp];
    if (hasA) args.push('-i', sfx);
    args.push('-filter_complex', `[0:v]scale=${info.W}:${info.H}:force_original_aspect_ratio=increase,crop=${info.W}:${info.H},fps=${fps},setsar=1[bg];[bg][1:v]overlay=shortest=1:format=auto[o]`, '-map', '[o]');
    if (hasA) args.push('-map', '2:a', '-c:a', 'aac', '-b:a', '192k');
    args.push('-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', '-shortest', path.join(OUT, 'preview.mp4'));
    if (ff(args)) console.log('✓ preview.mp4 (plate + overlay' + (hasA ? ' + sfx' : '') + ')');
  }
})().catch(e => { console.error(e); process.exit(1); });
