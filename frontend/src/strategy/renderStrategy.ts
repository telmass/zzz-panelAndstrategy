// @ts-nocheck
/**
 * 代理人攻略页渲染器（从 legacy 静态模板迁移）。
 *
 * 数据契约（与抓取脚本输出逐字对应）：
 *   meta     抓取元信息（agentId / 来源 / 时间）
 *   profile  姓名 / 属性 / 职业 / 评级 / 称号 / 自定义字段 / 简介
 *   assets   本地图片相对路径 + 同名 *Remote 远程兜底 URL
 *   skills   六大类技能（key: basic/dodge/assist/special/chain/core），
 *            每类含 moves[]：title / text / growth[](1-16 级或 A-F 级详细数据)
 *   cinemas  影画 1-6 层：level / name / text
 *
 * 页面由 `StrategyView.vue` 挂载，所有页面共用本文件与 strategy.css；
 * `strategy/<slug>/` 只保留 JSON 数据，不再生成静态页副本。
 */

import { strategyGuides } from '@/constants/strategyGuides';
import { copyStrategyCard, saveStrategyCard } from './strategyCard';
import { formatPanelTitle, formatSubStats } from './substats';

/** 导航栏品牌名使用登记表的中文缩写；hero 与 document.title 仍用全名。 */
const AGENT_SHORT_NAMES = new Map(
  strategyGuides.map((guide) => [guide.slug, guide.shortName]),
);

export interface RenderStrategyOptions {
  root: HTMLElement;
  guide: Record<string, unknown>;
  slug: string;
  /**
   * 基础面板的行。**由调用方从代理人预设派生**（见 `@/strategy/basePanel`）——
   * 攻略 JSON 不再自带 ``basePanel``，基础面板的唯一真实源是预设数据。
   */
  basePanel?: Array<{ label: string; value: number; unit: string }>;
  onTitle?: (title: string) => void;
}

let app: HTMLElement;
let cleanups: Array<() => void> = [];

export function renderStrategy({ root, guide, slug, basePanel, onTitle }: RenderStrategyOptions): () => void {
  cleanups.forEach((fn) => fn());
  cleanups = [];
  app = root;
  render(guide, slug, basePanel);
  const name = (guide.profile && guide.profile.name) || '';
  onTitle?.(name ? `代理人攻略 · ${name}` : '代理人攻略');
  return () => {
    cleanups.forEach((fn) => fn());
    cleanups = [];
    root.innerHTML = '';
  };
}

/* ---------------------------------------------------------------- 工具 */

function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

/** 渲染备注说明：支持字符串或字符串数组；字符串内的换行也会转成 <br>。 */
function noteHtml(note) {
  if (!note) return '';
  const items = Array.isArray(note) ? note : String(note).split('\n');
  return items.map((item) => escapeHtml(String(item))).join('<br>');
}

/** 本地路径优先，缺失（如图片下载失败）时回退远程 URL。 */
function asset(assets, key) {
  if (!assets) return '';
  return assets[key] || assets[`${key}Remote`] || '';
}

/* ---------------------------------------------------------------- 提示与下载 */

/**
 * 页面顶部临时提示一条消息，便于用户感知成功/失败。
 */
/** 在页面顶部临时提示一条消息，便于用户感知成功/失败。 */
function showTip(message) {
  const tip = document.createElement('div');
  tip.textContent = message;
  Object.assign(tip.style, {
    position: 'fixed',
    top: '10px',
    left: '50%',
    transform: 'translateX(-50%)',
    padding: '8px 14px',
    fontSize: '14px',
    background: '#111827',
    color: '#fff',
    borderRadius: '6px',
    zIndex: 200,
    pointerEvents: 'none',
    opacity: '0',
    transition: 'opacity 200ms ease',
  });
  document.body.appendChild(tip);
  requestAnimationFrame(() => (tip.style.opacity = '1'));
  setTimeout(() => {
    tip.style.opacity = '0';
    setTimeout(() => tip.remove(), 200);
  }, 2500);
}

/** 以 blob 下载图片。 */
function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/** 攻略页中文名，用于下载文件名。 */
function agentFileName(guide, suffix) {
  const name = (guide.profile && guide.profile.name) || '攻略';
  return `${name}-${suffix}.png`;
}

/**
 * 术语 -> 属性：让攻略正文里的术语按属性着色（与属性徽标同色）。
 * 其他代理人的术语按需追加，如 锐暴: '凛刃'、灼烧: '火' 等。
 */
const TERM_ATTRIBUTE_MAP = {
  风化: '风',
  风能: '风',
  风眼: '风',
  净化: '风',
  // 浸染：风属性的反色（互补色），与风属性术语形成对比
  浸染: 'wind-inverse',
};

/**
 * 职业标签 -> 颜色类名：攻略正文里的 [击破]、[锋御]、[强攻] 等局内职业称谓按职业着色。
 * 与游戏内职业徽标同色系，便于一眼区分。
 */
const TERM_ROLE_MAP = {
  强攻: 'attack',
  击破: 'stun',
  异常: 'anomaly',
  支援: 'support',
  防护: 'defense',
  命破: 'rupture',
  锋御: 'armorer',
};

/**
 * 单行文本 -> HTML：转义 + [方括号] 术语高亮。
 * 命中属性词的按属性着色，命中职业标签的按职业着色，其余保持默认强调色。
 */
function lineHtml(text) {
  if (!text) return '';
  return escapeHtml(text).replace(/\[([^\[\]]+)\]/g, (match, inner) => {
    const attr = TERM_ATTRIBUTE_MAP[inner];
    const role = TERM_ROLE_MAP[inner];
    const cls = attr ? 'term--attr-' + attr : role ? 'term--role-' + role : '';
    return `<em class="term${cls ? ' ' + cls : ''}">[${inner}]</em>`;
  });
}

/**
 * 纯文本 -> 段落 HTML。空行视为分段（影画的「效果 / 剧情」之间用空行隔开），
 * 用 .para--gap 呈现额外间距；[方括号] 术语高亮（命中属性词的按属性着色）。
 */
function paragraphsHtml(text) {
  if (!text) return '';
  let html = '';
  let gap = false;
  for (const rawLine of String(text).split('\n')) {
    const line = rawLine.trim();
    if (!line) {
      gap = true;
      continue;
    }
    const highlighted = lineHtml(line);
    html += `<p class="para${gap ? ' para--gap' : ''}">${highlighted}</p>`;
    gap = false;
  }
  return html;
}

/** 成长数据的等级区间文案：数字级显示 Lv.1–Lv.16，字母级显示 A–F。 */
function levelRangeHtml(growth) {
  if (!Array.isArray(growth) || growth.length === 0) return '';
  const levels = growth.map((entry) => entry.level);
  const first = levels[0];
  const last = levels[levels.length - 1];
  const numeric = /^\d+$/.test(first) && /^\d+$/.test(last);
  return numeric ? `Lv.${first} – Lv.${last}` : `${first} – ${last}`;
}

function growthHtml(move) {
  const growth = move.growth;
  if (!Array.isArray(growth) || growth.length === 0) return '';

  // 以「等级」为行、每个数据组（伤害倍率 / 失衡倍率等）为一列，
  // 同级数据合并进同一行；组名按出现顺序去重成表头。
  const groupNames = [];
  const rows = [];
  for (const entry of growth) {
    const cells = {};
    for (const group of entry.groups || []) {
      if (!group.rows || group.rows.length === 0) continue;
      if (!groupNames.includes(group.name)) groupNames.push(group.name);
      cells[group.name] = escapeHtml(group.rows.join('\n')).replace(/\n/g, '<br>');
    }
    if (Object.keys(cells).length === 0) continue;
    rows.push({ level: entry.level, cells });
  }
  if (groupNames.length === 0) return '';

  const head = ['等级', ...groupNames].map((name) => `<th scope="col">${escapeHtml(name)}</th>`).join('');
  const body = rows
    .map(
      ({ level, cells }) =>
        `<tr><th scope="row" class="growth__level">${escapeHtml(level)}</th>${groupNames
          .map((name) => `<td>${cells[name] ?? '—'}</td>`)
          .join('')}</tr>`,
    )
    .join('');

  return `<details class="growth">
    <summary class="growth__summary">技能详细数据<span class="growth__range">${escapeHtml(levelRangeHtml(growth))}</span></summary>
    <div class="growth__body">
      <table class="growth__table">
        <thead><tr>${head}</tr></thead>
        <tbody>${body}</tbody>
      </table>
    </div>
  </details>`;
}

/* ---------------------------------------------------------------- 区块渲染 */

/** 属性色牌的底色：与游戏内属性徽标同色（2026-10-13 需求方给定）。 */
const ATTRIBUTE_TILE_COLORS = {
  电: '#0B94FE',
  火: '#F65411',
  冰: '#00E4CD',
  风: '#85A1F7',
  以太: '#C43C8F',
  物理: '#D6A500',
  烈霜: '#5DB6FB',
  玄墨: '#CC953E',
  凛刃: '#93B7FB',
  流明: '#C08EB6',
};

const ROLE_ICON_MAP = {
  强攻: 'attack',
  击破: 'stun',
  异常: 'anomaly',
  支援: 'support',
  防护: 'defense',
  命破: 'rupture',
  锋御: 'armorer',
};
function heroIconsHtml(profile) {
  const icons = (profile && profile.icons) || {};
  const attribute = profile ? profile.attribute : '';
  const attributeIcon = icons.attribute
    ? `<img class="hero-icon hero-icon--image" src="${escapeHtml(icons.attribute)}" alt="属性图标" title="属性 · ${escapeHtml(attribute)}" onerror="this.style.display='none'" />`
    : `<span class="hero-icon hero-icon--attribute" title="属性 · ${escapeHtml(attribute)}">${escapeHtml(attribute)}</span>`;
  const roleTag = profile ? profile.roleTag : '';
  const professionIcon = icons.profession || (ROLE_ICON_MAP[roleTag] ? `/images/icons/${ROLE_ICON_MAP[roleTag]}.webp` : '');
  return `<p class="hero__icons">
    ${attributeIcon}
    ${professionIcon ? `<img class="hero-icon" src="${escapeHtml(professionIcon)}" alt="特性图标" title="特性 · ${escapeHtml(roleTag)}" onerror="this.style.display='none'" />` : ''}
    ${icons.grade ? `<img class="hero-icon" src="${escapeHtml(icons.grade)}" alt="等级图标" title="${escapeHtml(profile.grade || '')} 级" onerror="this.style.display='none'" />` : ''}
    ${icons.title ? `<span class="hero-title-badge" title="称号 · ${escapeHtml(profile.factionTitle || '')}"><img src="${escapeHtml(icons.title)}" alt="称号图标" onerror="this.parentElement.style.display='none'" /></span>` : ''}
  </p>`;
}

/**
 * 校验外部链接 URL：仅放行 https 且域名在官方 allowlist 内。
 * 防止数据中的 `javascript:`/`data:` 等危险 scheme 被渲染成可点击链接。
 */
function safeExternalUrl(url) {
  if (!url || typeof url !== 'string') return '';
  try {
    const parsed = new URL(url);
    if (parsed.protocol !== 'https:') return '';
    const ALLOWED_HOSTS = /^(?:[\w-]+\.)*mihoyo\.com$/;
    if (!ALLOWED_HOSTS.test(parsed.hostname)) return '';
    return url;
  } catch {
    return '';
  }
}

function heroHtml(guide) {
  const { profile, assets, meta } = guide;
  const tachie = asset(assets, 'tachie');
  const avatar = asset(assets, 'avatar');
  return `<header class="hero">
    <div class="hero__row">
      ${avatar ? `<img class="hero__avatar" src="${escapeHtml(avatar)}" alt="${escapeHtml(profile.name)}头像" />` : ''}
      <div class="hero__meta">
        <p class="hero__eyebrow"><span>ZENLESS ZONE ZERO</span><i></i><span>代理人攻略</span></p>
        <div class="hero__title-row">
          <h1 class="hero__name" tabindex="-1">${escapeHtml(profile.name)}</h1>
          ${heroIconsHtml(profile)}
        </div>
        <p class="hero__source">数据来源：${(() => { const safeUrl = safeExternalUrl(meta.source); return safeUrl ? `<a href="${escapeHtml(safeUrl)}" target="_blank" rel="noopener noreferrer">米游社绝区零 WIKI</a>` : '米游社绝区零 WIKI'; })()}，抓取于 ${escapeHtml(
          meta.scrapedAt ? new Date(meta.scrapedAt).toLocaleString('zh-CN') : '—',
        )}</p>
      </div>
      ${tachie ? `<img class="hero__tachie" src="${escapeHtml(tachie)}" alt="${escapeHtml(profile.name)}立绘" />` : ''}
    </div>
  </header>`;
}

/** 左侧导航栏：四大区块 + 技能六大类子链接 + 移动端目录开关。 */
function sidebarHtml(guide, slug) {
  const sections = [
    { id: 'guide', label: '攻略', index: '01' },
    { id: 'base', label: '基础面板', index: '02' },
    { id: 'skills', label: '技能', index: '03' },
    { id: 'cinema', label: '影画', index: '04' },
  ];
  const skillSublinks = (guide.skills || [])
    .map((skill) => `<a class="sidebar__sublink" href="#skill-${escapeHtml(skill.key)}">${escapeHtml(skill.name)}</a>`)
    .join('');
  const name =
    AGENT_SHORT_NAMES.get(slug) ||
    (guide.profile && guide.profile.name) ||
    '';
  // 攻略二级菜单（与攻略区块的 id 一一对应；毕业面板视数据存在与否显隐）
  const strategy = guide.strategy;
  const guideSublinks = strategy
    ? [
        ...(strategy.cinemaPriority && strategy.cinemaPriority.image ? [{ id: 'guide-cinemas', label: '关键命座推荐' }] : []),
        { id: 'guide-skills', label: '技能加点优先级' },
        { id: 'guide-weapons', label: '音擎推荐' },
        { id: 'guide-drives', label: '驱动盘推荐' },
        ...(strategy.graduationPanel && strategy.graduationPanel.totals ? [{ id: 'guide-graduation', label: '毕业面板' }] : []),
        { id: 'guide-team', label: '队伍推荐' },
        { id: 'guide-text', label: '文字攻略' },
      ]
        .map((item) => `<a class="sidebar__sublink" href="#${item.id}">${escapeHtml(item.label)}</a>`)
        .join('')
    : '';
  return `<aside class="sidebar" id="sidebar" aria-label="攻略目录">
    <div class="sidebar__brand">
      <span class="sidebar__brand-badge">ZZZ</span>
      <div class="sidebar__brand-text">
        <p class="sidebar__brand-name">${escapeHtml(name)}</p>
        <p class="sidebar__brand-sub">代理人攻略</p>
      </div>
      <button class="sidebar__toggle" type="button" aria-expanded="false" aria-controls="sidebar-nav">目录</button>
    </div>
    <nav class="sidebar__nav" id="sidebar-nav" aria-label="页面导航">
      ${sections
        .map((section) => {
          let sub = '';
          if (section.id === 'skills' && skillSublinks) {
            sub = `<div class="sidebar__sublinks">${skillSublinks}</div>`;
          } else if (section.id === 'guide' && guideSublinks) {
            sub = `<div class="sidebar__sublinks">${guideSublinks}</div>`;
          }
          return `<div class="sidebar__group">
            <a class="sidebar__link" href="#${section.id}" data-spy>
              <span class="sidebar__index">${section.index}</span>
              <span class="sidebar__label">${escapeHtml(section.label)}</span>
            </a>${sub}
          </div>`;
        })
        .join('')}
    </nav>
    <div class="sidebar__actions">
      <button class="sidebar__btn" type="button" data-action="save-guide">保存攻略</button>
      <button class="sidebar__btn" type="button" data-action="copy-guide">复制攻略</button>
    </div>
  </aside>`;
}

/** 一级板块头部带：编号方块 + 标题 + 一句副标题（与左侧导航编号一致）。 */
function sectionHeadHtml(index, title, sub, id) {
  return `<header class="section__head">
    <span class="section__no">${escapeHtml(index)}</span>
    <div class="section__heading">
      <h2 class="section__title" id="${escapeHtml(id)}-title">${escapeHtml(title)}</h2>
      ${sub ? `<p class="section__sub">${escapeHtml(sub)}</p>` : ''}
    </div>
  </header>`;
}

function basePanelHtml(fields) {
  const rows = (fields || [])
    .map((field) => {
      const value = Number(field.value).toLocaleString('zh-CN');
      return `<div class="base-field">
        <span class="base-field__label">${escapeHtml(field.label)}</span>
        <span class="base-field__value">${escapeHtml(value)}${escapeHtml(field.unit || '')}</span>
      </div>`;
    })
    .join('');
  return `<section id="base" class="section reveal" aria-labelledby="base-title">
    ${sectionHeadHtml('02', '基础面板', '60 级 · 0 突破 · 不含核心技与配装加成', 'base')}
    <p class="section__hint">该面板为晋升需求滑块的初始行与满级行合并结果，与游戏内 60 级（0 突破）基础数据一致。</p>
    <div class="base-panel">${rows || '<p class="para">暂无基础面板数据</p>'}</div>
  </section>`;
}

/** 单个技能区块：多招式类别用「招式二级选择页」（tab 切换），单招式类别直接展示面板。 */
function skillCatHtml(skill) {
  const moves = skill.moves || [];
  const head = `<header class="skill-cat__head">
    ${skill.icon ? `<img class="skill-cat__icon" src="${escapeHtml(skill.icon)}" alt="" loading="lazy" onerror="this.style.display='none'" />` : ''}
    <h3 class="skill-cat__name">${escapeHtml(skill.name)}</h3>
    <span class="skill-cat__count">${moves.length} 个招式</span>
  </header>`;

  const skillId = `skill-${escapeHtml(skill.key)}`;
  const tabbed = moves.length > 1;
  const panelHtml = (move, index) => {
    const panelId = `${skillId}-panel-${index}`;
    const tabId = `${skillId}-tab-${index}`;
    const panelAttrs = tabbed
      ? ` role="tabpanel" id="${panelId}" aria-labelledby="${tabId}" tabindex="0"${index === 0 ? '' : ' hidden'}`
      : '';
    return `<div class="move-panel${index === 0 ? ' is-active' : ''}" data-panel="${index}"${panelAttrs}>
      <h4 class="move__title">${escapeHtml(move.title)}</h4>
      <div class="move__text">${paragraphsHtml(move.text)}</div>
      ${growthHtml(move)}
    </div>`;
  };

  // 多招式类别：招式 tab + 详情面板的二级选择
  if (tabbed) {
    // tab 标签去掉与类别名重复的前缀（如「普通攻击：」），面板内仍用完整标题
    const prefix = new RegExp(`^${skill.name}[：:]\\s*`);
    const tabLabel = (title) => title.replace(prefix, '');
    const tabs = moves
      .map(
        (move, index) =>
          `<button class="move-tab${index === 0 ? ' is-active' : ''}" type="button" role="tab" id="${skillId}-tab-${index}" aria-selected="${index === 0}" aria-controls="${skillId}-panel-${index}" tabindex="${index === 0 ? 0 : -1}" data-move="${index}">${escapeHtml(tabLabel(move.title))}</button>`,
      )
      .join('');
    const panels = moves.map(panelHtml).join('');
    return `<section class="skill-cat skill-cat--tabbed" id="${skillId}">
      ${head}
      <div class="move-tabs" role="tablist" aria-label="${escapeHtml(skill.name)}招式">${tabs}</div>
      <div class="move-panels">${panels}</div>
    </section>`;
  }

  // 单招式类别：无 tab bar，直接展示面板
  if (moves.length === 1) {
    return `<section class="skill-cat skill-cat--tabbed" id="${skillId}">
      ${head}
      <div class="move-panels">${moves.map(panelHtml).join('')}</div>
    </section>`;
  }

  return `<section class="skill-cat skill-cat--tabbed" id="${skillId}">
    ${head}
    <div class="move-panels"><p class="para">暂无招式数据</p></div>
  </section>`;
}

function skillsHtml(guide) {
  const skillList = [...(guide.skills || [])].sort(
    (a, b) => SKILL_CATEGORY_ORDER.indexOf(a.key) - SKILL_CATEGORY_ORDER.indexOf(b.key),
  );
  const blocks = skillList.map(skillCatHtml);
  return `<section id="skills" class="section reveal" aria-labelledby="skills-title">
    ${sectionHeadHtml('03', '技能', '六大类技能 · 板块内支持按招式二级切换', 'skills')}
    <p class="section__hint">按普攻 / 闪避 / 支援 / 特殊 / 连携（含终结技）/ 核心技六大类展示；各板块内支持按招式二级切换查看描述，展开「技能详细数据」可查看各等级数值。</p>
    ${blocks.join('')}
  </section>`;
}

/** 绑定技能招式 tab：点击 / 方向键 / Home / End，并同步 ARIA 状态。 */
/** 通用 tablist：技能招式与驱动盘方案共用点击 / 方向键 / Home / End 与 ARIA 同步。 */
function bindTablist({ tablistSelector, tabSelector, panelSelector }) {
  app.querySelectorAll(tablistSelector).forEach((bar) => {
    const tabs = [...bar.querySelectorAll(tabSelector)];
    const scope = bar.parentElement;
    if (!scope || tabs.length === 0) return;

    const activate = (tab) => {
      if (!tab) return;
      const index = tabs.indexOf(tab);
      tabs.forEach((item) => {
        const active = item === tab;
        item.classList.toggle('is-active', active);
        item.setAttribute('aria-selected', String(active));
        item.tabIndex = active ? 0 : -1;
      });
      scope.querySelectorAll(panelSelector).forEach((panel) => {
        const active = panel.dataset.panel === String(index);
        panel.classList.toggle('is-active', active);
        panel.hidden = !active;
      });
    };

    bar.addEventListener('click', (event) => {
      const tab = event.target.closest(tabSelector);
      if (!tab || !bar.contains(tab)) return;
      activate(tab);
    });

    bar.addEventListener('keydown', (event) => {
      const current = tabs.indexOf(document.activeElement);
      if (current === -1) return;
      let next = current;
      if (event.key === 'ArrowRight') next = (current + 1) % tabs.length;
      else if (event.key === 'ArrowLeft') next = (current - 1 + tabs.length) % tabs.length;
      else if (event.key === 'Home') next = 0;
      else if (event.key === 'End') next = tabs.length - 1;
      else return;
      event.preventDefault();
      tabs[next].focus();
      activate(tabs[next]);
    });
  });
}

/** 左侧导航：移动端目录开关 + 子链接点击后自动收起。 */
function bindSidebar() {
  const sidebar = app.querySelector('.sidebar');
  const toggle = app.querySelector('.sidebar__toggle');
  if (!sidebar || !toggle) return () => {};
  toggle.addEventListener('click', () => {
    const open = sidebar.classList.toggle('is-open');
    toggle.setAttribute('aria-expanded', String(open));
    toggle.textContent = open ? '收起' : '目录';
  });
  sidebar.querySelectorAll('.sidebar__sublink').forEach((link) => {
    link.addEventListener('click', () => {
      sidebar.classList.remove('is-open');
      toggle.setAttribute('aria-expanded', 'false');
      toggle.textContent = '目录';
    });
  });
  return () => {};
}

/** 滚动侦测：按当前可见区块高亮左侧导航（子区块优先；触底时兜底高亮最后一个目标）。 */
function bindScrollSpy() {
  const links = [...app.querySelectorAll('.sidebar__link[data-spy], .sidebar__sublink')];
  if (links.length === 0 || !('IntersectionObserver' in window)) return () => {};
  const targets = [...new Set(links.map((link) => app.querySelector(link.getAttribute('href'))))].filter(Boolean);
  if (targets.length === 0) return () => {};
  // 命中优先级：深层目标（被另一目标包含，如 skill-* 之于 #skills）优先
  const deepFirst = targets
    .slice()
    .sort((a, b) => (b.contains(a) ? -1 : a.contains(b) ? 1 : 0))
    .map((node) => node.id);
  // 页面最底部的目标（DOM 顺序最后一个）：滚动触底时的兜底高亮
  const lastId = targets[targets.length - 1].id;
  const visible = new Set();
  const isAtBottom = () =>
    window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 4;
  const paint = () => {
    const current = isAtBottom() ? lastId : deepFirst.find((id) => visible.has(id));
    const currentHref = current ? `#${current}` : '';
    links.forEach((link) => {
      const active = link.getAttribute('href') === currentHref;
      link.classList.toggle('is-active', active);
      if (active) link.setAttribute('aria-current', 'location');
      else link.removeAttribute('aria-current');
    });
    app.querySelectorAll('.sidebar__link').forEach((link) => {
      const group = link.closest('.sidebar__group');
      link.classList.toggle('is-parent', !!group && !!group.querySelector('.sidebar__sublink.is-active'));
    });
  };
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) visible.add(entry.target.id);
        else visible.delete(entry.target.id);
      });
      paint();
    },
    { rootMargin: '-15% 0px -70% 0px', threshold: 0 },
  );
  targets.forEach((node) => observer.observe(node));
  // 滚动时也重绘：末尾区块不足一屏、停在命中带下方时，靠触底判断补上高亮
  let ticking = false;
  const onScroll = () => {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(() => {
      paint();
      ticking = false;
    });
  };
  window.addEventListener('scroll', onScroll, { passive: true });
  paint();
  return () => {
    observer.disconnect();
    window.removeEventListener('scroll', onScroll);
  };
}

/** 入场动效：主区块进入视口时淡入上移（一次性，尊重减少动效偏好）。 */
function bindReveal() {
  const items = [...app.querySelectorAll('.reveal')];
  const showAll = () => items.forEach((item) => item.classList.add('is-visible'));
  const reduceMotion =
    typeof window.matchMedia === 'function' && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduceMotion || !('IntersectionObserver' in window)) {
    showAll();
    return () => {};
  }
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.06 },
  );
  items.forEach((item) => observer.observe(item));
  return () => observer.disconnect();
}

/** 返回顶部按钮：滚动超过一屏后浮现。 */
function bindToTop() {
  const button = app.querySelector('.to-top');
  if (!button) return () => {};
  const onScroll = () => button.classList.toggle('is-visible', window.scrollY > 480);
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
  button.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
  return () => window.removeEventListener('scroll', onScroll);
}

/**
 * 绑定「保存攻略」/「复制攻略」按钮。
 * 「保存攻略」不再截取页面，而是把 strategy JSON 渲染成一张紧凑的攻略卡片；
 * 「复制攻略」把攻略卡复制到系统剪贴板（不可用时退回下载）。
 */
function bindSaveButtons(guide) {
  const actions = app.querySelector('.sidebar__actions');
  if (!actions) return;
  actions.addEventListener('click', async (event) => {
    const btn = event.target.closest('.sidebar__btn');
    if (!btn || !actions.contains(btn)) return;
    const action = btn.dataset.action;
    if (!app || app.dataset.state !== 'ready') return;

    if (action === 'save-guide') {
      const filename = agentFileName(guide, '攻略');
      btn.disabled = true;
      try {
        await saveStrategyCard(guide, filename);
        showTip('已下载：' + filename);
      } catch (error) {
        showTip('生成攻略图失败：' + (error && error.message ? error.message : String(error)));
      } finally {
        btn.disabled = false;
      }
      return;
    }

    if (action !== 'copy-guide') return;
    const filename = agentFileName(guide, '攻略');
    btn.disabled = true;
    try {
      // 复制到剪贴板：拿到图就能直接粘贴，不用先下载再上传。
      const copied = await copyStrategyCard(guide, filename);
      showTip(copied ? '已复制攻略图，可直接粘贴' : '剪贴板不可用，已改为下载：' + filename);
    } catch (error) {
      showTip('生成攻略图失败：' + (error && error.message ? error.message : String(error)));
    } finally {
      btn.disabled = false;
    }
  });
}

function cinemaHtml(guide) {
  const backdrops = guide.cinemaBackdrops || {};
  const backdropImageOf = (level) => {
    const backdrop = backdrops[String(level)];
    return backdrop ? backdrop.image || backdrop.imageRemote || '' : '';
  };

  // 按「共用同一张展示图」把影画分组：1-3 命共用影画展示2、4-6 命共用影画展示3，
  // 每组用一个大框承载该展示图作背景（分组规则完全由 cinemaBackdrops 数据驱动）
  const groups = [];
  (guide.cinemas || []).forEach((cinema) => {
    const image = backdropImageOf(cinema.level);
    const last = groups[groups.length - 1];
    if (last && last.image === image) {
      last.items.push(cinema);
    } else {
      groups.push({ image, items: [cinema] });
    }
  });

  const cardHtml = (cinema) => `<article class="cinema">
    <header class="cinema__head">
      <span class="cinema__badge">影画 ${escapeHtml(cinema.level)}</span>
      ${cinema.name ? `<span class="cinema__name">${escapeHtml(cinema.name)}</span>` : ''}
    </header>
    <div class="cinema__text">${paragraphsHtml(cinema.text)}</div>
  </article>`;

  const blocks = groups
    .map((group) => {
      const levels = group.items.map((cinema) => cinema.level);
      const label = levels.length > 1 ? `影画 ${levels[0]} - ${levels[levels.length - 1]}` : `影画 ${levels[0]}`;
      const bg = group.image
        ? `<div class="cinema-group__bg" style="background-image:url('${escapeHtml(group.image)}')" aria-hidden="true"></div>`
        : '';
      const cards = group.items.map(cardHtml).join('');
      return `<div class="cinema-group">
        ${bg}
        <div class="cinema-group__inner">
          <span class="cinema-group__label">${escapeHtml(label)}</span>
          <div class="cinema-grid">${cards}</div>
        </div>
      </div>`;
    })
    .join('');

  return `<section id="cinema" class="section reveal" aria-labelledby="cinema-title">
    ${sectionHeadHtml('04', '影画', '影画 1 - 6 · 按命数分组展示 WIKI 展示图', 'cinema')}
    <div class="cinema-groups">${blocks || '<p class="para">暂无影画数据</p>'}</div>
  </section>`;
}

function footerHtml(guide) {
  return `<footer class="footer">
    <p>代理人攻略原型页 · ${escapeHtml((guide.meta && guide.meta.name) || '')}</p>
    <p>数据来自米游社绝区零 WIKI，仅供学习交流，版权归 miHoYo 所有</p>
  </footer>`;
}

/* ---------- 攻略（第四部分） ---------- */

/** 六大类技能的固定顺序（普攻/闪避/支援/特殊/连携/核心），技能区按此排序展示。 */
const SKILL_CATEGORY_ORDER = ['basic', 'dodge', 'assist', 'special', 'chain', 'core'];

/**
 * 关键命座（影画）推荐——左侧小图 + 右侧 6 格编号，关键命座高亮。
 * JSON 字段：image（图 URL）、keyLevels（[1..6]）、note（说明文字）。
 * 没有 cinemaPriority 字段的代理人整块跳过。
 */
function cinemaPriorityHtml(strategy) {
  const cp = strategy.cinemaPriority;
  if (!cp || !cp.image) return '';
  const keyLevels = new Set(cp.keyLevels || []);
  const slots = Array.from({ length: 6 }, (_, i) => {
    const level = i + 1;
    const isKey = keyLevels.has(level);
    const num = String(level).padStart(2, '0');
    return `<span class="cinema-slot${isKey ? ' cinema-slot--key' : ''}" ${isKey ? 'title="关键命座"' : ''}>${num}</span>`;
  }).join('');
  const note = cp.note
    ? `<figcaption class="cinema-priority__note">${escapeHtml(cp.note)}</figcaption>`
    : '';
  return `<div class="guide-block" id="guide-cinemas">
    <h3 class="guide-block__title">关键命座推荐</h3>
    <figure class="cinema-priority">
      <img
        class="cinema-priority__image"
        src="${escapeHtml(cp.image)}"
        alt="命座图标"
        loading="lazy"
      />
      <div class="cinema-priority__slots">${slots}</div>
      ${note}
    </figure>
  </div>`;
}

function skillPriorityHtml(strategy) {
  // 加点优先级用「> / =」连接符表达（数据顺序即优先级链），与副词条一致
  const chain = (strategy.skillPriority || [])
    .map((item) => {
      const chip = `<span class="skill-chip">
        ${item.icon ? `<img class="skill-chip__icon" src="${escapeHtml(item.icon)}" alt="" loading="lazy" onerror="this.style.display='none'" />` : ''}
        <span class="skill-chip__meta">
          <span class="skill-chip__label">${escapeHtml(item.label)}</span>
          <span class="skill-chip__level">Lv.${escapeHtml(item.level ?? 0)}</span>
        </span>
      </span>`;
      const next = item.next ? `<span class="skill-op">${escapeHtml(item.next)}</span>` : '';
      return chip + next;
    })
    .join('');
  return `<div class="guide-block" id="guide-skills">
    <h3 class="guide-block__title">技能加点优先级</h3>
    <p class="skill-chain">${chain || '暂无数据'}</p>
  </div>`;
}

function weaponHtml(strategy) {
  const cards = (strategy.weapons || [])
    .map((group) => {
      const items = group.items || [];
      return `<div class="weapon-card${group.note ? '' : ' weapon-card--no-note'}">
        <div class="weapon-card__head">
          <span class="weapon-card__tier">${escapeHtml(group.tier)}</span>
          <span class="weapon-card__count">${items.length} 把</span>
        </div>
        <div class="weapon-card__row">
          ${items
            .map(
              (weapon) => `<div class="weapon-item">
                ${weapon.icon ? `<img class="weapon-item__icon" src="${escapeHtml(weapon.icon)}" alt="${escapeHtml(weapon.name)}图标" loading="lazy" onerror="this.style.display='none'" />` : ''}
                <div class="weapon-item__meta">
                  <p class="weapon-item__name">${escapeHtml(weapon.name)}</p>
                  <p class="weapon-item__stats">${escapeHtml(weapon.stats)}</p>
                </div>
              </div>`,
            )
            .join('')}
        </div>
        ${group.note ? `<p class="weapon-card__note">${noteHtml(group.note)}</p>` : ''}
      </div>`;
    })
    .join('');
  return `<div class="guide-block" id="guide-weapons">
    <h3 class="guide-block__title">音擎推荐</h3>
    <div class="weapon-list">${cards || '<p class="para">暂无数据</p>'}</div>
  </div>`;
}

/** 套装名称 / 图标 / 效果字段兼容字符串与对象两种历史形态。 */
function driveSetValue(set, key) {
  if (!set || typeof set !== 'object') return '';
  return set[key] || '';
}

function driveSetUnitHtml(set) {
  const name = typeof set === 'string' ? set : set.name || '';
  const icon = typeof set === 'string' ? '' : set.icon || '';
  return `<span class="drive-set-row__unit">
    ${icon ? `<img class="drive-set-row__icon" src="${escapeHtml(icon)}" alt="${escapeHtml(name)}图标" loading="lazy" onerror="this.style.display='none'" />` : ''}
    <span class="drive-set-row__unit-name">${escapeHtml(name)}</span>
  </span>`;
}

function driveSetTagHtml(tag) {
  return tag ? `<span class="drive-set-row__tag">${escapeHtml(tag)}</span>` : '';
}

function driveSetEffectHtml(tag, text) {
  if (!text) return '';
  return `<p class="drive-set-row__effect"><span>${escapeHtml(tag)}</span><span>${escapeHtml(text)}</span></p>`;
}

function driveSetSceneHtml(text) {
  if (!text) return '';
  return `<p class="drive-set-row__scene"><span>适用</span><span>${escapeHtml(text)}</span></p>`;
}

function driveSetRowShell(units, body) {
  return `<div class="drive-set-row">
    <div class="drive-set-row__units">${units}</div>
    ${body ? `<div class="drive-set-row__body">${body}</div>` : ''}
  </div>`;
}

/** 4 件套：每个套装一行；alt4 递归为「备选 4 件套」行。 */
function driveSet4RowsHtml(sets, tag = '') {
  return asList(sets)
    .filter(Boolean)
    .map((set) => {
      const body = [
        driveSetEffectHtml('二件套', driveSetValue(set, 'label')),
        driveSetEffectHtml('四件套', driveSetValue(set, 'effect4')),
        driveSetSceneHtml(driveSetValue(set, 'scene')),
      ].join('');
      const row = driveSetRowShell(`${driveSetUnitHtml(set)}${driveSetTagHtml(tag)}`, body);
      const alt = driveSetValue(set, 'alt4') ? driveSet4RowsHtml(set.alt4, '备选') : '';
      return row + alt;
    })
    .join('');
}

/** 2 件套：按二件套效果合并同效果套装；每行可并列多个套装。 */
function driveSet2RowsHtml(sets, tag) {
  const list = asList(sets).filter(Boolean);
  if (!list.length) return '';
  const groups = [];
  for (const set of list) {
    const label = driveSetValue(set, 'label').trim();
    const hit = groups.find((group) => group.label === label);
    if (hit) hit.sets.push(set);
    else groups.push({ label, sets: [set] });
  }
  return groups
    .map(({ label, sets: groupSets }) => {
      const units = groupSets.map(driveSetUnitHtml).join('') + driveSetTagHtml(tag);
      return driveSetRowShell(units, driveSetEffectHtml('二件套', label));
    })
    .join('');
}

/**
 * 2 件套**组**，按槽位收集。
 *
 * **组**与**候选**是两个维度，不能混：
 *
 * - **组**（这一层）：第 1/2/3 组 2 件套，**并列，都要装**。2+2+2 就是三组。
 *   字段是 ``set2`` / ``set2b`` / ``set2c``。
 * - **候选**（组内一层）：``main`` / ``alt``——同一组里的首选 / 备选套装，
 *   二选一。``main`` / ``alt`` 各自还可以是数组，表示「多套同效果的候选」
 *   （如「物理伤害 +10%」有獠牙重金属与沧浪行歌两套）。
 *
 * 6 个槽位最多同时生效**三组** 2 件套（2+2+2），也最多生效**一个** 4 件套——
 * 4 件套组必然带来它自己的 2 件套效果，而 4+4 装不下（8 片 > 6 槽）。
 *
 * ``set4`` 是**另一条轴**：它是 4 件套的**候选**列表（三选一，各带 scene），
 * 不是「同时生效多个 4 件套」——见 ``strategy/README.md``。
 */
function driveSet2Groups(build) {
  return ['set2', 'set2b', 'set2c']
    .map((key) => build[key])
    .filter((group) => group && typeof group === 'object')
    .map((group) => (Array.isArray(group) ? group[0] : group));
}

/** 方案名缺省时用套装组合自动生成，追加方案不强制命名。 */
function driveBuildName(build, set4, set2Groups) {
  if (build.name) return build.name;
  const set4List = asList(set4);
  const set2Main = set2Groups.flatMap((group) => asList(group.main));
  const fallback = [
    set4List.length ? `${set4List.map((set) => (typeof set === 'string' ? set : set.name)).filter(Boolean).join(' / ')} 4 件套` : '',
    set2Main.length ? `${set2Main.map((set) => (typeof set === 'string' ? set : set.name)).filter(Boolean).join(' / ')} 2 件套` : '',
  ].filter(Boolean).join(' + ');
  return fallback || '推荐配装';
}

/** 单个驱动盘推荐方案：套装/副词条两栏 + 全宽四列主词条表。 */
function driveBuildHtml(build) {
  const set4 = build.set4;
  const set2Groups = driveSet2Groups(build);
  // 2+2+2 没有 4 件套组——那一栏整栏不渲染，而不是留一个「暂无数据」。
  const hasSet4 = asList(set4).length > 0;

  const mains = (Array.isArray(build.mainStats) ? build.mainStats : [])
    .map(
      (item) => `<tr>
        <th scope="row" class="drive-main__slot">${escapeHtml(item.slot)}</th>
        <td class="drive-main__stat">${escapeHtml(item.main)}</td>
        <td class="drive-main__alt">${escapeHtml(item.alt)}</td>
        <td class="drive-main__note">${noteHtml(item.note) || '—'}</td>
      </tr>`,
    )
    .join('');

  const subs = (Array.isArray(build.subPriority) ? build.subPriority : [])
    .map((item) => {
      const label = typeof item === 'string' ? item : item.label;
      const next = typeof item === 'string' ? '' : item.next || '';
      return `<span class="sub-chip">${escapeHtml(label)}</span>${next ? `<span class="sub-op">${escapeHtml(next)}</span>` : ''}`;
    })
    .join('');

  // 多个 2 件套组时逐组编号（①②③），单组时沿用「2 件套」不带编号。
  const set2Sections = set2Groups
    .map((group, index) => {
      const title = set2Groups.length > 1 ? `2 件套 ${'①②③④'[index] || index + 1}` : '2 件套';
      const rows = driveSet2RowsHtml(group.main, '首选') + driveSet2RowsHtml(group.alt, '备选');
      return `<section class="drive-spec__set2${set2Groups.length > 1 ? ' drive-spec__set2--group' : ''}" aria-label="${escapeHtml(title)}推荐">
          <h5 class="guide-block__subtitle">${escapeHtml(title)}</h5>
          <div class="drive-set-list">${rows || '<p class="para">暂无数据</p>'}</div>
        </section>`;
    })
    .join('');

  return `<div class="drive-group">
    <h4 class="drive-group__title">${escapeHtml(driveBuildName(build, set4, set2Groups))}</h4>
    ${build.note ? `<p class="drive-group__note">${noteHtml(build.note)}</p>` : ''}
    <div class="drive-spec">
      <div class="drive-spec__sets">
        ${hasSet4 ? `<section class="drive-spec__set4" aria-label="4 件套推荐">
          <h5 class="guide-block__subtitle">4 件套</h5>
          <div class="drive-set-list">${driveSet4RowsHtml(set4)}</div>
        </section>` : ''}
        ${set2Sections || '<section class="drive-spec__set2" aria-label="2 件套推荐"><h5 class="guide-block__subtitle">2 件套</h5><div class="drive-set-list"><p class="para">暂无数据</p></div></section>'}
      </div>
      <section class="drive-spec__mains" aria-label="主词条推荐">
        <h5 class="guide-block__subtitle">主词条推荐</h5>
        ${mains ? `<div class="table-scroll">
          <table class="drive-main" aria-label="主词条推荐">
            <thead><tr><th scope="col">部位</th><th scope="col">首选</th><th scope="col">备选</th><th scope="col">备注</th></tr></thead>
            <tbody>${mains}</tbody>
          </table>
        </div>` : '<p class="para">暂无主词条数据</p>'}
      </section>
      <section class="drive-spec__subs" aria-label="副词条优先级">
        <h5 class="guide-block__subtitle">副词条优先级</h5>
        <p class="sub-prio">${subs || '暂无数据'}</p>
      </section>
    </div>
  </div>`;
}

function drivesHtml(strategy) {
  const builds = Array.isArray(strategy.driveBuilds)
    ? strategy.driveBuilds
    : strategy.drives
      ? [strategy.drives]
      : [];
  if (!builds.length) {
    return `<div class="guide-block" id="guide-drives">
      <h3 class="guide-block__title">驱动盘推荐</h3>
      <p class="para">暂无数据</p>
    </div>`;
  }
  if (builds.length === 1) {
    return `<div class="guide-block" id="guide-drives">
      <h3 class="guide-block__title">驱动盘推荐</h3>
      ${driveBuildHtml(builds[0])}
    </div>`;
  }
  const tabs = builds
    .map((build, index) => {
      const name = driveBuildName(build, build.set4, driveSet2Groups(build));
      return `<button class="drive-tab${index === 0 ? ' is-active' : ''}" type="button" role="tab" id="drive-tab-${index}" aria-selected="${index === 0}" aria-controls="drive-panel-${index}" tabindex="${index === 0 ? 0 : -1}" title="${escapeHtml(name)}">${escapeHtml(name)}</button>`;
    })
    .join('');
  const panels = builds
    .map(
      (build, index) => `<div class="drive-panel${index === 0 ? ' is-active' : ''}" data-panel="${index}" role="tabpanel" id="drive-panel-${index}" aria-labelledby="drive-tab-${index}"${index === 0 ? '' : ' hidden'}>
      ${driveBuildHtml(build)}
    </div>`,
    )
    .join('');
  return `<div class="guide-block" id="guide-drives">
    <h3 class="guide-block__title">驱动盘推荐</h3>
    <div class="drive-tabs" role="tablist" aria-label="驱动盘方案">${tabs}</div>
    <div class="drive-panels drive-panels--tabbed">${panels}</div>
  </div>`;
}

/** 毕业配装说明的键名 -> 展示文案。 */
const BUILD_LABELS = {
  agent: '角色',
  weapon: '音擎',
  core: '核心技',
  set4: '4 件套',
  set2: '2 件套',
  mainStats: '主词条',
  subStats: '副词条',
};

/** 单值统一成数组，便于把「单对象 / 数组 / 空」三种写法一把梭。 */
function asList(value) {
  return Array.isArray(value) ? value : value ? [value] : [];
}

/** 毕业配装里这几个字段配图标：按名字从音擎推荐 / 驱动盘推荐里取。 */
const BUILD_ICON_FIELDS = {
  weapon: (strategy, name) => {
    for (const tier of strategy.weapons || []) {
      for (const item of tier.items || []) {
        if (item.name === name && item.icon) return item.icon;
      }
    }
    return '';
  },
  set4: (strategy, name) => findDiscIcon(strategy, name),
  set2: (strategy, name) => findDiscIcon(strategy, name),
};

/** 在驱动盘推荐（4 件套单值或数组、2 件套组的对象或数组）里按套装名找图标。 */
function findDiscIcon(strategy, name) {
  for (const build of strategy.driveBuilds || []) {
    const set2Sets = driveSet2Groups(build).flatMap((group) => [
      ...asList(group.main),
      ...asList(group.alt),
    ]);
    for (const set of [...asList(build.set4), ...set2Sets]) {
      if (set && set.name === name && set.icon) return set.icon;
    }
  }
  return '';
}

function graduationPanelHtml(strategy, panel) {
  const totals = panel.totals
    .map(
      (field) => `<div class="base-field">
        <span class="base-field__label">${escapeHtml(field.label)}</span>
        <span class="base-field__value">${escapeHtml(Number(field.value).toLocaleString('zh-CN'))}${escapeHtml(field.unit || '')}</span>
      </div>`,
    )
    .join('');
  const build = Object.entries(panel.build || {})
    .filter(([key]) => !['agent', 'weapon', 'core'].includes(key))
    // 空的条目不渲染——2+2+2 没有 4 件套组时，``build.set4`` 是 null，
    // 留一行空的「4 件套」比不显示更让人困惑。
    .filter(([, value]) => value !== null && value !== undefined && value !== '')
    .map(([key, value]) => {
      const lookup = BUILD_ICON_FIELDS[key];
      // 图标加载失败就退化成纯文字，不影响这一行的信息
      const iconHtml = (name) => {
        const icon = lookup ? lookup(strategy, String(name)) : '';
        return icon
          ? `<img class="build-row__icon" src="${escapeHtml(icon)}" alt="" loading="lazy" onerror="this.style.display='none'" />`
          : '';
      };
      // 计算仍用完整词条；这里只把「副词条」行换成「大词条 + 小词条」的展示口径。
      const displayValue =
        key === 'subStats' ? formatSubStats(value)?.display || value : value;
      // 值可能是数组（2+2+2 的多组 2 件套）：逐个渲染「图标 + 名称」。
      const content = Array.isArray(value)
        ? value
            .map((item) => `${iconHtml(item)}${escapeHtml(String(item))}`)
            .join(' + ')
        : `${iconHtml(value)}${escapeHtml(displayValue)}`;
      return `<div class="build-row"><dt>${escapeHtml(BUILD_LABELS[key] || key)}</dt><dd>${content}</dd></div>`;
    })
    .join('');
  return `<div class="base-panel base-panel--graduation">${totals}</div>
    <dl class="build-spec">${build}</dl>`;
}

function graduationHtml(strategy) {
  const panel = strategy.graduationPanel;
  if (!panel || !Array.isArray(panel.totals)) return '';
  const panelStats = formatSubStats(panel.build && panel.build.subStats);
  // 非满配面板为可选项：攻略数据带 graduationPanelAlt 才渲染第二个面板（词条数由需求方人为界定）
  const alt = strategy.graduationPanelAlt;
  const altStats =
    alt && Array.isArray(alt.totals)
      ? formatSubStats(alt.build && alt.build.subStats)
      : null;
  const altBlock =
    alt && Array.isArray(alt.totals)
      ? `<h4 class="guide-block__subtitle">${escapeHtml(
          formatPanelTitle(alt.title || '非满配毕业面板', altStats),
        )}</h4>
${graduationPanelHtml(strategy, alt)}`
      : '';
  return `<div class="guide-block" id="guide-graduation">
    <h3 class="guide-block__title">毕业面板</h3>
    ${panel.title ? `<h4 class="guide-block__subtitle">${escapeHtml(formatPanelTitle(panel.title, panelStats))}</h4>` : ''}
    ${graduationPanelHtml(strategy, panel)}
    ${altBlock}
  </div>`;
}

function teamHtml(strategy) {
  const groups = (strategy.teams || [])
    .map((team) => {
      const cards = (team.members || [])
        .map(
          (member) => `<div class="team-card">
            <div class="team-card__top">
              <div class="team-card__agent">
                ${member.avatar ? `<img class="team-card__avatar" src="${escapeHtml(member.avatar)}" alt="${escapeHtml(member.name)}头像" loading="lazy" onerror="this.style.display='none'" />` : ''}
                <p class="team-card__name">${escapeHtml(member.name)}</p>
              </div>
              <div class="team-card__text">
                <span class="team-card__role">${escapeHtml(member.role)}</span>
                <p class="team-card__note">${noteHtml(member.note)}</p>
              </div>
            </div>
            ${member.set4 && member.set4.length ? `<div class="team-card__drives">
              <span class="team-card__drives-label">4 件套</span>
              <div class="team-card__set-list">
                ${member.set4
                  .map(
                    (set) => `<span class="team-card__set" title="${escapeHtml(set.name || '')}">
                      ${set.icon ? `<img class="team-card__set4-icon" src="${escapeHtml(set.icon)}" alt="${escapeHtml(set.name || '')}图标" loading="lazy" onerror="this.style.display='none'" />` : ''}
                      <span class="team-card__set4-name">${escapeHtml(set.name || '')}</span>
                    </span>`,
                  )
                  .join('')}
              </div>
            </div>` : ''}
          </div>`,
        )
        .join('');
      return `<div class="team-group">
        <h4 class="team-group__title">${escapeHtml(team.name)}</h4>
        <div class="team-grid">${cards || '<p class="para">暂无数据</p>'}</div>
      </div>`;
    })
    .join('');
  return `<div class="guide-block" id="guide-team">
    <h3 class="guide-block__title">队伍推荐</h3>
    ${groups || '<p class="para">暂无数据</p>'}
  </div>`;
}

function textGuideHtml(strategy) {
  const blocks = (strategy.textGuide || [])
    .map(
      (block) => `<div class="text-block">
        <h4 class="text-block__title">${escapeHtml(block.title)}</h4>
        ${(block.lines || []).map((line) => `<p class="para">${lineHtml(line)}</p>`).join('')}
      </div>`,
    )
    .join('');
  return `<div class="guide-block" id="guide-text">
    <h3 class="guide-block__title">文字攻略</h3>
    ${blocks || '<p class="para">暂无数据</p>'}
  </div>`;
}

function strategyHtml(guide, slug) {
  const strategy = guide.strategy;
  if (!strategy) {
    return `<section id="guide" class="section reveal" aria-labelledby="guide-title">
      ${sectionHeadHtml('01', '攻略', '技能加点优先级 · 音擎推荐 · 驱动盘推荐 · 毕业面板 · 队伍推荐 · 文字攻略', 'guide')}
      <div class="guide-block"><p class="para">未找到攻略数据文件（data/${escapeHtml(slug)}.strategy.json）。</p></div>
    </section>`;
  }
  return `<section id="guide" class="section reveal" aria-labelledby="guide-title">
    ${sectionHeadHtml('01', '攻略', '关键命座推荐 · 技能加点优先级 · 音擎推荐 · 驱动盘推荐 · 毕业面板 · 队伍推荐 · 文字攻略', 'guide')}
    <div class="guide-grid">
      ${cinemaPriorityHtml(strategy)}
      ${skillPriorityHtml(strategy)}
      ${weaponHtml(strategy)}
      ${drivesHtml(strategy)}
      ${graduationHtml(strategy)}
      ${teamHtml(strategy)}
      ${textGuideHtml(strategy)}
    </div>
  </section>`;
}

/** hex 颜色与白色/黑色按比例混合（生成浅底色、深文字色）。 */
function attributeShade(hex, ratio, toWhite) {
  const value = parseInt(hex.replace('#', ''), 16);
  const r = (value >> 16) & 255;
  const g = (value >> 8) & 255;
  const b = value & 255;
  const target = toWhite ? 255 : 0;
  const mix = (channel) => Math.round(channel * (1 - ratio) + target * ratio);
  return `#${[mix(r), mix(g), mix(b)].map((c) => c.toString(16).padStart(2, '0')).join('')}`;
}

/** 按属性色的相对亮度选择黑/白前景，避免亮色上的白字对比度不足。 */
function contrastText(hex) {
  const value = parseInt(String(hex).replace('#', ''), 16);
  if (!Number.isFinite(value)) return '#101318';
  const channel = (shift) => {
    const c = ((value >> shift) & 255) / 255;
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  };
  const luminance = 0.2126 * channel(16) + 0.7152 * channel(8) + 0.0722 * channel(0);
  const blackContrast = (luminance + 0.05) / 0.05;
  const whiteContrast = 1.05 / (luminance + 0.05);
  return blackContrast >= whiteContrast ? '#101318' : '#ffffff';
}

function render(guide, slug, basePanel) {
  app.dataset.state = 'ready';
  const background =
    (guide.strategy && guide.strategy.background) ||
    (guide.assets && guide.assets.background) ||
    '';
  if (background) {
    app.style.setProperty('--strategy-bg', `url("${background}")`);
  } else {
    app.style.removeProperty('--strategy-bg');
  }
  app.innerHTML = `${background ? '<div class="page-bg" aria-hidden="true"></div>' : ''}
    <div class="layout">
      ${sidebarHtml(guide, slug)}
      <div class="content">
        ${heroHtml(guide)}
        <main class="page" id="strategy-main" tabindex="-1">
          ${strategyHtml(guide, slug)}
          ${basePanelHtml(basePanel)}
          ${skillsHtml(guide)}
          ${cinemaHtml(guide)}
        </main>
        ${footerHtml(guide)}
      </div>
    </div>
    <button class="to-top" type="button" aria-label="返回顶部">
      <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M12 19V5M5 12l7-7 7 7"/></svg>
    </button>`;
  // 属性色（凛刃等）作为全局强调色：模块编号方块、属性色牌、左侧导航共用，保持风格统一
  const attribute = (guide.profile && guide.profile.attribute) || '';
  const attributeColor = ATTRIBUTE_TILE_COLORS[attribute] || '#9aa3b2';
  app.style.setProperty('--attr-color', attributeColor);
  app.style.setProperty('--attr-color-soft', attributeShade(attributeColor, 0.9, true));
  app.style.setProperty('--attr-color-text', attributeShade(attributeColor, 0.35, false));
  app.style.setProperty('--attr-on-color', contrastText(attributeColor));
  bindTablist({
    tablistSelector: '.skill-cat--tabbed .move-tabs',
    tabSelector: '.move-tab',
    panelSelector: '.move-panel',
  });
  bindTablist({
    tablistSelector: '.drive-tabs',
    tabSelector: '.drive-tab',
    panelSelector: '.drive-panel',
  });
  cleanups.push(bindSidebar());
  cleanups.push(bindScrollSpy());
  cleanups.push(bindReveal());
  cleanups.push(bindToTop());
  bindSaveButtons(guide);
}

