import puppeteer from 'puppeteer-core';

async function test() {
  const browser = await puppeteer.launch({
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    headless: 'new'
  });
  const page = await browser.newPage();
  await page.goto('http://localhost:5173');

  // Trigger navigation
  await page.click('nav button:nth-child(2)');
  await new Promise(r => setTimeout(r, 200));

  const info = await page.evaluate(() => {
    const allDivs = Array.from(document.querySelectorAll('div'));
    const shardDivs = allDivs.filter(d => d.style && (d.style.clipPath || d.getAttribute('style')?.includes('clip-path')));
    const overlay = document.querySelector('div[style*="perspective"]');
    return {
      hasOverlay: !!overlay,
      overlayHTML: overlay ? overlay.outerHTML.slice(0, 300) : null,
      shardCount: shardDivs.length,
      firstShardHTML: shardDivs[0] ? shardDivs[0].outerHTML.slice(0, 200) : null
    };
  });

  console.log('DOM Info during transition:', info);
  await browser.close();
}

test();
