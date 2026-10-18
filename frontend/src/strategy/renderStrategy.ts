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

export interface RenderStrategyOptions {
  root: HTMLElement;
  guide: Record<string, unknown>;
  slug: string;
  onTitle?: (title: string) => void;
}

let app: HTMLElement;
let cleanups: Array<() => void> = [];

export function renderStrategy({ root, guide, slug, onTitle }: RenderStrategyOptions): () => void {
  cleanups.forEach((fn) => fn());
  cleanups = [];
  app = root;
  render(guide, slug);
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

/** 渲染备注说明：支持字符串或字符串数组，数组项之间用 <br> 换行。 */
function noteHtml(note) {
  if (!note) return '';
  const items = Array.isArray(note) ? note : [note];
  return items.map((item) => escapeHtml(String(item))).join('<br>');
}

/** 本地路径优先，缺失（如图片下载失败）时回退远程 URL。 */
function asset(assets, key) {
  if (!assets) return '';
  return assets[key] || assets[`${key}Remote`] || '';
}

/* ---------------------------------------------------------------- 截图与下载（保存攻略 / 保存一图流） */

/** 加载 html2canvas（CDN，仅首次请求，后续缓存实例）。 */
let html2canvasPromise = null;
function loadHtml2canvas() {
  if (window.html2canvas) return Promise.resolve(window.html2canvas);
  if (html2canvasPromise) return html2canvasPromise;
  html2canvasPromise = new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = 'https://unpkg.com/html2canvas@1.4.1/dist/html2canvas.min.js';
    script.onload = () => resolve(window.html2canvas);
    script.onerror = () => reject(new Error('加载 html2canvas 失败'));
    document.head.appendChild(script);
  });
  return html2canvasPromise;
}

/** 等待字体就绪（最多 5 秒），再截图；图片加载交由 html2canvas 内部处理，避免某张图永不就绪导致截图挂起。 */
async function waitImagesReady() {
  const timeout = new Promise((resolve) => setTimeout(resolve, 5000, 'timeout'));
  await Promise.race([timeout, 'fonts' in document ? document.fonts.ready : Promise.resolve()]);
}

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

/** 截取目标元素并下载为图片。 */
async function captureAndDownload(targetEl, filename) {
  if (!targetEl) throw new Error('未找到截图目标区域');
  const html2canvas = await loadHtml2canvas();
  await waitImagesReady();
  const canvas = await html2canvas(targetEl, {
    scale: 1,
    useCORS: false,
    scrollX: 0,
    scrollY: 0,
    windowWidth: targetEl.scrollWidth,
    windowHeight: targetEl.scrollHeight,
    logging: false,
  });
  if (!canvas) throw new Error('html2canvas 未返回画布');
  return new Promise((resolve, reject) => {
    canvas.toBlob((blob) => {
      if (!blob) return reject(new Error('生成图片失败'));
      downloadBlob(blob, filename);
      resolve();
    }, 'image/png');
  });
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
  const professionIcon = icons.profession || (ROLE_ICON_MAP[roleTag] ? `/images/icons/${ROLE_ICON_MAP[roleTag]}.png` : '');
  return `<p class="hero__icons">
    ${attributeIcon}
    ${professionIcon ? `<img class="hero-icon" src="${escapeHtml(professionIcon)}" alt="特性图标" title="特性 · ${escapeHtml(roleTag)}" onerror="this.style.display='none'" />` : ''}
    ${icons.grade ? `<img class="hero-icon" src="${escapeHtml(icons.grade)}" alt="等级图标" title="${escapeHtml(profile.grade || '')} 级" onerror="this.style.display='none'" />` : ''}
    ${icons.title ? `<span class="hero-title-badge" title="称号 · ${escapeHtml(profile.factionTitle || '')}"><img src="${escapeHtml(icons.title)}" alt="称号图标" onerror="this.parentElement.style.display='none'" /></span>` : ''}
  </p>`;
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
          <h1 class="hero__name">${escapeHtml(profile.name)}</h1>
          ${heroIconsHtml(profile)}
        </div>
        <p class="hero__source">数据来源：<a href="${escapeHtml(meta.source)}" target="_blank" rel="noreferrer">米游社绝区零 WIKI</a>，抓取于 ${escapeHtml(
          meta.scrapedAt ? new Date(meta.scrapedAt).toLocaleString('zh-CN') : '—',
        )}</p>
      </div>
      ${tachie ? `<img class="hero__tachie" src="${escapeHtml(tachie)}" alt="${escapeHtml(profile.name)}立绘" />` : ''}
    </div>
  </header>`;
}

/** 左侧导航栏：四大区块 + 技能六大类子链接 + 移动端目录开关。 */
function sidebarHtml(guide) {
  const sections = [
    { id: 'guide', label: '攻略', index: '01' },
    { id: 'base', label: '基础面板', index: '02' },
    { id: 'skills', label: '技能', index: '03' },
    { id: 'cinema', label: '影画', index: '04' },
  ];
  const skillSublinks = (guide.skills || [])
    .map((skill) => `<a class="sidebar__sublink" href="#skill-${escapeHtml(skill.key)}">${escapeHtml(skill.name)}</a>`)
    .join('');
  const name = (guide.profile && guide.profile.name) || '';
  // 攻略二级菜单（与攻略区块的 id 一一对应；毕业面板视数据存在与否显隐）
  const strategy = guide.strategy;
  const guideSublinks = strategy
    ? [
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
  return `<aside class="sidebar" id="sidebar">
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
      <button class="sidebar__btn" type="button" data-action="save-full">保存一图流</button>
    </div>
    <div class="sidebar__foot">
      <p>数据来源</p>
      <p class="sidebar__foot-source">米游社绝区零 WIKI</p>
    </div>
  </aside>`;
}

/** 一级板块头部带：编号方块 + 标题 + 一句副标题（与左侧导航编号一致）。 */
function sectionHeadHtml(index, title, sub) {
  return `<header class="section__head">
    <span class="section__no">${escapeHtml(index)}</span>
    <div class="section__heading">
      <h2 class="section__title">${escapeHtml(title)}</h2>
      ${sub ? `<p class="section__sub">${escapeHtml(sub)}</p>` : ''}
    </div>
  </header>`;
}

/* 锋御固有属性「锐暴伤害」是局内恒定值（不随等级/突破/配装变化），
   不属于 60 级基础面板的展示范围，基础面板模块过滤掉它。 */
const BASE_PANEL_HIDDEN_LABELS = ['锐暴伤害'];

function basePanelHtml(guide) {
  const fields = (guide.basePanel || [])
    .filter((field) => !BASE_PANEL_HIDDEN_LABELS.includes(field.label))
    .map((field) => {
      const value = Number(field.value).toLocaleString('zh-CN');
      return `<div class="base-field">
        <span class="base-field__label">${escapeHtml(field.label)}</span>
        <span class="base-field__value">${escapeHtml(value)}${escapeHtml(field.unit || '')}</span>
      </div>`;
    })
    .join('');
  return `<section id="base" class="section reveal">
    ${sectionHeadHtml('02', '基础面板', '60 级 · 0 突破 · 不含核心技与配装加成')}
    <p class="section__hint">该面板为晋升需求滑块的初始行与满级行合并结果，与游戏内 60 级（0 突破）基础数据一致。</p>
    <div class="base-panel">${fields || '<p class="para">暂无基础面板数据</p>'}</div>
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

  const panelHtml = (move, index) => `<div class="move-panel${index === 0 ? ' is-active' : ''}" data-panel="${index}">
    <h4 class="move__title">${escapeHtml(move.title)}</h4>
    <div class="move__text">${paragraphsHtml(move.text)}</div>
    ${growthHtml(move)}
  </div>`;

  // 多招式类别：招式 tab + 详情面板的二级选择
  if (moves.length > 1) {
    // tab 标签去掉与类别名重复的前缀（如「普通攻击：」），面板内仍用完整标题
    const prefix = new RegExp(`^${skill.name}[：:]\\s*`);
    const tabLabel = (title) => title.replace(prefix, '');
    const tabs = moves
      .map(
        (move, index) =>
          `<button class="move-tab${index === 0 ? ' is-active' : ''}" type="button" data-move="${index}">${escapeHtml(tabLabel(move.title))}</button>`,
      )
      .join('');
    const panels = moves.map(panelHtml).join('');
    return `<section class="skill-cat skill-cat--tabbed" id="skill-${escapeHtml(skill.key)}">
      ${head}
      <div class="move-tabs" role="tablist">${tabs}</div>
      <div class="move-panels">${panels}</div>
    </section>`;
  }

  // 单招式类别：无 tab bar，直接展示面板
  if (moves.length === 1) {
    return `<section class="skill-cat skill-cat--tabbed" id="skill-${escapeHtml(skill.key)}">
      ${head}
      <div class="move-panels">${moves.map(panelHtml).join('')}</div>
    </section>`;
  }

  return `<section class="skill-cat skill-cat--tabbed" id="skill-${escapeHtml(skill.key)}">
    ${head}
    <div class="move-panels"><p class="para">暂无招式数据</p></div>
  </section>`;
}

function skillsHtml(guide) {
  const skillList = [...(guide.skills || [])].sort(
    (a, b) => SKILL_CATEGORY_ORDER.indexOf(a.key) - SKILL_CATEGORY_ORDER.indexOf(b.key),
  );
  const blocks = skillList.map(skillCatHtml);
  return `<section id="skills" class="section reveal">
    ${sectionHeadHtml('03', '技能', '六大类技能 · 板块内支持按招式二级切换')}
    <p class="section__hint">按普攻 / 闪避 / 支援 / 特殊 / 连携（含终结技）/ 核心技六大类展示；各板块内支持按招式二级切换查看描述，展开「技能详细数据」可查看各等级数值。</p>
    ${blocks.join('')}
  </section>`;
}

/** 绑定普攻板块的招式 tab 切换（事件委托，重渲染后自动失效，无需手动解绑）。 */
function bindSkillTabs() {
  app.querySelectorAll('.skill-cat--tabbed .move-tabs').forEach((bar) => {
    bar.addEventListener('click', (event) => {
      const tab = event.target.closest('.move-tab');
      if (!tab || !bar.contains(tab)) return;
      const cat = tab.closest('.skill-cat');
      const index = tab.dataset.move;
      cat.querySelectorAll('.move-tab').forEach((item) => item.classList.remove('is-active'));
      cat.querySelectorAll('.move-panel').forEach((panel) => panel.classList.remove('is-active'));
      tab.classList.add('is-active');
      const panel = cat.querySelector(`.move-panel[data-panel="${index}"]`);
      if (panel) panel.classList.add('is-active');
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
    links.forEach((link) => link.classList.toggle('is-active', link.getAttribute('href') === currentHref));
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

/** 绑定「保存攻略」/「保存一图流」按钮：截取对应区块并下载。 */
function bindSaveButtons(guide) {
  const actions = app.querySelector('.sidebar__actions');
  if (!actions) return;
  actions.addEventListener('click', async (event) => {
    const btn = event.target.closest('.sidebar__btn');
    if (!btn || !actions.contains(btn)) return;
    const action = btn.dataset.action;
    if (!app || app.dataset.state !== 'ready') return;

    let target;
    let suffix;
    let tempWrapper = null;
    if (action === 'save-guide') {
      const hero = app.querySelector('.hero');
      const guide = app.querySelector('#guide');
      if (!hero || !guide) {
        showTip('截图目标不存在，请刷新页面后重试');
        return;
      }
      // 包含 hero 头部（含属性/职业/评级图标）与 01攻略区块，截图后移除临时包裹元素，
      // 确保不包含左侧导航栏与返回顶部按钮。
      tempWrapper = document.createElement('div');
      // 样式已收窄在 `.strategy-detail` 下；截图副本必须带同一个作用域类，
      // 否则 html2canvas 克隆到 body 后会丢失攻略页样式。
      tempWrapper.className = 'strategy-detail';
      tempWrapper.style.cssText =
        'position:fixed;inset:0;overflow:visible;pointer-events:none;z-index:-1;';
      tempWrapper.appendChild(hero.cloneNode(true));
      tempWrapper.appendChild(guide.cloneNode(true));
      document.body.appendChild(tempWrapper);
      target = tempWrapper;
      suffix = '攻略';
    } else if (action === 'save-full') {
      target = app.querySelector('.content');
      suffix = '一图流';
    } else {
      return;
    }
    if (!target) {
      showTip('截图目标不存在，请刷新页面后重试');
      return;
    }
    btn.disabled = true;
    try {
      await captureAndDownload(target, agentFileName(guide, suffix));
      showTip('已下载：' + agentFileName(guide, suffix));
    } catch (error) {
      showTip('截图下载失败：' + (error && error.message ? error.message : String(error)));
    } finally {
      if (tempWrapper) tempWrapper.remove();
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

  return `<section id="cinema" class="section reveal">
    ${sectionHeadHtml('04', '影画', '影画 1 - 6 · 按命数分组展示 WIKI 展示图')}
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
    .map(
      (group) => `<div class="weapon-card">
        <span class="weapon-card__tier">${escapeHtml(group.tier)}</span>
        <div class="weapon-card__row">
          ${(group.items || [])
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
      </div>`,
    )
    .join('');
  return `<div class="guide-block" id="guide-weapons">
    <h3 class="guide-block__title">音擎推荐</h3>
    <div class="weapon-list">${cards || '<p class="para">暂无数据</p>'}</div>
  </div>`;
}

/**
 * 渲染「首选 / 备选 / 4 件套备选」行。
 * 接受单个套装或数组；**二件套效果文案相同的套装会合并到同一行**——
 * 图标与名称并列、效果文案只显示一次（如 摇摆爵士 / 月光骑士颂 同为能量自动回复 +20%）。
 */
function driveSetRowHtml(sets, prefix) {
  const list = (Array.isArray(sets) ? sets : [sets]).filter(Boolean);
  if (!list.length) return '';
  const groups = [];
  for (const set of list) {
    const label = (set.label || '').trim();
    const hit = groups.find((group) => group.label === label);
    if (hit) {
      hit.sets.push(set);
    } else {
      groups.push({ label, sets: [set] });
    }
  }
  return groups
    .map(
      ({ label, sets: groupSets }) => `<div class="drive-set__row">
      <span class="drive-set__prefix">${escapeHtml(prefix)}</span>
      <div class="drive-set__row-sets">
        ${groupSets
          .map(
            (set) => `<span class="drive-set__unit">
          ${set.icon ? `<img class="drive-set__icon" src="${escapeHtml(set.icon)}" alt="${escapeHtml(set.name || '')}图标" loading="lazy" onerror="this.style.display='none'" />` : ''}
          <span class="drive-set__name">${escapeHtml(set.name || '')}</span>
        </span>`,
          )
          .join('')}
        <span class="drive-set__label">${escapeHtml(label)}</span>
      </div>
    </div>`,
    )
    .join('');
}

/**
 * 渲染 4 件套卡。
 *
 * `set4` 可以是单个对象，也可以是**数组**：多个 4 件套共用同一套 2 件套 /
 * 主词条 / 副词条时（如柚叶的月光骑士颂 / 静听嘉音 / 自由蓝调，2 件套都是
 * 法厄同之歌），把它们合并进同一个方案，每个 4 件套各占一条并附 `scene`
 * 使用场景备注——否则主词条表与副词条链要整段重复三遍。
 * 单套装时走的是同一条渲染路径，产出的 DOM 与旧版逐字符一致。
 */
function set4CardHtml(set4) {
  const list = (Array.isArray(set4) ? set4 : [set4]).filter(Boolean);
  if (!list.length) return '';
  const block = (set) => `      <div class="drive-set__row">
        ${set.icon ? `<img class="drive-set__icon" src="${escapeHtml(set.icon)}" alt="${escapeHtml(set.name || '')}图标" loading="lazy" onerror="this.style.display='none'" />` : ''}
        <div class="drive-set__meta">
          <p class="drive-set__name">${escapeHtml(set.name || '')}</p>
          <div class="drive-set__effects">
            ${set.label ? `<div class="drive-set__effect2"><span class="drive-set__effect2-tag">二件套</span><p>${escapeHtml(set.label)}</p></div>` : ''}
            ${set.effect4 ? `<div class="drive-set__effect4"><span class="drive-set__effect4-tag">四件套</span><p>${escapeHtml(set.effect4)}</p></div>` : ''}${set.scene ? `
            <p class="drive-set__scene"><span class="drive-set__scene-tag">适用</span><span>${escapeHtml(set.scene)}</span></p>` : ''}
          </div>
        </div>
      </div>
      ${set.alt4 ? driveSetRowHtml(set.alt4, '备选') : ''}`;
  // 多个 4 件套之间插一条分隔线；只有一个时不插，输出与旧模板逐字符一致
  const blocks = list
    .map(block)
    .join(`
      <div class="drive-set__sep" aria-hidden="true"></div>
`);
  // ${blocks} 必须顶格：块内自带 6 空格缩进，占位符若也有缩进，
  // 单套装的首行就会比旧模板多出一段空白（DOM 相同但不再是逐字符一致）。
  return `<div class="drive-set">
      <span class="drive-set__slot">4 件套</span>
${blocks}
    </div>`;
}

/** 单个驱动盘推荐方案：4 件套卡 + 2 件套卡 + 主词条表 + 副词条链。 */
function driveBuildHtml(build) {
  const set4 = build.set4;
  const set2 = build.set2;
  const setCards = [];
  if (set4) {
    setCards.push(set4CardHtml(set4));
  }
  if (set2) {
    // main / alt 均可为单对象或数组（多套装并列；效果文案相同的会在行内合并）
    const asList = (value) => (Array.isArray(value) ? value : value ? [value] : []);
    // 整组一次性交给 driveSetRowHtml，由它按效果文案分组合并
    const rows = [driveSetRowHtml(asList(set2.main), '首选'), driveSetRowHtml(asList(set2.alt), '备选')].join('');
    setCards.push(`<div class="drive-set">
      <span class="drive-set__slot">2 件套</span>
      ${rows}
    </div>`);
  }
  const mains = (build.mainStats || [])
    .map(
      (item) => `<tr>
        <th scope="row" class="drive-main__slot">${escapeHtml(item.slot)}</th>
        <td class="drive-main__stat">${escapeHtml(item.main)}</td>
        <td class="drive-main__alt">${escapeHtml(item.alt)}</td>
      </tr>`,
    )
    .join('');
  // 副词条按「> / ≈」连接符排序（≈ 表示同档约等于，> 表示严格大于），不用数字序号
  const subs = (build.subPriority || [])
    .map((item) => {
      const label = typeof item === 'string' ? item : item.label;
      const next = typeof item === 'string' ? '' : item.next || '';
      return `<span class="sub-chip">${escapeHtml(label)}</span>${next ? `<span class="sub-op">${escapeHtml(next)}</span>` : ''}`;
    })
    .join('');
  // 方案名缺省时用套装组合自动生成，追加方案不强制命名。
  // set4 可能是数组（多个 4 件套合并成一个方案），名称用「 / 」连接。
  const set2Main = Array.isArray(set2.main) ? set2.main : set2.main ? [set2.main] : [];
  const set4List = Array.isArray(set4) ? set4 : set4 ? [set4] : [];
  const fallbackName = [
    set4List.length ? `${set4List.map((set) => set.name).filter(Boolean).join(' / ')} 4 件套` : '',
    set2Main.length ? `${set2Main.map((set) => set.name).join(' / ')} 2 件套` : '',
  ]
    .filter(Boolean)
    .join(' + ');
  return `<div class="drive-group">
    <h4 class="drive-group__title">${escapeHtml(build.name || fallbackName || '推荐配装')}</h4>
    ${build.note ? `<p class="drive-group__note">${noteHtml(build.note)}</p>` : ''}
    <div class="drive-sets">${setCards.join('')}</div>
    <h5 class="guide-block__subtitle">主词条（4 / 5 / 6 号位）</h5>
    <table class="drive-main">
      <thead><tr><th>部位</th><th>首选</th><th>备选</th></tr></thead>
      <tbody>${mains}</tbody>
    </table>
    <h5 class="guide-block__subtitle">副词条优先级</h5>
    <p class="sub-prio">${subs || '暂无数据'}</p>
  </div>`;
}

function drivesHtml(strategy) {
  // 多方案数组；兼容旧的单个 drives 对象（迁移前的手改数据）
  const builds = Array.isArray(strategy.driveBuilds)
    ? strategy.driveBuilds
    : strategy.drives
      ? [strategy.drives]
      : [];
  return `<div class="guide-block" id="guide-drives">
    <h3 class="guide-block__title">驱动盘推荐</h3>
    ${builds.length ? builds.map(driveBuildHtml).join('') : '<p class="para">暂无数据</p>'}
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

/** 在驱动盘推荐（4 件套单值或数组、2 件套 main/alt）里按套装名找图标。 */
function findDiscIcon(strategy, name) {
  for (const build of strategy.driveBuilds || []) {
    for (const set of [...asList(build.set4), ...asList((build.set2 || {}).main), ...asList((build.set2 || {}).alt)]) {
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
  const attribute = (strategy && strategy.profile && strategy.profile.attribute) || '';
  const attributeColor = ATTRIBUTE_TILE_COLORS[attribute] || '#9aa3b2';
  const build = Object.entries(panel.build || {})
    .filter(([key]) => !['agent', 'weapon', 'core'].includes(key))
    .map(([key, value]) => {
      const lookup = BUILD_ICON_FIELDS[key];
      const icon = lookup ? lookup(strategy, String(value)) : '';
      // 图标加载失败就退化成纯文字，不影响这一行的信息
      const iconHtml = icon
        ? `<img class="build-row__icon" src="${escapeHtml(icon)}" alt="" loading="lazy" onerror="this.style.display='none'" />`
        : '';
      return `<div class="build-row"><dt style="background:${escapeHtml(attributeColor)};color:#000;border-color:${escapeHtml(attributeColor)}">${escapeHtml(BUILD_LABELS[key] || key)}</dt><dd>${iconHtml}${escapeHtml(value)}</dd></div>`;
    })
    .join('');
  return `<div class="base-panel base-panel--graduation">${totals}</div>
    <dl class="build-spec">${build}</dl>`;
}

function graduationHtml(strategy) {
  const panel = strategy.graduationPanel;
  if (!panel || !Array.isArray(panel.totals)) return '';
  // 非满配面板为可选项：攻略数据带 graduationPanelAlt 才渲染第二个面板（词条数由需求方人为界定）
  const alt = strategy.graduationPanelAlt;
  const altBlock =
    alt && Array.isArray(alt.totals)
      ? `<h4 class="guide-block__subtitle">${escapeHtml(alt.title || '非满配毕业面板')}</h4>
${graduationPanelHtml(strategy, alt)}`
      : '';
  return `<div class="guide-block" id="guide-graduation">
    <h3 class="guide-block__title">毕业面板</h3>
    ${panel.title ? `<h4 class="guide-block__subtitle">${escapeHtml(panel.title)}</h4>` : ''}
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

function strategyHtml(guide) {
  const strategy = guide.strategy;
  if (!strategy) {
    return `<section id="guide" class="section reveal">
      ${sectionHeadHtml('01', '攻略', '技能加点优先级 · 音擎推荐 · 驱动盘推荐 · 毕业面板 · 队伍推荐 · 文字攻略')}
      <div class="guide-block"><p class="para">未找到攻略数据文件（data/roxy.strategy.json）。</p></div>
    </section>`;
  }
  return `<section id="guide" class="section reveal">
    ${sectionHeadHtml('01', '攻略', '技能加点优先级 · 音擎推荐 · 驱动盘推荐 · 毕业面板 · 队伍推荐 · 文字攻略')}
    <div class="guide-grid">
      ${skillPriorityHtml(strategy)}
      ${weaponHtml(strategy)}
      ${drivesHtml(strategy)}
    </div>
    ${graduationHtml(strategy)}
    ${teamHtml(strategy)}
    ${textGuideHtml(strategy)}
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

function render(guide, slug) {
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
      ${sidebarHtml(guide)}
      <div class="content">
        ${heroHtml(guide)}
        <main class="page">
          ${strategyHtml(guide)}
          ${basePanelHtml(guide)}
          ${skillsHtml(guide)}
          ${cinemaHtml(guide)}
          ${footerHtml(guide)}
        </main>
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
  bindSkillTabs();
  cleanups.push(bindSidebar());
  cleanups.push(bindScrollSpy());
  cleanups.push(bindReveal());
  cleanups.push(bindToTop());
  bindSaveButtons(guide);
}

