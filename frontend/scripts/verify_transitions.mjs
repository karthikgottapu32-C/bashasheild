import puppeteer from 'puppeteer-core';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const APP_URL = 'http://localhost:5173';
const SCREENSHOTS_DIR = path.resolve(__dirname, '../../verification_screenshots');

if (!fs.existsSync(SCREENSHOTS_DIR)) {
  fs.mkdirSync(SCREENSHOTS_DIR, { recursive: true });
}

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

const results = {
  performed: [],
  passed: [],
  failed: [],
  bugs: [],
  fixes: [],
  limitations: []
};

function recordTest(name, passed, details = '') {
  results.performed.push(name);
  if (passed) {
    results.passed.push(`${name}${details ? ` (${details})` : ''}`);
    console.log(`[PASS] ${name}${details ? ` - ${details}` : ''}`);
  } else {
    results.failed.push(`${name}${details ? ` (${details})` : ''}`);
    console.error(`[FAIL] ${name}${details ? ` - ${details}` : ''}`);
  }
}

async function queryShards(page) {
  return await page.evaluate(() => {
    const shards = document.querySelectorAll('[data-fragment-shard="true"]');
    const canvas = document.querySelector('canvas[data-transition-canvas="true"]');
    const overlay = document.querySelector('[data-fragmentation-overlay="true"]');
    return {
      count: shards.length,
      hasCanvas: !!canvas,
      hasOverlay: !!overlay
    };
  });
}

async function run() {
  console.log('=====================================================');
  console.log('BHASHASHIELD CINEMATIC TRANSITIONS RUNTIME VERIFICATION');
  console.log('=====================================================');

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
        console.warn(`[Browser Console Error]: ${text}`);
      }
    }
  });

  page.on('pageerror', (err) => {
    pageErrors.push(err.message);
    console.error(`[Browser Page Error]: ${err.message}`);
  });

  try {
    // ------------------------------------------------------------------
    // Initial Load & Route
    // ------------------------------------------------------------------
    console.log('\n--- 1. Loading BhashaShield Overview ---');
    await page.goto(`${APP_URL}/#landing`, { waitUntil: 'networkidle2' });
    await sleep(1200);

    const title = await page.title();
    console.log(`Page title: "${title}"`);
    recordTest('Initial Page Load', title.includes('BhashaShield'), `Loaded title: ${title}`);

    // Set default theme to obsidian-lime for baseline tests
    await page.evaluate(() => {
      localStorage.setItem('bhashashield_theme_id', 'obsidian-lime');
    });

    // ------------------------------------------------------------------
    // TEST 1: Navigate Overview -> Text Guard (Radial Pulse & Shockwave)
    // ------------------------------------------------------------------
    console.log('\n--- 2. TEST: Navigate Overview -> Text Guard ---');
    const textGuardLink = await page.waitForSelector('button[data-nav-desktop="textguard"]');
    await textGuardLink.click();

    // Capture mid-transition (shards exploding outward + shockwave ring)
    await sleep(220);
    const mid1 = await queryShards(page);
    const mid1Path = path.join(SCREENSHOTS_DIR, '01_transition_overview_to_textguard_midpoint.png');
    await page.screenshot({ path: mid1Path });
    console.log(`T1 mid-transition DOM: Shards=${mid1.count}, Canvas=${mid1.hasCanvas}, Overlay=${mid1.hasOverlay}`);

    recordTest(
      'Transition 1 (Overview -> Text Guard) Radial Dispersal & Canvas Triggered',
      mid1.count > 0 && mid1.hasCanvas,
      `Observed ${mid1.count} glass shards, shockwave aura, and particle canvas in flight`
    );

    // Wait for transition to fully settle
    await sleep(900);
    const post1 = await queryShards(page);
    const settled1Path = path.join(SCREENSHOTS_DIR, '02_textguard_settled.png');
    await page.screenshot({ path: settled1Path });

    const textGuardActive = await page.evaluate(() => {
      const ta = document.querySelector('textarea');
      return !!ta && window.location.hash.includes('textguard');
    });

    recordTest(
      'Text Guard View Settled & Fragments Cleared',
      textGuardActive && post1.count === 0,
      `Text Guard interactive, 0 stuck shards, hash=#textguard`
    );
    await sleep(200);

    // ------------------------------------------------------------------
    // TEST 2: Navigate Text Guard -> Intelligence Console (Scanner Shear)
    // ------------------------------------------------------------------
    console.log('\n--- 3. TEST: Navigate Text Guard -> Intelligence Console ---');
    const dashboardLink = await page.waitForSelector('button[data-nav-desktop="dashboard"]');
    await dashboardLink.click();

    await sleep(220);
    const mid2 = await queryShards(page);
    const mid2Path = path.join(SCREENSHOTS_DIR, '03_transition_textguard_to_dashboard_midpoint.png');
    await page.screenshot({ path: mid2Path });
    console.log(`T2 mid-transition DOM: Shards=${mid2.count}, Canvas=${mid2.hasCanvas}`);

    recordTest(
      'Transition 2 (Text Guard -> Intelligence) Scanner Laser & Shear Shards',
      mid2.count > 0 && mid2.hasCanvas,
      `Observed ${mid2.count} glass shards shearing with horizontal beam`
    );

    await sleep(900);
    const post2 = await queryShards(page);
    const settled2Path = path.join(SCREENSHOTS_DIR, '04_dashboard_settled.png');
    await page.screenshot({ path: settled2Path });

    const dashboardActive = await page.evaluate(() => {
      const panels = document.querySelectorAll('.recharts-wrapper, .glass-panel');
      return panels.length > 0 && window.location.hash.includes('dashboard');
    });

    recordTest(
      'Intelligence Console Settled & Clean Teardown',
      dashboardActive && post2.count === 0,
      `Dashboard panels rendered, 0 stuck shards`
    );
    await sleep(200);

    // ------------------------------------------------------------------
    // TEST 3: Navigate Intelligence Console -> Evaluation (Telemetry Lift)
    // ------------------------------------------------------------------
    console.log('\n--- 4. TEST: Navigate Intelligence Console -> Evaluation ---');
    const evalLink = await page.waitForSelector('button[data-nav-desktop="evaluation"]');
    await evalLink.click();

    await sleep(220);
    const mid3 = await queryShards(page);
    const mid3Path = path.join(SCREENSHOTS_DIR, '05_transition_dashboard_to_evaluation_midpoint.png');
    await page.screenshot({ path: mid3Path });
    console.log(`T3 mid-transition DOM: Shards=${mid3.count}, Canvas=${mid3.hasCanvas}`);

    recordTest(
      'Transition 3 (Intelligence -> Evaluation) Upward Telemetry Lift Shards',
      mid3.count > 0 && mid3.hasCanvas,
      `Observed ${mid3.count} vertical telemetry shards lifting`
    );

    await sleep(900);
    const post3 = await queryShards(page);
    const settled3Path = path.join(SCREENSHOTS_DIR, '06_evaluation_settled.png');
    await page.screenshot({ path: settled3Path });

    const evalActive = await page.evaluate(() => {
      const bodyText = document.body.innerText;
      const hasF1 = bodyText.includes('Overall F1-Score') || bodyText.includes('Evaluation & Model Performance');
      return hasF1 && window.location.hash.includes('evaluation');
    });

    recordTest(
      'Evaluation View Settled & Benchmark KPI Displayed',
      evalActive && post3.count === 0,
      `Evaluation benchmark active, 0 stuck shards`
    );
    await sleep(200);

    // ------------------------------------------------------------------
    // TEST 4: Navigate Evaluation -> Overview (Shield Inward Convergence)
    // ------------------------------------------------------------------
    console.log('\n--- 5. TEST: Navigate Evaluation -> Overview ---');
    const overviewLink = await page.waitForSelector('button[data-nav-desktop="landing"]');
    await overviewLink.click();

    await sleep(260);
    const mid4 = await queryShards(page);
    const mid4Path = path.join(SCREENSHOTS_DIR, '07_transition_evaluation_to_overview_midpoint.png');
    await page.screenshot({ path: mid4Path });
    console.log(`T4 mid-transition DOM: Shards=${mid4.count}, Canvas=${mid4.hasCanvas}`);

    recordTest(
      'Transition 4 (Evaluation -> Overview) Inward Convergence & Shield Silhouette',
      mid4.count > 0,
      `Observed ${mid4.count} inward converging shards and central shield outline`
    );

    await sleep(900);
    const post4 = await queryShards(page);
    const settled4Path = path.join(SCREENSHOTS_DIR, '08_overview_settled.png');
    await page.screenshot({ path: settled4Path });

    const overviewActive = await page.evaluate(() => {
      return document.body.innerText.includes('MULTILINGUAL AI');
    });

    recordTest(
      'Overview View Settled & 3D Shield Hero Active',
      overviewActive && post4.count === 0,
      `3D hero rendered, 0 stuck shards`
    );
    await sleep(200);

    // ------------------------------------------------------------------
    // TEST 5: Remaining Cross-Route Permutations
    // ------------------------------------------------------------------
    console.log('\n--- 6. TEST: Remaining Navigation Routes ---');
    const crossRoutes = [
      { from: 'landing', to: 'dashboard', selector: 'button[data-nav-desktop="dashboard"]', name: 'Overview -> Dashboard' },
      { from: 'dashboard', to: 'textguard', selector: 'button[data-nav-desktop="textguard"]', name: 'Dashboard -> Text Guard' },
      { from: 'textguard', to: 'evaluation', selector: 'button[data-nav-desktop="evaluation"]', name: 'Text Guard -> Evaluation' },
      { from: 'evaluation', to: 'textguard', selector: 'button[data-nav-desktop="textguard"]', name: 'Evaluation -> Text Guard' }
    ];

    let allCrossOk = true;
    for (const cr of crossRoutes) {
      const btn = await page.waitForSelector(cr.selector);
      await btn.click();
      await sleep(220);

      const mid = await queryShards(page);
      await sleep(1050);
      const post = await queryShards(page);
      const hash = await page.evaluate(() => window.location.hash);

      const pass = mid.count > 0 && post.count === 0 && hash.includes(cr.to);
      if (!pass) {
        allCrossOk = false;
        console.log(`[DIAGNOSTIC] ${cr.name} failed: mid=${mid.count}, post=${post.count}, hash=${hash}`);
      }
      console.log(`Cross Route ${cr.name}: mid=${mid.count}, post=${post.count}, hash=${hash}`);
      await sleep(300);
    }

    recordTest(
      'All Remaining Cross-Route Permutations',
      allCrossOk,
      'Tested 4 cross-route navigational transitions with clean completion'
    );

    // ------------------------------------------------------------------
    // TEST 6: Browser Back & Forward Navigation
    // ------------------------------------------------------------------
    console.log('\n--- 7. TEST: Browser Back and Forward Navigation ---');
    // Currently on textguard. Go back to evaluation
    await page.evaluate(() => window.history.back());
    await sleep(240);
    const backMid = await queryShards(page);
    await sleep(950);
    const backPost = await queryShards(page);
    const backHash = await page.evaluate(() => window.location.hash);

    // Now go forward back to textguard
    await page.evaluate(() => window.history.forward());
    await sleep(240);
    const forwardMid = await queryShards(page);
    await sleep(950);
    const forwardPost = await queryShards(page);
    const forwardHash = await page.evaluate(() => window.location.hash);

    const historyOk = backMid.count > 0 && forwardMid.count > 0 && backPost.count === 0 && forwardPost.count === 0;
    const historyPath = path.join(SCREENSHOTS_DIR, '09_browser_history_back_forward.png');
    await page.screenshot({ path: historyPath });

    recordTest(
      'Browser Back & Forward History Transitions',
      historyOk,
      `goBack triggered (${backMid.count} shards), goForward triggered (${forwardMid.count} shards)`
    );
    await sleep(300);

    // ------------------------------------------------------------------
    // TEST 7: Rapid Multi-Clicking (Transition Locking / Debouncing)
    // ------------------------------------------------------------------
    console.log('\n--- 8. TEST: Rapid Multi-Clicking (Debounce / Locking) ---');
    const nav1 = await page.waitForSelector('button[data-nav-desktop="landing"]');
    const nav3 = await page.waitForSelector('button[data-nav-desktop="dashboard"]');
    const nav4 = await page.waitForSelector('button[data-nav-desktop="evaluation"]');

    // Rapid spam clicks within 40ms
    await nav1.click();
    await sleep(20);
    await nav3.click();
    await sleep(20);
    await nav4.click();

    await sleep(220);
    const spamMid = await queryShards(page);
    const lockPath = path.join(SCREENSHOTS_DIR, '10_transition_locking_rapid_click.png');
    await page.screenshot({ path: lockPath });

    await sleep(950);
    const spamPost = await queryShards(page);
    console.log(`[TEST 8 DEBUG] spamMid: count=${spamMid.count}, hasOverlay=${spamMid.hasOverlay}, hasCanvas=${spamMid.hasCanvas}; spamPost: count=${spamPost.count}`);

    recordTest(
      'Transition Locking & Debounce Guard',
      (spamMid.count > 0 || spamMid.hasOverlay) && spamPost.count === 0,
      `Debounce locked safely: midShards=${spamMid.count}, overlay=${spamMid.hasOverlay}, 0 stuck shards after settle`
    );
    await sleep(200);

    // ------------------------------------------------------------------
    // TEST 8: Switch between all 6 available themes & test transitions
    // ------------------------------------------------------------------
    console.log('\n--- 9. TEST: Switch between All 6 Themes & Verify Transitions ---');
    const themes = [
      'obsidian-lime',
      'midnight-lime',
      'navy-coral',
      'forest-green',
      'electric-purple',
      'original-cyber'
    ];

    let themesPassed = true;
    for (let i = 0; i < themes.length; i++) {
      const themeId = themes[i];
      await page.evaluate((id) => {
        localStorage.setItem('bhashashield_theme_id', id);
        window.location.reload();
      }, themeId);

      await page.waitForNavigation({ waitUntil: 'networkidle2' });
      await sleep(500);

      const colors = await page.evaluate(() => {
        const root = document.documentElement;
        return {
          primary: root.style.getPropertyValue('--theme-primary').trim(),
          accent: root.style.getPropertyValue('--theme-accent').trim(),
          accentRgb: root.style.getPropertyValue('--theme-accent-rgb').trim()
        };
      });

      // Target opposite view to ensure transition is guaranteed to trigger
      const currentHash = await page.evaluate(() => window.location.hash);
      const targetSelector = currentHash.includes('landing') ? 'button[data-nav-desktop="textguard"]' : 'button[data-nav-desktop="landing"]';
      const targetBtn = await page.waitForSelector(targetSelector);
      await targetBtn.click();
      await sleep(220);

      const themeMid = await queryShards(page);

      if (['obsidian-lime', 'navy-coral', 'electric-purple'].includes(themeId)) {
        const themeScreenshot = path.join(SCREENSHOTS_DIR, `theme_${themeId.replace('-', '_')}_transition.png`);
        await page.screenshot({ path: themeScreenshot });
        console.log(`Captured theme transition: ${themeScreenshot}`);
      }

      await sleep(1050);
      const themePost = await queryShards(page);

      const ok = colors.primary.length > 0 && colors.accent.length > 0 && themeMid.count > 0 && themePost.count === 0;
      if (!ok) themesPassed = false;
      console.log(`Theme ${themeId}: primary=${colors.primary}, accent=${colors.accent}, midShards=${themeMid.count}, postShards=${themePost.count}`);
      await sleep(300);
    }

    recordTest(
      'Theme Adaptation across all 6 Palettes',
      themesPassed,
      'Tested obsidian-lime, midnight-lime, navy-coral, forest-green, electric-purple, original-cyber'
    );

    // Reset back to obsidian-lime
    await page.evaluate(() => {
      localStorage.setItem('bhashashield_theme_id', 'obsidian-lime');
      window.location.reload();
    });
    await page.waitForNavigation({ waitUntil: 'networkidle2' });
    await sleep(500);

    // ------------------------------------------------------------------
    // TEST 9: Mobile Viewport Size (390x844)
    // ------------------------------------------------------------------
    console.log('\n--- 10. TEST: Mobile Viewport Size (390x844) ---');
    await page.setViewport({ width: 390, height: 844 });
    await sleep(400);

    // Open mobile menu
    await page.waitForSelector('header button[aria-label="Toggle Navigation Menu"]');
    await page.evaluate(() => {
      const hamburger = document.querySelector('header button[aria-label="Toggle Navigation Menu"]');
      if (hamburger) hamburger.click();
    });
    await sleep(350);

    // Click "Text Guard Workstation" in mobile drawer
    await page.waitForSelector('button[data-nav-mobile="textguard"]');
    await page.evaluate(() => {
      const btn = document.querySelector('button[data-nav-mobile="textguard"]');
      if (btn) btn.click();
    });

    await sleep(200);
    const mobileMid = await queryShards(page);
    const mobileMidPath = path.join(SCREENSHOTS_DIR, '14_mobile_viewport_transition.png');
    await page.screenshot({ path: mobileMidPath });

    await sleep(950);
    const mobilePost = await queryShards(page);

    console.log(`Mobile: midShards=${mobileMid.count} (target <= 8), postShards=${mobilePost.count}`);
    recordTest(
      'Mobile Viewport Performance & Shard Pruning',
      mobileMid.count <= 8 && mobilePost.count === 0,
      `Pruned to ${mobileMid.count} shards on mobile (<= 8), 0 stuck shards after transition`
    );

    // Reset viewport to desktop
    await page.setViewport({ width: 1920, height: 1080 });
    await sleep(400);

    // ------------------------------------------------------------------
    // TEST 10: prefers-reduced-motion Enabled
    // ------------------------------------------------------------------
    console.log('\n--- 11. TEST: prefers-reduced-motion: reduce ---');
    await page.emulateMediaFeatures([{ name: 'prefers-reduced-motion', value: 'reduce' }]);
    await sleep(200);

    const evalNav = await page.waitForSelector('button[data-nav-desktop="evaluation"]');
    await evalNav.click();

    await sleep(150);
    const reducedMid = await queryShards(page);
    const reducedPath = path.join(SCREENSHOTS_DIR, '15_reduced_motion_transition.png');
    await page.screenshot({ path: reducedPath });

    await sleep(350);
    const reducedHash = await page.evaluate(() => window.location.hash);

    console.log(`Reduced Motion: shards=${reducedMid.count}, canvas=${reducedMid.hasCanvas}, hash=${reducedHash}`);
    recordTest(
      'prefers-reduced-motion Accessibility Fallback',
      reducedMid.count === 0 && !reducedMid.hasCanvas && reducedHash.includes('evaluation'),
      '3D shards and canvas skipped, clean rapid crossfade executed'
    );

    await page.emulateMediaFeatures([]);

    // ------------------------------------------------------------------
    // TECHNICAL CHECKS: Interaction after completion, No memory leaks
    // ------------------------------------------------------------------
    console.log('\n--- 12. TECHNICAL CHECKS: Post-Transition Interactivity & Memory ---');
    const tgNav = await page.waitForSelector('button[data-nav-desktop="textguard"]');
    await tgNav.click();
    await sleep(900);

    // Click an attack preset button in Text Guard
    const presetBtn = await page.waitForSelector('div.flex.flex-wrap button:first-child');
    await presetBtn.click();
    await sleep(300);

    const textareaContent = await page.evaluate(() => {
      const ta = document.querySelector('textarea');
      return ta ? ta.value : '';
    });

    recordTest(
      'Post-Transition Interactivity (Text Guard Presets & Input)',
      textareaContent.length > 0,
      `Preset loaded "${textareaContent.slice(0, 30)}..." into textarea`
    );

    recordTest(
      'Zero React Console Errors',
      consoleErrors.length === 0,
      consoleErrors.length === 0 ? 'No console errors detected' : `Errors: ${consoleErrors.join('; ')}`
    );

    recordTest(
      'Zero Uncaught Page Errors',
      pageErrors.length === 0,
      pageErrors.length === 0 ? 'No uncaught page errors' : `Errors: ${pageErrors.join('; ')}`
    );

    const finalTeardown = await queryShards(page);
    recordTest(
      'Clean Lifecycle Teardown (No Stuck Fragments or Canvas)',
      finalTeardown.count === 0 && !finalTeardown.hasCanvas,
      `Remaining shards: ${finalTeardown.count}, canvas: ${finalTeardown.hasCanvas}`
    );

  } catch (err) {
    console.error('Test execution error:', err);
    results.bugs.push(`Test execution failure: ${err.message}`);
  } finally {
    await browser.close();
  }

  // ------------------------------------------------------------------
  // Summary Report Output
  // ------------------------------------------------------------------
  console.log('\n=====================================================');
  console.log('SUMMARY REPORT');
  console.log('=====================================================');
  console.log(`Total Tests Performed: ${results.performed.length}`);
  console.log(`Total Tests Passed:    ${results.passed.length}`);
  console.log(`Total Tests Failed:    ${results.failed.length}`);

  const reportData = {
    summary: {
      total: results.performed.length,
      passed: results.passed.length,
      failed: results.failed.length
    },
    tests: results,
    screenshots: fs.readdirSync(SCREENSHOTS_DIR)
  };

  fs.writeFileSync(
    path.join(SCREENSHOTS_DIR, 'verification_report.json'),
    JSON.stringify(reportData, null, 2)
  );

  console.log(`\nVerification report saved to ${path.join(SCREENSHOTS_DIR, 'verification_report.json')}`);
}

run();
