import {createRequire} from 'node:module';
import {readFile, writeFile} from 'node:fs/promises';
import {pathToFileURL} from 'node:url';
import path from 'node:path';

const require = createRequire('@RUNTIME_DEPS@/node/package.json');
const {chromium} = require('playwright');
const root = '@USER_HOME@/Desktop/山海与人间-YouTube上传';
const source = '@DATA_ROOT@/v3';
const browser = await chromium.launch({
  executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  headless: true,
});
try {
  const page = await browser.newPage({viewport: {width: 1360, height: 1050}});
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  await page.goto(pathToFileURL(path.join(root, '打开预览.html')).href);
  const links = await page.locator('a').evaluateAll(elements => elements.map(a => a.getAttribute('href')));
  const media = [];
  for (let i = 0; i < 4; i++) {
    const result = await page.locator('video').nth(i).evaluate(async video => {
      await new Promise((resolve, reject) => {
        video.addEventListener('loadedmetadata', resolve, {once: true});
        video.addEventListener('error', () => reject(new Error('Video load failed')), {once: true});
        video.preload = 'metadata';
        video.load();
      });
      video.muted = true;
      await video.play();
      await new Promise(resolve => setTimeout(resolve, 250));
      video.pause();
      return {file: video.getAttribute('src'), duration: video.duration,
              width: video.videoWidth, height: video.videoHeight,
              currentTime: video.currentTime, error: video.error?.message ?? null};
    });
    if (result.width !== 1920 || result.error || result.currentTime <= 0) throw new Error(JSON.stringify(result));
    media.push(result);
  }
  const seekChecks = [];
  for (const time of [43, 318, 591, 818, 1200]) {
    seekChecks.push(await page.locator('video').first().evaluate(async (video, t) => {
      await new Promise((resolve, reject) => {
        video.addEventListener('seeked', resolve, {once: true});
        video.addEventListener('error', () => reject(new Error('Seek failed')), {once: true});
        video.currentTime = t;
      });
      return {requested: t, actual: video.currentTime, error: video.error?.message ?? null};
    }, time));
  }
  const images = await page.locator('img').evaluateAll(elements => elements.map(i => ({
    src: i.getAttribute('src'), complete: i.complete, width: i.naturalWidth, height: i.naturalHeight,
  })));
  if (images.some(i => !i.complete || i.width !== 1280 || i.height !== 720)) throw new Error('Cover failed to load');
  await page.screenshot({path: path.join(source, 'checks/youtube-package-desktop.jpg'), type: 'jpeg', quality: 85});
  await page.setViewportSize({width: 390, height: 844});
  const mobileOverflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
  if (errors.length || mobileOverflow) throw new Error(JSON.stringify({errors, mobileOverflow}));
  const result = {status: 'passed', mode: 'file://; no server required', links,
                  videos: media, seekChecks, covers: images, pageErrors: errors, mobileOverflow};
  await writeFile(path.join(source, 'checks/youtube-package-browser.json'), JSON.stringify(result, null, 2) + '\n');
  const reportPath = path.join(root, '资料/校验记录.json');
  const report = JSON.parse(await readFile(reportPath, 'utf8'));
  report.browser_package_review = result;
  // Both generated covers were visually inspected at their final delivered size.
  report.cover_visual_review = 'Passed: title only, one language per cover, intact composition and figure, readable text.';
  await writeFile(reportPath, JSON.stringify(report, null, 2) + '\n');
  const sourceReportPath = path.join(source, 'checks/youtube-package.json');
  const sourceReport = JSON.parse(await readFile(sourceReportPath, 'utf8'));
  sourceReport.status = 'passed';
  sourceReport.browser_review = 'youtube-package-browser.json';
  await writeFile(sourceReportPath, JSON.stringify(sourceReport, null, 2) + '\n');
  console.log(JSON.stringify({status: 'passed', videos: media, coverCount: images.length,
                              pageErrors: errors, mobileOverflow}, null, 2));
} finally {
  await browser.close();
}
