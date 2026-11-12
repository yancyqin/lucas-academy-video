// usage: node render.cjs props.json out.mp4 [scale]   (still: node render.cjs props.json out.jpg scale frame)
const fs = require('node:fs');
const path = require('node:path');
const {bundle} = require('@remotion/bundler');
const {openBrowser, renderMedia, renderStill, selectComposition} = require('@remotion/renderer');

async function main() {
  const [propsPath, out, scale = '0.5', frame] = process.argv.slice(2);
  const inputProps = JSON.parse(fs.readFileSync(propsPath, 'utf8'));
  const repo = path.resolve(__dirname, '../..');
  const serveUrl = await bundle({entryPoint: path.join(repo, 'src/videos/leaf-truck/LeafTruck.tsx'), rootDir: repo,
    publicDir: path.join(repo, 'out/leaf-truck/public'), outDir: path.join(repo, 'out/leaf-truck/build/bundle')});
  const browser = await openBrowser('chrome', {browserExecutable: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
  try {
    const composition = await selectComposition({serveUrl, id: 'LeafTruck', inputProps, puppeteerInstance: browser});
    if (frame !== undefined) {
      for (const f of frame.split(',')) {
        await renderStill({composition, serveUrl, inputProps, puppeteerInstance: browser, frame: Number(f), scale: Number(scale),
          imageFormat: 'jpeg', jpegQuality: 88, output: out.replace('.jpg', `-${f}.jpg`)});
      }
      return;
    }
    let last = -1;
    await renderMedia({composition, serveUrl, inputProps, puppeteerInstance: browser, outputLocation: out + '.part.mp4',
      codec: 'h264', muted: true, scale: Number(scale), crf: 18, x264Preset: 'veryfast', imageFormat: 'jpeg', jpegQuality: 90,
      concurrency: 6, onProgress: ({progress}) => { const p = Math.floor(progress * 10) * 10; if (p > last) { last = p; console.log('picture', p + '%'); } }});
    fs.renameSync(out + '.part.mp4', out);
    console.log(out);
  } finally {
    await browser.close({silent: true});
  }
}
main().catch(e => { console.error(e); process.exitCode = 1; });
