/**
 * 从 legacy 页面导出抽样用例的数值，作为 backend/tests/test_panel.py 的夹具。
 * 用法：node tools/dump_legacy_cases.mjs > /tmp/legacy_cases.json
 */
import { readFileSync, writeFileSync } from 'node:fs';
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

function harness(win) {
  const doc = win.document;
  const ev = (t) => new win.Event(t, { bubbles: true });
  const recalc = () => doc.dispatchEvent(ev('input'));
  const setNum = (id, v) => {
    doc.getElementById(id).value = String(v);
    recalc();
  };
  const byLabel = (id, label) => {
    const sel = doc.getElementById(id);
    const opt = [...sel.options].find((o) => o.textContent === label);
    if (!opt) throw new Error(`#${id} 无选项「${label}」`);
    sel.value = opt.value;
    sel.dispatchEvent(ev('change'));
  };
  const rows = () =>
    [...doc.querySelectorAll('.result .r-row')]
      .filter((r) => !r.hidden)
      .map((r) => ({
        label: r.querySelector('.r-label')?.textContent ?? '',
        value: r.querySelector('.r-value')?.textContent ?? '',
        num: Number((r.querySelector('.r-value')?.textContent ?? '').replace(/[%,]/g, '')),
      }));
  const base = () => {
    const get = (id) => Number(doc.getElementById(id).value);
    return {
      hp: get('base_hp'),
      atk: get('base_atk'),
      def: get('base_def'),
      impact: get('base_impact'),
      cr: get('base_cr'),
      cd: get('base_cd'),
      ac: get('base_ac'),
      am: get('base_am'),
      pr: get('base_pr'),
      er: get('base_er'),
    };
  };
  const subStats = () => {
    const out = {};
    for (const el of doc.querySelectorAll('[id^="sub_"]')) {
      const v = Number(el.value);
      if (v) out[el.id.slice(4)] = v;
    }
    return out;
  };
  const discMain = () => {
    const out = {};
    for (const id of ['disc4', 'disc5', 'disc6']) {
      const sel = doc.getElementById(id);
      if (sel.selectedIndex > 0) out[id] = sel.options[sel.selectedIndex].textContent;
    }
    return out;
  };
  const sets = () => {
    const out = [];
    for (const id of ['set0', 'set1', 'set2']) {
      const sel = doc.getElementById(id);
      out.push(sel.selectedIndex > 0 ? sel.options[sel.selectedIndex].textContent : '');
    }
    return out;
  };
  const core = () => {
    const out = [];
    for (const id of ['core1', 'core2']) {
      const sel = doc.getElementById(id);
      out.push(sel.selectedIndex > 0 ? sel.options[sel.selectedIndex].textContent : '');
    }
    return out;
  };
  const weapon = () => {
    const sel = doc.getElementById('weapon_preset');
    if (sel.selectedIndex <= 0) return null;
    const opt = sel.options[sel.selectedIndex];
    return { text: opt.textContent, id: opt.value };
  };
  return { doc, ev, recalc, setNum, byLabel, rows, base, subStats, discMain, sets, core, weapon };
}

/* ===== 场景 ===== */

function caseEmpty(h) {
  return { name: 'empty', rows: h.rows() };
}

function caseFull(h) {
  h.setNum('base_hp', 8000);
  h.setNum('base_atk', 1000);
  h.setNum('base_def', 600);
  h.setNum('base_impact', 90);
  h.setNum('base_cr', 5);
  h.setNum('base_cd', 50);
  h.setNum('base_ac', 100);
  h.setNum('base_am', 100);
  h.setNum('base_pr', 0);
  h.setNum('base_er', 1.2);
  h.byLabel('weapon_grade', 'S级');
  h.byLabel('weapon_role', '强攻');
  const sel = h.doc.getElementById('weapon_preset');
  sel.value = sel.options[1].value;
  sel.dispatchEvent(h.ev('change'));
  h.byLabel('core1', '暴击率 +14.4%');
  h.byLabel('core2', '暴击伤害 +28.8%');
  h.byLabel('disc4', '攻击力 30%');
  h.byLabel('disc5', '增伤 30%');
  h.byLabel('disc6', '冲击力 24%');
  h.setNum('sub_hp_flat', 12);
  h.setNum('sub_atk_pct', 7);
  h.setNum('sub_def_flat', 5);
  h.setNum('sub_cr', 9);
  h.setNum('sub_cd', 4);
  h.setNum('sub_pen_val', 6);
  h.setNum('sub_am', 11);
  h.byLabel('set0', '攻击力 +10%');
  h.byLabel('set1', '暴击伤害 +16%');
  h.byLabel('set2', '能量回复 +20%');
  return {
    name: 'full',
    base: h.base(),
    core: h.core(),
    discMain: h.discMain(),
    subStats: h.subStats(),
    sets: h.sets(),
    weapon: h.weapon(),
    rows: h.rows(),
  };
}

function caseAgent(h, roleTag, presetId) {
  h.byLabel('agent_role', roleTag);
  const sel = h.doc.getElementById('agent_preset');
  sel.value = presetId;
  sel.dispatchEvent(h.ev('change'));
  return {
    name: presetId,
    roleTag,
    base: h.base(),
    core: h.core(),
    discMain: h.discMain(),
    subStats: h.subStats(),
    sets: h.sets(),
    weapon: h.weapon(),
    rows: h.rows(),
  };
}

const out = [];
for (const build of [
  caseEmpty,
  caseFull,
  (h) => caseAgent(h, '命破', 'ep-1299'),
  (h) => caseAgent(h, '锋御', 'ep-2145'),
]) {
  const win = createLegacyWindow();
  out.push(build(harness(win)));
}

writeFileSync(process.argv[2] ?? 'legacy_cases.json', JSON.stringify(out, null, 2), 'utf8');
console.log('scenarios:', out.length);
for (const c of out) console.log(' -', c.name, c.rows.length, 'rows');
