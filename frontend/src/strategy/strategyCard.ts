/**
 * 「保存攻略」导出的攻略缩略图（一图流卡片）。
 *
 * 与整页截图不同，这张图完全由 `strategy/<slug>/data/*.json` 生成：
 * 代理人立绘 + 技能加点 / 命座 / 武器 / 驱动盘 / 队伍 / 毕业面板 / 文字攻略
 * 七条分支。数据缺失的分支自动降级为「待拓展 / —」，不会把整页 DOM 截进去。
 */

import { escapeHtml } from '@/utils/fmt';
import { formatPanelTitle, formatSubStats } from './substats';

type Json = Record<string, any>;

const list = (value: unknown): any[] => (Array.isArray(value) ? value : value ? [value] : []);
const text = (value: unknown): string => String(value ?? '');
const esc = (value: unknown): string => escapeHtml(text(value));

function img(src: unknown, className: string, alt = ''): string {
  const url = text(src);
  if (!url) return '';
  return `<img class="${className}" src="${esc(url)}" alt="${esc(alt)}" />`;
}

function placeholder(): string {
  return '<span class="strategy-card__muted">—</span>';
}

function rowHtml(label: string, content: string): string {
  return `<div class="strategy-card__row">
    <span class="strategy-card__label">${esc(label)}</span>
    <div class="strategy-card__value">${content}</div>
  </div>`;
}

/* ---------------------------------------------------------------- 技能加点 */

const SKILL_SHORT_LABELS: Record<string, string> = {
  普通攻击: '普攻',
  特殊技: '特殊技',
  强化特殊技: '强化技',
  连携技: '连携技',
  支援技: '支援技',
  核心技: '核心',
  闪避: '闪避',
};

function skillChips(strategy: Json): string {
  const items = list(strategy.skillPriority).filter((item) => item && typeof item === 'object');
  if (!items.length) return '';
  return items
    .map((item) => {
      const label = SKILL_SHORT_LABELS[text(item.label)] || text(item.label);
      const level = item.level === undefined || item.level === null ? '' : `Lv.${text(item.level)}`;
      const chip = `<span class="strategy-card__skill">
        ${img(item.icon, 'strategy-card__skill-icon')}
        <span class="strategy-card__skill-meta">
          <b>${esc(label)}</b>
          ${level ? `<small>${esc(level)}</small>` : ''}
        </span>
      </span>`;
      const next = text(item.next) ? `<span class="strategy-card__op">${esc(item.next)}</span>` : '';
      return chip + next;
    })
    .join('');
}

/* ---------------------------------------------------------------- 命座 */

function cinemaLevels(strategy: Json): string {
  const priority = strategy.cinemaPriority && typeof strategy.cinemaPriority === 'object' ? strategy.cinemaPriority : null;
  const keyLevels = new Set(
    list(priority && priority.keyLevels)
      .map((level) => Number(level))
      .filter((level) => Number.isFinite(level)),
  );
  if (!priority) return '';
  const slots = Array.from({ length: 6 }, (_, index) => {
    const level = index + 1;
    const isKey = keyLevels.has(level);
    return `<span class="strategy-card__cinema-slot${isKey ? ' is-key' : ''}">${String(level).padStart(2, '0')}</span>`;
  }).join('');
  return `<span class="strategy-card__cinema">
    <span class="strategy-card__cinema-slots">${slots}</span>
  </span>`;
}

/* ---------------------------------------------------------------- 武器 */

function weaponGroups(strategy: Json): string {
  const groups = list(strategy.weapons).filter((group) => group && typeof group === 'object');
  if (!groups.length) return '';
  return `<span class="strategy-card__stack">${groups
    .map(
      (group, index) => `<span class="strategy-card__weapon-group">
        <span class="strategy-card__tier${index === 0 ? ' is-primary' : ''}">${esc(group.tier || '推荐')}</span>
        <span class="strategy-card__weapon-items">${list(group.items)
          .map(
            (weapon) => `<span class="strategy-card__weapon">
              ${img(weapon.icon, 'strategy-card__weapon-icon', weapon.name)}
              <span class="strategy-card__weapon-name">${esc(weapon.name)}</span>
            </span>`,
          )
          .join('')}</span>
      </span>`,
    )
    .join('')}</span>`;
}

/* ---------------------------------------------------------------- 驱动盘 */

const STAT_ABBR: Array<[RegExp, string]> = [
  [/暴击率/, '暴率'],
  [/暴击伤害/, '爆伤'],
  [/攻击力/, '攻击'],
  [/穿透率/, '穿透'],
  [/能量(?:自动)?回复/, '回能'],
  [/异常精通/, '精通'],
  [/异常掌控/, '掌控'],
  [/冲击力/, '冲击'],
  [/防御力/, '防御'],
  [/生命值/, '生命'],
];

function shortStat(raw: unknown): string {
  const value = text(raw);
  if (!value) return '';
  const attributeDamage = /(风|火|冰|电|以太|物理|烈霜|玄墨|凛刃|流明)(?:属性)?伤害/.exec(value);
  if (attributeDamage) return `${attributeDamage[1]}伤`;
  for (const [pattern, label] of STAT_ABBR) {
    if (pattern.test(value)) return label;
  }
  return value.replace(/\s*[+＋]?\s*\d+(?:\.\d+)?%?/, '').trim() || value;
}

function buildName(build: Json): string {
  const name = text(build.name).trim();
  const index = name.search(/[：:]/);
  if (index >= 0) return name.slice(0, index).trim();
  const firstSet = list(build.set4).find((set) => set && typeof set === 'object' && set.name);
  return firstSet ? text(firstSet.name) : name;
}

function driveBuilds(strategy: Json): Json[] {
  if (Array.isArray(strategy.driveBuilds) && strategy.driveBuilds.length) return strategy.driveBuilds;
  return strategy.drives ? [strategy.drives] : [];
}

function driveSetIcons(sets: unknown): string {
  return list(sets)
    .map((set) => img(set && typeof set === 'object' ? set.icon : '', 'strategy-card__set-icon', set && set.name))
    .join('');
}

function driveSetNames(sets: unknown): string {
  return list(sets)
    .map((set) => esc(typeof set === 'string' ? set : (set && set.name) || ''))
    .filter(Boolean)
    .join(' / ');
}

function driveSetTag(sets: unknown): string {
  const labels = list(sets)
    .map((set) => (set && typeof set === 'object' ? shortStat(set.label) : ''))
    .filter(Boolean);
  return Array.from(new Set(labels)).join(' / ');
}

function driveBuildHtml(build: Json): string {
  const set4 = list(build.set4);
  const set2 = build.set2 && typeof build.set2 === 'object' ? build.set2 : {};
  const set2Main = list(set2.main);
  const set2Tag = driveSetTag(set2Main);
  return `<span class="strategy-card__build">
    <span class="strategy-card__build-label">${esc(buildName(build) || '推荐配装')}</span>
    <span class="strategy-card__build-sets">
      <span class="strategy-card__set">
        ${driveSetIcons(set4)}
        <b>4 ${driveSetNames(set4) || '件套'}</b>
      </span>
      <span class="strategy-card__set">
        ${driveSetIcons(set2Main)}
        <b>2 ${set2Tag || driveSetNames(set2Main) || '件套'}</b>
      </span>
    </span>
  </span>`;
}

function driveMainsHtml(strategy: Json): string {
  const build = driveBuilds(strategy).find((item) => list(item.mainStats).length);
  const stats = build ? list(build.mainStats).filter((stat) => stat && typeof stat === 'object') : [];
  if (!stats.length) return '';
  return `<span class="strategy-card__mains-row">
    <span class="strategy-card__mains-label">主词条</span>
    <span class="strategy-card__mains">${stats
      .map((stat) => {
        const alt = text(stat.alt).trim();
        const altText = alt.replace(/\s*\/\s*/g, ' / ');
        const hasAlt = altText && altText !== '无' && altText !== '—';
        return `<span class="strategy-card__main"${stat.note ? ` title="${esc(stat.note)}"` : ''}>
          <span class="strategy-card__main-slot">${esc(stat.slot || '')}</span>
          <b>${esc(stat.main || '—')}</b>
          ${hasAlt ? `<small><em>备选</em>${esc(altText)}</small>` : ''}
        </span>`;
      })
      .join('')}</span>
  </span>`;
}

function drivesHtml(strategy: Json): string {
  const builds = driveBuilds(strategy);
  if (!builds.length) return '';
  return `<span class="strategy-card__builds">
    ${builds.map(driveBuildHtml).join('')}
    ${driveMainsHtml(strategy)}
  </span>`;
}

/* ---------------------------------------------------------------- 队伍 */

function teamsHtml(strategy: Json): string {
  const teams = list(strategy.teams).filter((team) => team && typeof team === 'object');
  if (!teams.length) return '';
  return `<span class="strategy-card__stack">${teams
    .map(
      (team) => `<span class="strategy-card__team">
        <span class="strategy-card__team-name">${esc(team.name || '队伍')}</span>
        <span class="strategy-card__team-members">${list(team.members)
          .map(
            (member) => `<span class="strategy-card__member">
              ${img(member.avatar, 'strategy-card__member-avatar', member.name)}
              <span class="strategy-card__member-name">${esc(member.name)}</span>
              ${member.role ? `<small>${esc(member.role)}</small>` : ''}
            </span>`,
          )
          .join('')}</span>
      </span>`,
    )
    .join('')}</span>`;
}

/* ---------------------------------------------------------------- 毕业面板 */

function graduationPanelHtml(panel: Json, fallbackTitle: string): string {
  const totals = Array.isArray(panel.totals) ? panel.totals : [];
  const stats = totals
    .filter((field: Json) => field && typeof field === 'object')
    .map((field: Json) => {
      const value = Number(field.value);
      const display = Number.isFinite(value) ? value.toLocaleString('zh-CN') : text(field.value);
      return `<span class="strategy-card__stat">
        <span>${esc(field.label)}</span>
        <b>${esc(display)}${esc(field.unit || '')}</b>
      </span>`;
    })
    .join('');
  const sub = formatSubStats(panel.build && panel.build.subStats);
  const rawTitle = text(panel.title) || fallbackTitle;
  const formattedTitle = formatPanelTitle(rawTitle, sub);
  const title =
    sub && !/\d+\s*(词条|条)/.test(rawTitle) ? `${formattedTitle}（${sub.summary} 词条）` : formattedTitle;
  const subLine = sub
    ? `有效：${sub.breakdown || '—'}${sub.minor > 0 ? ` · +${sub.minor} 小词条` : ''}`
    : '';
  return `<span class="strategy-card__grad">
    <span class="strategy-card__grad-title">${esc(title)}</span>
    ${subLine ? `<span class="strategy-card__grad-substats">${esc(subLine)}</span>` : ''}
    <span class="strategy-card__stats">${stats || '<span class="strategy-card__muted">—</span>'}</span>
  </span>`;
}

function graduationHtml(strategy: Json): string {
  const panels: string[] = [];
  if (strategy.graduationPanel && Array.isArray(strategy.graduationPanel.totals)) {
    panels.push(graduationPanelHtml(strategy.graduationPanel, '满配毕业面板'));
  }
  if (strategy.graduationPanelAlt && Array.isArray(strategy.graduationPanelAlt.totals)) {
    panels.push(graduationPanelHtml(strategy.graduationPanelAlt, '非满配毕业面板'));
  }
  if (!panels.length) return '<span class="strategy-card__todo">待拓展</span>';
  return `<span class="strategy-card__grad-list">${panels.join('')}</span>`;
}

/* ---------------------------------------------------------------- 组装 */

function cardHtml(guide: Json): string {
  const profile = guide.profile && typeof guide.profile === 'object' ? guide.profile : {};
  const assets = guide.assets && typeof guide.assets === 'object' ? guide.assets : {};
  const strategy = guide.strategy && typeof guide.strategy === 'object' ? guide.strategy : {};
  const portrait =
    text(strategy.background) ||
    text(assets.background) ||
    text(assets.tachie) ||
    text(assets.tachieRemote) ||
    text(assets.avatar) ||
    text(assets.avatarRemote) ||
    '';
  return `<div class="strategy-card__portrait">${
    portrait ? img(portrait, 'strategy-card__tachie', profile.name || '代理人立绘') : ''
  }</div>
  <div class="strategy-card__body">
    ${rowHtml('技能加点', skillChips(strategy) || placeholder())}
    ${rowHtml('命座推荐', cinemaLevels(strategy) || placeholder())}
    ${rowHtml('武器推荐', weaponGroups(strategy) || placeholder())}
    ${rowHtml('驱动盘推荐', drivesHtml(strategy) || placeholder())}
    ${rowHtml('队伍推荐', teamsHtml(strategy) || placeholder())}
    ${rowHtml('毕业面板需求', graduationHtml(strategy))}
  </div>`;
}

/** 生成离屏卡片节点（供导出与测试复用）。 */
export function buildStrategyCard(guide: Json): HTMLElement {
  const root = document.createElement('div');
  // `strategy-card` 同时被启动页的代理人卡片使用（components.css）。
  // 加 `--export` 修饰类，确保导出卡片的布局/立绘规则覆盖那一套基础样式。
  root.className = 'strategy-card strategy-card--export';
  root.innerHTML = cardHtml(guide);
  return root;
}

/* ---------------------------------------------------------------- 截图与下载 */

let html2canvasPromise: Promise<any> | null = null;

function loadHtml2canvas(): Promise<any> {
  if ((window as any).html2canvas) return Promise.resolve((window as any).html2canvas);
  if (html2canvasPromise) return html2canvasPromise;
  html2canvasPromise = new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = 'https://unpkg.com/html2canvas@1.4.1/dist/html2canvas.min.js';
    script.onload = () => resolve((window as any).html2canvas);
    script.onerror = () => reject(new Error('加载 html2canvas 失败'));
    document.head.appendChild(script);
  });
  return html2canvasPromise;
}

function loadImage(image: HTMLImageElement): Promise<void> {
  if (image.complete) return Promise.resolve();
  return new Promise((resolve) => {
    image.addEventListener('load', () => resolve(), { once: true });
    image.addEventListener('error', () => resolve(), { once: true });
  });
}

async function waitReady(root: HTMLElement): Promise<void> {
  const timeout = new Promise<void>((resolve) => setTimeout(resolve, 6000));
  const images = Array.from(root.querySelectorAll('img'));
  const fonts = 'fonts' in document ? document.fonts.ready.then(() => undefined) : Promise.resolve();
  await Promise.race([Promise.all([...images.map(loadImage), fonts]), timeout]);
}

function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  URL.revokeObjectURL(url);
}

/** 由攻略 JSON 生成缩略图并下载（替代「保存攻略」的整页截图）。 */
export async function saveStrategyCard(guide: Json, filename: string): Promise<void> {
  const root = buildStrategyCard(guide);
  root.style.cssText = 'position:fixed;top:0;left:0;z-index:-1;pointer-events:none;';
  document.body.appendChild(root);
  try {
    await waitReady(root);
    const html2canvas = await loadHtml2canvas();
    const canvas = await html2canvas(root, {
      scale: 2,
      useCORS: false,
      backgroundColor: '#ffffff',
      logging: false,
      windowWidth: root.scrollWidth,
      windowHeight: root.scrollHeight,
    });
    const blob = await new Promise<Blob>((resolve, reject) => {
      canvas.toBlob((result: Blob | null) => {
        if (result) resolve(result);
        else reject(new Error('生成攻略图失败'));
      }, 'image/png');
    });
    downloadBlob(blob, filename);
  } finally {
    root.remove();
  }
}
