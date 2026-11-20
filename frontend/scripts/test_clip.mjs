import puppeteer from 'puppeteer-core';

async function check() {
  const b = await puppeteer.launch({
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    headless: 'new'
  });
  const page = await b.newPage();
  await page.goto('http://localhost:5173/#textguard');
  await new Promise(r => setTimeout(r, 2000));

  const res = await page.evaluate(() => {
    const all = Array.from(document.querySelectorAll('*')).filter(el =>
      el.style && (el.style.clipPath || el.getAttribute('style')?.includes('clip-path'))
    );
    return all.map(el => ({
      tag: el.tagName,
      className: el.className,
      style: el.getAttribute('style')?.slice(0, 100)
    }));
  });

  console.log('Total elements with clip-path on Text Guard after 2s:', res.length);
  if (res.length > 0) {
    console.log('Sample elements:', res.slice(0, 3));
  }
  await b.close();
}

check();
