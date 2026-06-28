const { chromium } = require("playwright");

async function waitAndLog(page, label, ms = 3000) {
  await page.waitForTimeout(ms);
  const t = await page.locator("body").innerText();
  console.log(`\n[${label}]\n${t.slice(0, 500)}\n`);
  await page.screenshot({ path: `/tmp/${label.replace(/ /g, "_")}.png` });
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.setViewportSize({ width: 1280, height: 1000 });

  // ── Step 1: 提交题目 ──
  console.log("=== Step 1: 提交题目 ===");
  await page.goto("http://localhost:5173/");
  await page.waitForSelector("textarea");
  await page.fill("textarea", "Prove that sqrt(2) is irrational.");
  await page.click('button:has-text("Submit")');
  await waitAndLog(page, "1_submitted", 2500);

  // ── Step 2: G2 审批 ──
  console.log("=== Step 2: G2 审批 (Approve) ===");
  await page.waitForSelector('button:has-text("Approve")', { timeout: 10000 });
  await page.click('button:has-text("Approve")');
  await waitAndLog(page, "2_approved", 3000);

  // ── Step 3: 等待 SOLVE 表单 ──
  console.log("=== Step 3: 等待 SOLVE 表单 ===");
  // SOLVE form has inputs with placeholder "Expression" and "Reason"
  await page.waitForSelector('input[placeholder*="Expression"]', {
    timeout: 15000,
  });
  console.log("SOLVE 表单已出现");

  // Fill Step 1
  await page.fill(
    'input[placeholder*="Expression"]',
    "sqrt(2) = p/q (lowest terms) → p^2 = 2q^2 → p even → p=2k → q^2=2k^2 → q even → contradiction",
  );
  await page.fill(
    'input[placeholder*="Reason"]',
    "Proof by contradiction: if rational in lowest terms, both p and q must be even, contradicting lowest terms",
  );
  // Fill Final Result
  await page.fill(
    'input[placeholder*="Final Result"]',
    "sqrt(2) is irrational",
  );
  // Fill Intuition (textarea)
  await page.fill(
    'textarea[placeholder*="Intuition"]',
    "Assuming rational leads to infinite descent; the key insight is that evenness propagates through squaring",
  );

  await page.screenshot({ path: "/tmp/3_solve_filled.png" });
  console.log("SOLVE 已填写，提交...");
  await page.click('button:has-text("提交 SOLVE")');
  await waitAndLog(page, "4_after_solve", 3000);

  // ── Step 4: 等待 VERIFY 表单 ──
  console.log("=== Step 4: 等待 VERIFY 表单 ===");
  await page.waitForSelector('input[placeholder*="Method"]', {
    timeout: 15000,
  });
  console.log("VERIFY 表单已出现");

  await page.fill('input[placeholder*="Method"]', "Proof by contradiction");
  await page.fill(
    'input[placeholder*="Input"]',
    "Assume sqrt(2) = p/q in lowest terms",
  );
  await page.fill(
    'input[placeholder*="Expected"]',
    "Contradiction: p and q both even",
  );
  await page.fill(
    'input[placeholder*="Actual"]',
    "Contradiction confirmed: both p and q are even",
  );
  // "验证通过" checkbox is checked by default

  await page.screenshot({ path: "/tmp/5_verify_filled.png" });
  console.log("VERIFY 已填写，提交...");
  await page.click('button:has-text("提交 VERIFY")');
  await waitAndLog(page, "6_final", 4000);

  // ── 检查最终状态 ──
  const body = await page.locator("body").innerText();
  const isDone = /DONE|done|完成/.test(body);
  console.log("=== 最终状态 ===");
  console.log("包含 DONE?", isDone);
  console.log(body.slice(0, 800));

  // 截图
  await page.screenshot({ path: "/tmp/7_done.png", fullPage: true });
  console.log("\n截图保存: /tmp/7_done.png");

  await browser.close();
})().catch((e) => {
  console.error("ERROR:", e.message);
  process.exit(1);
});
