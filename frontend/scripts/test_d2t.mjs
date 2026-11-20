import puppeteer from 'puppeteer-core';

async function testD2T() {
  const b = await puppeteer.launch({
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    headless: 'new'
  });
  const page = await b.newPage();
  await page.setViewport({ width: 1920, height: 1080 });
  await page.goto('http://localhost:5173/#dashboard');
  await new Promise(r => setTimeout(r, 1000));

  console.log('Initial hash:', await page.evaluate(() => window.location.hash));

  // Click Text Guard
  await page.click('button[data-nav-desktop="textguard"]');
  console.log('Clicked Text Guard');

  for (let t = 100; t <= 1500; t += 100) {
    await new Promise(r => setTimeout(r, 100));
    const status = await page.evaluate(() => {
      const shards = Array.from(document.querySelectorAll('div')).filter(
        d => d.style && (d.style.clipPath || d.getAttribute('style')?.includes('clip-path'))
      );
      const overlay = document.querySelector('div[style*="perspective"]');
      return {
        shards: shards.length,
        hasOverlay: !!overlay,
        hash: window.location.hash
      };
    });
    console.log(`t=${t}ms: shards=${status.shards}, overlay=${status.hasOverlay}, hash=${status.hash}`);
  }

  await b.close();
}

testD2T();
