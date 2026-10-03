/**
 * 三方对拍诊断：legacy innerHTML vs 后端结构化片段经 usePanelCalc 规则渲染后的 HTML。
 *
 * 用法：
 *   cd frontend && node tools/diff_breakdown.mjs <legacy_cases.json> <backend_resp.json> [场景]
 */
import { readFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { JSDOM } from 'jsdom';

const HERE = dirname(fileURLToPath(import.meta.url));
const LEGACY_ROOT = resolve(HERE, '../legacy');
const LEGACY_SCRIPTS = [
  'data/agent-presets.js',
  'data/weapon-presets.js',
  'scripts/calculator-config.js',
  'scripts/calculator.js',
];

/* ===== usePanelCalc.ts 的渲染规则（必须逐字照抄） ===== */

const escapeHtml = (value) =>
  value.replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);

const fmt = (n) => {
  const fixed = Number(n.toFixed(10));
  if (Math.abs(fixed - Math.round(fixed)) < 0.0000001) return Math.round(fixed).toLocaleString();
  return Number(fixed.toFixed(2)).toString();
};

const renderSources = (items) => {
  if (items.length === 0) return '无';
  return items
    .map((v) => `<span class="breakdown-item">${escapeHtml(v.replace(/ ([0-9])/g, '\u00a0$1'))}</span>`)
    .join(' + ');
};

const renderSegment = (seg) => {
  switch (seg.type) {
    case 'text':
      return escapeHtml(seg.text);
    case 'kw':
      return `<span class="kw">${escapeHtml(seg.text)}</span>`;
    case 'num': {
      const text = `${fmt(seg.value)}${seg.unit ?? ''}`;
      return seg.bold ? `<b>${text}</b>` : text;
    }
    case 'sources':
      return renderSources(seg.items);
    default:
      return '';
  }
};

const renderLine = (line) => {
  const inner = line.parts.map(renderSegment).join('');
  return line.wrapped ? `<span class="breakdown-line">${inner}</span>` : inner;
};

const renderBreakdown = (lines) => (lines ?? []).map(renderLine).join('');

/* ===== legacy 侧 ===== */

function createLegacyWindow() {
  const dom = new JSDOM(readFileSync(resolve(LEGACY_ROOT, 'pages/calculator.html'), 'utf8'), {
    runScripts: 'dangerously',
    url: 'http://localhost/legacy/pages/calculator.html',
  });
  const source = LEGACY_SCRIPTS.map((p) => readFileSync(resolve(LEGACY_ROOT, p), 'utf8')).join('\n;\n');
  const el = dom.window.document.createElement('script');
  el.textContent = source;
  dom.window.document.body.appendChild(el);
  return dom.window;
}

/* ===== 行标签 → 后端键 ===== */

const LABEL_TO_KEY = {
  '生命值': 'hp', '攻击力': 'atk', '防御力': 'def',
  '贯穿力': 'penforce', '暴击率': 'cr', '暴击伤害': 'cd',
  '实际暴击率': 'actual_cr', '锐暴伤害': 'blast_dmg', '增伤': 'dmg',
  '穿透率': 'pr', '穿透值': 'pv', '异常精通': 'am',
  '异常掌控': 'ac', '冲击力': 'imp', '能量回复': 'er', '锐能自动累积': 'er',
};

function legacyRows(win) {
  return [...win.document.querySelectorAll('.result .r-row')]
    .filter((r) => !r.hidden)
    .map((r) => ({
      label: r.querySelector('.r-label')?.textContent ?? '',
      value: r.querySelector('.r-value')?.textContent ?? '',
      breakdown: r.querySelector('.breakdown')?.innerHTML ?? '',
    }));
}

/* ===== 场景构建（与 dump_legacy_cases.mjs 的 case* 对应） ===== */

function buildLegacyScenario(win, name) {
  const doc = win.document;
  const ev = (t) => new win.Event(t, { bubbles: true });
  const recalc = () => doc.dispatchEvent(ev('input'));
  const setNum = (id, v) => { doc.getElementById(id).value = String(v); recalc(); };
  const byLabel = (id, label) => {
    const sel = doc.getElementById(id);
    const opt = [...sel.options].find((o) => o.textContent === label);
    if (!opt) throw new Error(`#${id} 无选项「${label}」`);
    sel.value = opt.value;
    sel.dispatchEvent(ev('change'));
  };

  if (name === 'full') {
    setNum('base_hp', 8000); setNum('base_atk', 1000); setNum('base_def', 600);
    setNum('base_impact', 90); setNum('base_cr', 5); setNum('base_cd', 50);
    setNum('base_ac', 100); setNum('base_am', 100); setNum('base_pr', 0); setNum('base_er', 1.2);
    byLabel('weapon_grade', 'S级'); byLabel('weapon_role', '强攻');
    const sel = doc.getElementById('weapon_preset');
    sel.value = sel.options[1].value;
    sel.dispatchEvent(ev('change'));
    byLabel('core1', '暴击率 +14.4%'); byLabel('core2', '暴击伤害 +28.8%');
    byLabel('disc4', '攻击力 30%'); byLabel('disc5', '增伤 30%'); byLabel('disc6', '冲击力 24%');
    setNum('sub_hp_flat', 12); setNum('sub_atk_pct', 7); setNum('sub_def_flat', 5);
    setNum('sub_cr', 9); setNum('sub_cd', 4); setNum('sub_pen_val', 6); setNum('sub_am', 11);
    byLabel('set0', '攻击力 +10%'); byLabel('set1', '暴击伤害 +16%'); byLabel('set2', '能量回复 +20%');
  } else if (name === 'ep-1299' || name === 'ep-2145') {
    const roleTag = name === 'ep-1299' ? '命破' : '锋御';
    byLabel('agent_role', roleTag);
    const sel = doc.getElementById('agent_preset');
    sel.value = name;
    sel.dispatchEvent(ev('change'));
  }
}

/* ===== 序列化对齐 ===== */

/**
 * legacy 侧的 innerHTML 来自 DOM 序列化，不换行空格会被写成 `&nbsp;`。
 * 我方是裸 HTML 字符串，直接比较会产生假阳性，必须同样过一遍 DOM。
 */
function serialize(html) {
  const div = new JSDOM('<!doctype html><body></body>').window.document.createElement('div');
  div.innerHTML = html;
  return div.innerHTML;
}

/* ===== 主流程 ===== */

const legacyPath = process.argv[2];
const backendPath = process.argv[3];
const only = process.argv[4];

const backend = JSON.parse(readFileSync(backendPath, 'utf8'));
const scenarios = ['empty', 'full', 'ep-1299', 'ep-2145'].filter((s) => !only || s === only);

let mismatchTotal = 0;

for (const name of scenarios) {
  const win = createLegacyWindow();
  buildLegacyScenario(win, name);
  const legacy = legacyRows(win);
  const resp = backend[name];

  console.log(`\n===== ${name} =====`);
  for (const row of legacy) {
    const key = LABEL_TO_KEY[row.label];
    const mine = serialize(renderBreakdown(resp.breakdown[key]));

    // 后端侧的数值文本
    let mineValue;
    if (key === 'penforce') mineValue = fmt(resp.modeStats.penforce);
    else if (key === 'actual_cr') mineValue = `${fmt(resp.modeStats.actual_cr)}%`;
    else if (key === 'blast_dmg') mineValue = resp.blastDmg === null ? '—' : `${fmt(resp.blastDmg)}%`;
    else mineValue = fmt(resp.totals[key]);

    const unit = ['cr', 'cd', 'dmg', 'pr'].includes(key) ? '%' : '';
    if (`${mineValue}${unit}` !== row.value) {
      mismatchTotal += 1;
      console.log(`  [值] ${row.label}: legacy=${row.value} 后端=${mineValue}${unit}`);
    }
    if (mine !== row.breakdown) {
      mismatchTotal += 1;
      console.log(`  [明细] ${row.label}:`);
      console.log(`    legacy: ${row.breakdown}`);
      console.log(`    后端  : ${mine}`);
    }
  }
}

console.log(`\n差异总数: ${mismatchTotal}`);