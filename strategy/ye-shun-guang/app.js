'use strict';

/**
 * 代理人攻略原型页渲染逻辑。
 *
 * 页面只做一件事：把 `data/ye-shun-guang.json`（由 scrape_agent_guide.py 生成）
 * 渲染成响应式攻略页。全部 DOM 由本文件构建，不依赖任何框架与构建步骤。
 *
 * 数据契约（与抓取脚本输出逐字对应）：
 *   meta     抓取元信息（agentId / 来源 / 时间）
 *   profile  姓名 / 属性 / 职业 / 评级 / 称号 / 自定义字段 / 简介
 *   assets   本地图片相对路径 + 同名 *Remote 远程兜底 URL
 *   skills   六大类技能（key: basic/dodge/assist/special/chain/core），
 *            每类含 moves[]：title / text / growth[](1-16 级或 A-F 级详细数据)
 *   cinemas  影画 1-6 层：level / name / text
 */

const DATA_URL = 'data/ye-shun-guang.json';
const STRATEGY_URL = 'data/ye-shun-guang.strategy.json';

const app = document.getElementById('app');
document.addEventListener('DOMContentLoaded', init);

async function init() {
  try {
    const [guideResponse, strategyResponse] = await Promise.all([
      fetch(DATA_URL, { cache: 'no-store' }),
      fetch(STRATEGY_URL, { cache: 'no-store' }),
    ]);
    if (!guideResponse.ok) {
      throw new Error(`HTTP ${guideResponse.status}`);
    }
    const guide = await guideResponse.json();
    // 攻略编辑内容（加点/推荐/毕业面板/队伍/文字攻略）单独一份文件，
    // 缺失时不阻塞主页面，只隐藏该区块。
    guide.strategy = strategyResponse.ok ? await strategyResponse.json() : null;
    render(guide);
  } catch (error) {
    renderError(error);
  }
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

/** 本地路径优先，缺失（如图片下载失败）时回退远程 URL。 */
function asset(assets, key) {
  if (!assets) return '';
  return assets[key] || assets[`${key}Remote`] || '';
}

/**
 * 纯文本 -> 段落 HTML。空行视为分段（影画的「效果 / 剧情」之间用空行隔开），
 * 用 .para--gap 呈现额外间距；[方括号] 术语高亮。
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
    const highlighted = escapeHtml(line).replace(/\[([^\[\]]+)\]/g, '<em class="term">[$1]</em>');
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

/** 属性色牌的底色（WIKI 未公开属性图标，按各属性代表色降级呈现）。 */
const ATTRIBUTE_TILE_COLORS = {
  电: '#a06fc4',
  火: '#c85a50',
  冰: '#5c93c4',
  风: '#6aa876',
  以太: '#c2a05a',
  物理: '#9aa3b2',
  烈霜: '#5fb6c4',
  玄墨: '#6e7686',
  凛刃: '#8598b4',
  流明: '#b3a583',
};

function heroIconsHtml(profile) {
  const icons = (profile && profile.icons) || {};
  const attribute = profile ? profile.attribute : '';
  const attributeIcon = icons.attribute
    ? `<img class="hero-icon hero-icon--image" src="${escapeHtml(icons.attribute)}" alt="属性图标" title="属性 · ${escapeHtml(attribute)}" onerror="this.style.display='none'" />`
    : `<span class="hero-icon hero-icon--attribute" title="属性 · ${escapeHtml(attribute)}">${escapeHtml(attribute)}</span>`;
  return `<p class="hero__icons">
    ${attributeIcon}
    ${icons.profession ? `<img class="hero-icon" src="${escapeHtml(icons.profession)}" alt="特性图标" title="特性 · ${escapeHtml(profile.roleTag || '')}" onerror="this.style.display='none'" />` : ''}
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
        { id: 'guide-weapons', label: '武器推荐' },
        { id: 'guide-drives', label: '驱动盘推荐' },
        ...(strategy.graduationPanel && strategy.graduationPanel.totals ? [{ id: 'guide-graduation', label: '满配毕业面板' }] : []),
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
              <span class="sidebar__label">${section.label}</span>
            </a>${sub}
          </div>`;
        })
        .join('')}
    </nav>
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

function basePanelHtml(guide) {
  const fields = (guide.basePanel || [])
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
  if (!sidebar || !toggle) return;
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
}

/** 滚动侦测：按当前可见区块高亮左侧导航（子区块优先；触底时兜底高亮最后一个目标）。 */
function bindScrollSpy() {
  const links = [...app.querySelectorAll('.sidebar__link[data-spy], .sidebar__sublink')];
  if (links.length === 0 || !('IntersectionObserver' in window)) return;
  const targets = [...new Set(links.map((link) => app.querySelector(link.getAttribute('href'))))].filter(Boolean);
  if (targets.length === 0) return;
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
  window.addEventListener(
    'scroll',
    () => {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(() => {
        paint();
        ticking = false;
      });
    },
    { passive: true },
  );
  paint();
}

/** 入场动效：主区块进入视口时淡入上移（一次性，尊重减少动效偏好）。 */
function bindReveal() {
  const items = [...app.querySelectorAll('.reveal')];
  const showAll = () => items.forEach((item) => item.classList.add('is-visible'));
  const reduceMotion =
    typeof window.matchMedia === 'function' && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduceMotion || !('IntersectionObserver' in window)) {
    showAll();
    return;
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
}

/** 返回顶部按钮：滚动超过一屏后浮现。 */
function bindToTop() {
  const button = app.querySelector('.to-top');
  if (!button) return;
  const onScroll = () => button.classList.toggle('is-visible', window.scrollY > 480);
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
  button.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
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
        ${group.note ? `<p class="weapon-card__note">${escapeHtml(group.note)}</p>` : ''}
      </div>`,
    )
    .join('');
  return `<div class="guide-block" id="guide-weapons">
    <h3 class="guide-block__title">武器推荐</h3>
    <div class="weapon-list">${cards || '<p class="para">暂无数据</p>'}</div>
  </div>`;
}

function driveSetRowHtml(set, prefix) {
  return `<div class="drive-set__row">
    <span class="drive-set__prefix">${escapeHtml(prefix)}</span>
    ${set.icon ? `<img class="drive-set__icon" src="${escapeHtml(set.icon)}" alt="${escapeHtml(set.name || '')}图标" loading="lazy" onerror="this.style.display='none'" />` : ''}
    <div class="drive-set__meta">
      <p class="drive-set__name">${escapeHtml(set.name || '')}</p>
      <span class="drive-set__label">${escapeHtml(set.label)}</span>
    </div>
  </div>`;
}

function drivesHtml(strategy) {
  const drives = strategy.drives || {};
  const set4 = drives.set4;
  const set2 = drives.set2;
  const setCards = [];
  if (set4) {
    setCards.push(`<div class="drive-set">
      <span class="drive-set__slot">4 件套</span>
      <div class="drive-set__row">
        ${set4.icon ? `<img class="drive-set__icon" src="${escapeHtml(set4.icon)}" alt="${escapeHtml(set4.name || '')}图标" loading="lazy" onerror="this.style.display='none'" />` : ''}
        <div class="drive-set__meta">
          <p class="drive-set__name">${escapeHtml(set4.name || '')}</p>
          <span class="drive-set__label">二件套：${escapeHtml(set4.label)}</span>
        </div>
      </div>
      ${set4.effect4 ? `<div class="drive-set__effect4"><span class="drive-set__effect4-tag">四件套</span><p>${escapeHtml(set4.effect4)}</p></div>` : ''}
    </div>`);
  }
  if (set2) {
    const rows = [set2.main ? driveSetRowHtml(set2.main, '首选') : '', set2.alt ? driveSetRowHtml(set2.alt, '备选') : ''].join('');
    setCards.push(`<div class="drive-set">
      <span class="drive-set__slot">2 件套</span>
      ${rows}
    </div>`);
  }
  const mains = (drives.mainStats || [])
    .map(
      (item) => `<tr>
        <th scope="row" class="drive-main__slot">${escapeHtml(item.slot)}</th>
        <td class="drive-main__stat">${escapeHtml(item.main)}</td>
        <td class="drive-main__alt">${escapeHtml(item.alt)}</td>
      </tr>`,
    )
    .join('');
  // 副词条按「> / ≈」连接符排序（≈ 表示同档约等于，> 表示严格大于），不用数字序号
  const subs = (drives.subPriority || [])
    .map((item) => {
      const label = typeof item === 'string' ? item : item.label;
      const next = typeof item === 'string' ? '' : item.next || '';
      return `<span class="sub-chip">${escapeHtml(label)}</span>${next ? `<span class="sub-op">${escapeHtml(next)}</span>` : ''}`;
    })
    .join('');
  return `<div class="guide-block" id="guide-drives">
    <h3 class="guide-block__title">驱动盘推荐</h3>
    <div class="drive-sets">${setCards.join('')}</div>
    <h4 class="guide-block__subtitle">主词条（4 / 5 / 6 号位）</h4>
    <table class="drive-main">
      <thead><tr><th>部位</th><th>首选</th><th>备选</th></tr></thead>
      <tbody>${mains}</tbody>
    </table>
    <h4 class="guide-block__subtitle">副词条优先级</h4>
    <p class="sub-prio">${subs || '暂无数据'}</p>
  </div>`;
}

/** 毕业配装说明的键名 -> 展示文案。 */
const BUILD_LABELS = {
  agent: '角色',
  weapon: '武器',
  core: '核心技',
  set4: '4 件套',
  set2: '2 件套',
  mainStats: '主词条',
  subStats: '副词条',
};

function graduationHtml(strategy) {
  const panel = strategy.graduationPanel;
  if (!panel || !Array.isArray(panel.totals)) return '';
  const totals = panel.totals
    .map(
      (field) => `<div class="base-field">
        <span class="base-field__label">${escapeHtml(field.label)}</span>
        <span class="base-field__value">${escapeHtml(Number(field.value).toLocaleString('zh-CN'))}${escapeHtml(field.unit || '')}</span>
      </div>`,
    )
    .join('');
  const build = Object.entries(panel.build || {})
    .map(
      ([key, value]) =>
        `<div class="build-row"><dt>${escapeHtml(BUILD_LABELS[key] || key)}</dt><dd>${escapeHtml(value)}</dd></div>`,
    )
    .join('');
  return `<div class="guide-block" id="guide-graduation">
    <h3 class="guide-block__title">满配毕业面板</h3>
    <div class="base-panel base-panel--graduation">${totals}</div>
    <dl class="build-spec">${build}</dl>
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
                <p class="team-card__note">${escapeHtml(member.note)}</p>
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
        ${(block.lines || []).map((line) => `<p class="para">${escapeHtml(line)}</p>`).join('')}
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
      ${sectionHeadHtml('01', '攻略', '技能加点优先级 · 武器推荐 · 驱动盘推荐 · 毕业面板 · 队伍推荐 · 文字攻略')}
      <div class="guide-block"><p class="para">未找到攻略数据文件（data/ye-shun-guang.strategy.json）。</p></div>
    </section>`;
  }
  return `<section id="guide" class="section reveal">
    ${sectionHeadHtml('01', '攻略', '技能加点优先级 · 武器推荐 · 驱动盘推荐 · 毕业面板 · 队伍推荐 · 文字攻略')}
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

function render(guide) {
  app.dataset.state = 'ready';
  app.innerHTML = `<div class="layout">
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
  document.title = `代理人攻略 · ${(guide.profile && guide.profile.name) || ''}`;
  // 属性色（凛刃等）作为全局强调色：模块编号方块、属性色牌、左侧导航共用，保持风格统一
  const attribute = (guide.profile && guide.profile.attribute) || '';
  const attributeColor = ATTRIBUTE_TILE_COLORS[attribute] || '#9aa3b2';
  app.style.setProperty('--attr-color', attributeColor);
  app.style.setProperty('--attr-color-soft', attributeShade(attributeColor, 0.9, true));
  app.style.setProperty('--attr-color-text', attributeShade(attributeColor, 0.35, false));
  bindSkillTabs();
  bindSidebar();
  bindScrollSpy();
  bindReveal();
  bindToTop();
}

function renderError(error) {
  app.dataset.state = 'error';
  app.innerHTML = `<div class="boot boot--error">
    <p class="boot__title">无法加载攻略数据</p>
    <p class="boot__text">${escapeHtml(error && error.message ? error.message : String(error))}</p>
    <ol class="boot__hint">
      <li>先在仓库根运行 <code>python .github/skills/agent-strategy/scripts/scrape_agent_guide.py</code> 生成 <code>data/ye-shun-guang.json</code>；</li>
      <li>本页由主应用挂载：启动前端 <code>npm run dev --prefix frontend</code>，经 <code>/strategy</code> 选择页进入；</li>
      <li>数据齐全才会渲染；<code>data/ye-shun-guang.json</code> 缺失时页面停在加载态。</li>
    </ol>
  </div>`;
}
