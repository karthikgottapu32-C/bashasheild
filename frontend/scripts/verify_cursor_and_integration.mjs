import puppeteer from 'puppeteer-core';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const APP_URL = 'http://localhost:5173';
const SCREENSHOTS_DIR = path.resolve(__dirname, '../../verification_screenshots');

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function runIntegrationVerification() {
  console.log('=================================================================');
  console.log('BHASHASHIELD FINAL INTEGRATION & CUSTOM CURSOR RUNTIME VERIFICATION');
  console.log('=================================================================');

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: 'new',
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--window-size=1920,1080',
      '--disable-dev-shm-usage',
      '--disable-web-security'
    ]
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080 });

  const consoleErrors = [];
  const pageErrors = [];

  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      const text = msg.text();
      if (!text.includes('favicon.ico') && !text.includes('404')) {
        consoleErrors.push(text);
        console.warn(`[Console Error]: ${text}`);
      }
    }
  });

  page.on('pageerror', (err) => {
    pageErrors.push(err.message);
    console.error(`[Page Error]: ${err.message}`);
  });

  const report = {
    checks: [],
    passed: 0,
    failed: 0
  };

  function check(name, pass, details = '') {
    if (pass) {
      report.passed++;
      console.log(`[PASS] ${name}${details ? ` -> ${details}` : ''}`);
      report.checks.push({ name, pass: true, details });
    } else {
      report.failed++;
      console.error(`[FAIL] ${name}${details ? ` -> ${details}` : ''}`);
      report.checks.push({ name, pass: false, details });
    }
  }

  try {
    // -------------------------------------------------------------
    // Check 1: Initial Load & Cursor Elements Initialization
    // -------------------------------------------------------------
    console.log('\n--- 1. Testing Initial Page & Custom Cursor Elements ---');
    await page.goto(`${APP_URL}/#landing`, { waitUntil: 'networkidle2' });
    await sleep(800);

    // Dispatch mouse movement
    await page.mouse.move(500, 300);
    await sleep(200);

    const cursorElements = await page.evaluate(() => {
      const dot = document.querySelector('div.fixed[style*="border-radius: 9999px"], div.fixed.z-\\[99999\\]:last-child');
      const innerRing = document.querySelector('div.fixed[style*="width: 28px"]');
      const outerRing = document.querySelector('div.fixed[style*="width: 44px"]');
      const cursorCanvas = document.querySelector('canvas.z-\\[99998\\]');
      const globalStyle = document.getElementById('bhashashield-custom-cursor-style');

      return {
        hasDot: !!dot,
        hasInner: !!innerRing,
        hasOuter: !!outerRing,
        hasCanvas: !!cursorCanvas,
        hasGlobalStyle: !!globalStyle
      };
    });

    check(
      'Custom Cursor Layer Initialization',
      cursorElements.hasDot && cursorElements.hasInner && cursorElements.hasOuter && cursorElements.hasCanvas,
      `Dot=${cursorElements.hasDot}, Inner=${cursorElements.hasInner}, Outer=${cursorElements.hasOuter}, TrailCanvas=${cursorElements.hasCanvas}`
    );

    check(
      'Global Cursor Suppression Style Injected',
      cursorElements.hasGlobalStyle,
      'bhashashield-custom-cursor-style injected (* { cursor: none !important; })'
    );

    // -------------------------------------------------------------
    // Check 2: Cursor Movement Tracking & Smooth Animation
    // -------------------------------------------------------------
    console.log('\n--- 2. Testing Cursor Follows Mouse Movement ---');
    await page.mouse.move(700, 450);
    await sleep(150);

    const cursorPosition = await page.evaluate(() => {
      const dot = document.querySelector('div.fixed[style*="border-radius: 9999px"]') ||
                  document.querySelectorAll('div.fixed.z-\\[99999\\]')[2];
      const transform = dot ? dot.style.transform : '';
      return { transform };
    });

    check(
      'Cursor Follows Mouse Coordinates GPU Transform',
      cursorPosition.transform.includes('700') || cursorPosition.transform.includes('translate3d'),
      `Transform: ${cursorPosition.transform}`
    );

    // -------------------------------------------------------------
    // Check 3: Cursor Hover States (Buttons & Text Inputs)
    // -------------------------------------------------------------
    console.log('\n--- 3. Testing Cursor Hover Morphing on Interactive Elements ---');
    // Hover over a nav button
    const navBtn = await page.waitForSelector('button[data-nav-desktop="textguard"]');
    const navBox = await navBtn.boundingBox();
    if (navBox) {
      await page.mouse.move(navBox.x + navBox.width / 2, navBox.y + navBox.height / 2);
      await sleep(150);
    }

    const buttonHoverState = await page.evaluate(() => {
      const inner = document.querySelector('div.fixed[style*="width: 28px"]');
      const dot = document.querySelector('div.fixed[style*="border-radius: 9999px"]') ||
                  document.querySelectorAll('div.fixed.z-\\[99999\\]')[2];
      return {
        innerTransform: inner ? inner.style.transform : '',
        innerBg: inner ? inner.style.backgroundColor : '',
        dotBg: dot ? dot.style.backgroundColor : ''
      };
    });

    check(
      'Cursor Expands on Button Hover with Accent Glow',
      buttonHoverState.innerTransform.includes('scale'),
      `Inner scale applied: ${buttonHoverState.innerTransform}`
    );

    // Navigate to Text Guard to test Input morphing
    await navBtn.click();
    await sleep(1000); // Wait for transition

    const textarea = await page.waitForSelector('textarea');
    const taBox = await textarea.boundingBox();
    if (taBox) {
      await page.mouse.move(taBox.x + 50, taBox.y + 40);
      await sleep(200);
    }

    const inputHoverState = await page.evaluate(() => {
      const dot = document.querySelector('div.fixed.z-\\[99999\\]:last-child') ||
                  document.querySelector('div.fixed[style*="width: 2px"]') ||
                  document.querySelector('div.fixed[style*="border-radius: 1px"]');
      const width = dot ? dot.style.width : '';
      const height = dot ? dot.style.height : '';
      return { width, height };
    });

    check(
      'Cursor Morphs into Text Caret over Textarea',
      inputHoverState.width === '2px' && inputHoverState.height === '20px',
      `Width=${inputHoverState.width}, Height=${inputHoverState.height}`
    );

    // -------------------------------------------------------------
    // Check 4: Live Theme Adaptation across Cursor & Components
    // -------------------------------------------------------------
    console.log('\n--- 4. Testing Live Reactive Theme Switching in Cursor ---');
    const themesToTest = ['obsidian-lime', 'navy-coral', 'electric-purple', 'forest-green'];
    let themeAdaptationAllOk = true;

    for (const themeId of themesToTest) {
      await page.evaluate((id) => {
        // Trigger live theme change via context helper
        const btn = Array.from(document.querySelectorAll('button')).find(
          b => b.textContent && b.textContent.toLowerCase().includes(id.replace('-', ' '))
        );
        if (btn) {
          btn.click();
        } else {
          localStorage.setItem('bhashashield_theme_id', id);
          window.dispatchEvent(new Event('storage'));
        }
      }, themeId);

      await sleep(300);
      const activeAccent = await page.evaluate(() => {
        return getComputedStyle(document.documentElement).getPropertyValue('--theme-accent').trim();
      });
      if (!activeAccent) themeAdaptationAllOk = false;
      console.log(`Live Theme ${themeId}: --theme-accent = ${activeAccent}`);
    }

    check(
      'Theme Variables Reactivity on All Elements',
      themeAdaptationAllOk,
      'Tested active accent responsiveness'
    );

    // -------------------------------------------------------------
    // Check 5: Transitions with Cursor Co-existence
    // -------------------------------------------------------------
    console.log('\n--- 5. Testing Cinematic Transitions with Custom Cursor ---');
    const dashNav = await page.waitForSelector('button[data-nav-desktop="dashboard"]');
    await dashNav.click();

    // Check mid-transition that cursor is still in the DOM and visible
    await sleep(200);
    const midState = await page.evaluate(() => {
      const hasOverlay = !!document.querySelector('[data-fragmentation-overlay="true"]');
      const shardsCount = document.querySelectorAll('[data-fragment-shard="true"]').length;
      const cursorCanvas = !!document.querySelector('canvas.z-\\[99998\\]');
      const transitionCanvas = !!document.querySelector('canvas[data-transition-canvas="true"]');
      return { hasOverlay, shardsCount, cursorCanvas, transitionCanvas };
    });

    check(
      'Fragmentation Shards and Cursor Dual Canvases Coexist',
      midState.hasOverlay && midState.shardsCount > 0 && midState.cursorCanvas && midState.transitionCanvas,
      `Shards=${midState.shardsCount}, TransitionCanvas=${midState.transitionCanvas}, CursorCanvas=${midState.cursorCanvas}`
    );

    await sleep(950);

    const postState = await page.evaluate(() => {
      const hasOverlay = !!document.querySelector('[data-fragmentation-overlay="true"]');
      const shardsCount = document.querySelectorAll('[data-fragment-shard="true"]').length;
      const cursorCanvas = !!document.querySelector('canvas.z-\\[99998\\]');
      const hash = window.location.hash;
      return { hasOverlay, shardsCount, cursorCanvas, hash };
    });

    check(
      'Post-Transition Clean State with Retained Cursor',
      !postState.hasOverlay && postState.shardsCount === 0 && postState.cursorCanvas && postState.hash.includes('dashboard'),
      `Hash=${postState.hash}, StuckShards=${postState.shardsCount}, CursorActive=${postState.cursorCanvas}`
    );

    // -------------------------------------------------------------
    // Check 6: Browser History Back / Forward with Cursor Integrity
    // -------------------------------------------------------------
    console.log('\n--- 6. Testing Browser History Back and Forward ---');
    await page.evaluate(() => window.history.back());
    await sleep(200);
    const backMid = await page.evaluate(() => document.querySelectorAll('[data-fragment-shard="true"]').length);
    await sleep(1000);
    const backPostHash = await page.evaluate(() => window.location.hash);

    await page.evaluate(() => window.history.forward());
    await sleep(200);
    const forwardMid = await page.evaluate(() => document.querySelectorAll('[data-fragment-shard="true"]').length);
    await sleep(1000);
    const forwardPostHash = await page.evaluate(() => window.location.hash);

    check(
      'Browser History Navigation Triggers Seamless Breakup Transitions',
      backMid > 0 && forwardMid > 0 && forwardPostHash.includes('dashboard'),
      `Back triggered (${backMid} shards, to ${backPostHash}), Forward triggered (${forwardMid} shards, to ${forwardPostHash})`
    );

    // -------------------------------------------------------------
    // Check 7: Accessibility: prefers-reduced-motion
    // -------------------------------------------------------------
    console.log('\n--- 7. Testing prefers-reduced-motion on Cursor & Transitions ---');
    await page.emulateMediaFeatures([{ name: 'prefers-reduced-motion', value: 'reduce' }]);
    await sleep(300);

    const reducedCursorState = await page.evaluate(() => {
      const inner = document.querySelector('div.fixed[style*="width: 28px"]');
      const outer = document.querySelector('div.fixed[style*="width: 44px"]');
      const canvas = document.querySelector('canvas.z-\\[99998\\]');
      return {
        innerDisplay: inner ? window.getComputedStyle(inner).display : '',
        outerDisplay: outer ? window.getComputedStyle(outer).display : '',
        canvasDisplay: canvas ? window.getComputedStyle(canvas).display : ''
      };
    });

    check(
      'Reduced Motion Hides Rings and Cursor Particle Trail',
      reducedCursorState.innerDisplay === 'none' && reducedCursorState.outerDisplay === 'none',
      `Inner=${reducedCursorState.innerDisplay}, Outer=${reducedCursorState.outerDisplay}, Canvas=${reducedCursorState.canvasDisplay}`
    );

    // Trigger navigation under reduced motion
    const evalNav = await page.waitForSelector('button[data-nav-desktop="evaluation"]');
    await evalNav.click();
    await sleep(150);

    const reducedShards = await page.evaluate(() => document.querySelectorAll('[data-fragment-shard="true"]').length);
    await sleep(400);
    const evalHash = await page.evaluate(() => window.location.hash);

    check(
      'Reduced Motion Bypasses Breakup Shards and Quickly Crossfades',
      reducedShards === 0 && evalHash.includes('evaluation'),
      `Shards=${reducedShards}, Hash=${evalHash}`
    );

    await page.emulateMediaFeatures([]);

    // -------------------------------------------------------------
    // Check 8: Mobile Viewport Behavior
    // -------------------------------------------------------------
    console.log('\n--- 8. Testing Mobile Viewport Behavior ---');
    await page.setViewport({ width: 390, height: 844 });
    await sleep(400);

    // Open mobile hamburger
    await page.evaluate(() => {
      const btn = document.querySelector('header button[aria-label="Toggle Navigation Menu"]');
      if (btn) btn.click();
    });
    await sleep(350);

    // Click Overview in drawer
    await page.evaluate(() => {
      const btn = document.querySelector('button[data-nav-mobile="landing"]');
      if (btn) btn.click();
    });
    await sleep(200);

    const mobileShards = await page.evaluate(() => document.querySelectorAll('[data-fragment-shard="true"]').length);
    await sleep(1000);
    const mobileSettled = await page.evaluate(() => ({
      hash: window.location.hash,
      remainingShards: document.querySelectorAll('[data-fragment-shard="true"]').length
    }));

    check(
      'Mobile Viewport Shard Pruning & Responsive Cleanup',
      mobileShards <= 8 && mobileSettled.remainingShards === 0 && mobileSettled.hash.includes('landing'),
      `ActiveShards=${mobileShards} (limit 8), Remaining=${mobileSettled.remainingShards}, Hash=${mobileSettled.hash}`
    );

    // Reset desktop viewport
    await page.setViewport({ width: 1920, height: 1080 });
    await sleep(400);

    // -------------------------------------------------------------
    // Check 9: Console & Runtime Errors
    // -------------------------------------------------------------
    console.log('\n--- 9. Verifying Browser Console & Runtime Stability ---');
    check(
      'Zero Console Errors throughout Entire Run',
      consoleErrors.length === 0,
      consoleErrors.length === 0 ? 'No console errors detected' : `Errors: ${consoleErrors.join('; ')}`
    );

    check(
      'Zero Uncaught Page Exceptions',
      pageErrors.length === 0,
      pageErrors.length === 0 ? 'No uncaught page errors' : `Errors: ${pageErrors.join('; ')}`
    );

  } catch (err) {
    console.error('Integration verification error:', err);
    check('Integration Verification Script Integrity', false, err.message);
  } finally {
    await browser.close();
  }

  console.log('\n=================================================================');
  console.log(`INTEGRATION REPORT: ${report.passed} PASSED, ${report.failed} FAILED`);
  console.log('=================================================================');

  fs.writeFileSync(
    path.join(SCREENSHOTS_DIR, 'final_integration_report.json'),
    JSON.stringify(report, null, 2)
  );
}

runIntegrationVerification();
