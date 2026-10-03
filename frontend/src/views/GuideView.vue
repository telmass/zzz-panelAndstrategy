<script setup lang="ts">
import { BackToLauncher } from '@/components/layout';
import { GuideAttrGrid, GuideCallout, GuideSection, GuideTable } from '@/components/guide';

/**
 * 面板计算方式学习指南。
 *
 * 正文迁自 legacy/pages/guide.html（迁移第 5 步第 21 条）。原文是自带一整段
 * 内联样式的静态长文；这里把样式收进 components.css 的「指南页」区块，
 * 重复出现的四类结构抽成 components/guide/ 下的展示组件，
 * 文字与数值一字未改，包括原文自身的两处笔误：
 *   - 攻防血第 4 个步骤框标题写作「第三步」（原文如此）
 *   - 该框的 class 是 step4，而原文 CSS 只定义了 step1~3，故它按默认样式渲染
 */

/** 「基础面板」属性卡片。 */
const BASE_ATTRS = [
  { label: '生命值', value: '7673' },
  { label: '攻击力', value: '888' },
  { label: '防御力', value: '612' },
  { label: '冲击力', value: '93' },
  { label: '暴击率', value: '19.4%' },
  { label: '暴击伤害', value: '50%' },
  { label: '异常掌控', value: '94' },
  { label: '异常精通', value: '93' },
  { label: '穿透率', value: '0%' },
  { label: '能量自动回复', value: '1.2' },
  { label: '增伤', value: '0%' },
  { label: '穿透值', value: '0' },
];

/** 「武器加成」属性卡片。 */
const WEAPON_ATTRS = [
  { label: '基础攻击力', value: '713' },
  { label: '基础防御力', value: '0' },
  { label: '副词条：暴击率', value: '24%' },
];

/** 文末「最终面板一览」卡片。 */
const FINAL_ATTRS = [
  { label: '生命值', value: '10781.4' },
  { label: '攻击力', value: '3066' },
  { label: '防御力', value: '913' },
  { label: '暴击率', value: '72.2%' },
  { label: '暴击伤害', value: '155.6%' },
  { label: '增伤', value: '10%' },
  { label: '穿透率', value: '24%' },
  { label: '穿透值', value: '9' },
  { label: '冲击力', value: '93' },
  { label: '异常掌控', value: '94' },
  { label: '异常精通', value: '102' },
  { label: '能量自动回复', value: '1.2' },
];
</script>

<template>
  <BackToLauncher />

  <main class="container page-with-back guide">
    <h1>📊 面板计算方式学习指南</h1>
    <p class="subtitle">从零搞懂角色面板是怎么算出来的</p>

    <!-- 快速理解 -->
    <div class="guide-quick">
      <h3 class="guide-quick__title">⚡ 30秒快速理解</h3>
      <ul>
        <li>
          <strong>面板 = 6大模块加起来算</strong>：基础 + 武器 + 核心 + 驱动盘 + 2件套 → 最终面板
        </li>
        <li><strong>先乘后加的有6种</strong>：攻防血（+固定值）+ 冲异能（无固定值）→ 基础值 × (1 + 百分比)</li>
        <li><strong>纯加法的有5种</strong>：双爆/增伤/穿透率/穿透值/异常精通 → 所有来源直接堆加</li>
        <li><strong>核心要注意</strong>：基础值部分算在“基础面板”里，百分比部分单独算</li>
      </ul>
    </div>

    <!-- 示例角色介绍 -->
    <div class="guide-char">
      <div class="guide-char__avatar">🔥</div>
      <div class="guide-char__body">
        <h3>示例角色：[11号]夏潾</h3>
        <p>强攻系代理人 · 火属性 · 核心基础攻击力+暴击率</p>
        <p>4+2（4增伤2攻击） · 4号暴伤/5号穿透%/6号攻击%</p>
      </div>
    </div>

    <!-- 整体结构 -->
    <GuideSection title="一、整体结构概览" anchor="overview">
      <div class="guide-card">
        <p>面板由 <strong>6大模块</strong> 组成，最终汇总计算出角色的最终属性：</p>
        <div class="guide-flow">
          <div class="guide-flow__item">基础面板</div>
          <span class="guide-flow__arrow">→</span>
          <div class="guide-flow__item guide-flow__item--weapon">武器加成</div>
          <span class="guide-flow__arrow">→</span>
          <div class="guide-flow__item guide-flow__item--core">核心加成</div>
          <span class="guide-flow__arrow">→</span>
          <div class="guide-flow__item guide-flow__item--drive">驱动盘</div>
          <span class="guide-flow__arrow">→</span>
          <div class="guide-flow__item guide-flow__item--set">2件套</div>
          <span class="guide-flow__arrow">→</span>
          <div class="guide-flow__item guide-flow__item--final">最终面板</div>
        </div>
        <p>💡 不是简单的1+1，不同属性有不同的计算方式，下面逐一讲解。</p>
      </div>
    </GuideSection>

    <!-- 模块详解 -->
    <GuideSection title="二、六大模块详解" anchor="modules">
      <h3><span class="guide-tag">基础面板</span>角色自带属性</h3>
      <div class="guide-card">
        <p>角色出生自带的属性，<strong>再加上核心提供的基础值/部分加成</strong>，合起来叫“基础面板”。</p>
        <GuideCallout tone="blue" title="📌 一句话理解">
          <p>基础面板 = 角色自带 + 核心的<strong>基础值</strong> + 核心的<strong>非攻防血百分比</strong></p>
          <p>只有攻防血的百分比%是单独加的，其他核心加成全都算进基础面板里。</p>
        </GuideCallout>
        <GuideAttrGrid :items="BASE_ATTRS" />
        <p>
          * 攻击力 888 = 角色自带 813 + 核心基础攻击 75<br />
          * 暴击率 19.4% = 角色自带 5% + 核心暴击率 14.4%<br />
          * 代理人各项数值因角色而异，以上为示例数值。
        </p>
      </div>

      <div class="guide-card">
        <h3>🧩 基础面板的3种来源情况</h3>
        <p>
          你拿到的“基础面板”数值，不一定包含了核心的全部内容。根据数据来源的不同，有3种情况，需要分别处理：
        </p>
        <GuideTable :head="['#', '含核心基础值？', '含核心百分比？', '处理方式']" compact>
          <tr>
            <td><strong>1</strong></td>
            <td class="guide-yes">✅ 包含</td>
            <td class="guide-no">❌ 不含</td>
            <td><strong>正常计算</strong>：直接用这个基础值，核心百分比单独加</td>
          </tr>
          <tr>
            <td><strong>2</strong></td>
            <td class="guide-no">❌ 不含</td>
            <td class="guide-yes">✅ 包含</td>
            <td><strong>还原除法</strong>：数值 ÷ (1 + 核心%) = 实际基础面板</td>
          </tr>
          <tr>
            <td><strong>3</strong></td>
            <td class="guide-no">❌ 不含</td>
            <td class="guide-no">❌ 不含</td>
            <td><strong>直接相加</strong>：数值 + 核心基础值 = 实际基础面板</td>
          </tr>
        </GuideTable>
        <GuideCallout title="📝 举例说明（以攻击力为例）">
          <p>假设：角色纯基础攻击 = 1000，核心选了「基础攻击75」和「暴击率14.4%」</p>
          <p>
            <strong>情况1（含核心基础值，不含核心%）：</strong>拿到攻击 1075 → 正确，直接用。核心没有攻击%，所以不用加
          </p>
          <p><strong>情况2（不含核心基础值，含核心%）：</strong>假如核心选的是生命%18%，拿到生命 9440 → 9440 ÷ 1.18 = 8000（实际基础面板）</p>
          <p><strong>情况3（都不含）：</strong>拿到攻击 1000 → 1000 + 75 = 1075（实际基础面板）</p>
          <p>💡 情况1是最标准、最常见的（也就是本指南默认使用的情况）。</p>
          <p>⚠ 核心对同一属性<strong>不会同时</strong>提供基础值和百分比，所以“都含”的情况不会出现。</p>
        </GuideCallout>
      </div>

      <h3><span class="guide-tag guide-tag--core">核心加成</span>核心提供的加成</h3>
      <div class="guide-card">
        <p>💡 核心分两部分：<strong>基础值</strong>（已算进基础面板）和<strong>百分比</strong>（在这里单独加）</p>
        <h4>核心加成机制</h4>
        <p>
          核心从以下 <strong>8项中随机选2项</strong>，<strong>可以重复选同一项</strong>（比如两次暴击率 = 28.8%）：
        </p>
        <GuideTable :head="['加成项', '单组数值', '类型', '归属']" compact>
          <tr><td>基础能量自动回复</td><td>+0.36</td><td>数值型</td><td>归入基础面板</td></tr>
          <tr><td>基础攻击力</td><td>+75</td><td>基础值</td><td>归入基础面板</td></tr>
          <tr><td>基础冲击力</td><td>+18</td><td>基础值</td><td>归入基础面板</td></tr>
          <tr><td>暴击伤害</td><td>+28.8%</td><td>百分比</td><td>归入基础面板（双爆类）</td></tr>
          <tr><td>暴击率</td><td>+14.4%</td><td>百分比</td><td>归入基础面板（双爆类）</td></tr>
          <tr><td>生命值百分比</td><td>+18%</td><td>百分比</td><td>单独加（攻防血的%）</td></tr>
          <tr><td>异常掌控</td><td>+36</td><td>数值型</td><td>归入基础面板</td></tr>
          <tr><td>异常精通</td><td>+54</td><td>数值型</td><td>归入基础面板</td></tr>
        </GuideTable>
        <GuideCallout title="📌 核心加成的归属判断">
          <p>• <strong>攻防血的基础值</strong>（基础攻击75等）→ 算进基础面板</p>
          <p>• <strong>攻防血的百分比</strong>（生命%18%等）→ 单独加，归到百分比区域</p>
          <p>• <strong>其他所有属性</strong>（暴击率/暴伤/异常精通/异常掌控等）→ 都算进基础面板</p>
          <p>⚠ 同一属性不会同时有基础值和百分比（核心互斥规则）。</p>
        </GuideCallout>
      </div>

      <div class="guide-card">
        <h3>🔑 核心归属统一原则</h3>
        <p>核心从8项中<strong>随机选2项</strong>（可重复），每项归属规则如下：</p>
        <GuideCallout tone="blue" title="先乘后加的属性（6种）">
          <p>• 攻击/生命/防御 + 冲击力/异常掌控/能量回复</p>
          <p>• 核心的<strong>基础值</strong>（基础攻击75、基础冲击力18等）→ 算进基础面板</p>
          <p>• 核心的<strong>百分比%</strong>（生命%18%等）→ 单独算，归到百分比区域</p>
        </GuideCallout>
        <GuideCallout tone="green" title="纯加法的属性（5种）">
          <p>• 暴击率/暴伤/增伤/穿透率 + 穿透值/异常精通</p>
          <p>• 核心提供的加成 → <strong>全部算进基础面板</strong></p>
          <p>• 不要再单独加一遍！会重复计算！</p>
        </GuideCallout>
        <GuideCallout tone="purple" title="⚠ 重要互斥规则">
          <p>对于<strong>同一条属性</strong>，核心<strong>不会同时提供</strong>基础值和百分比加成。</p>
          <p>比如：核心选了基础攻击75，就不会再有攻击%；选了暴击率%，就不会再有暴击基础值。</p>
        </GuideCallout>
      </div>

      <h3><span class="guide-tag guide-tag--weapon">武器加成</span>武器提供的属性</h3>
      <div class="guide-card">
        <GuideAttrGrid :items="WEAPON_ATTRS" />
        <GuideCallout title="📌 武器两条重要规则">
          <p><strong>1. 基础攻防互斥</strong>：一把武器要么加攻击，要么加防御，不会同时加。攻击型武器基础防御=0，反之亦然。</p>
          <p><strong>2. 副词条只有1种</strong>：从9种里面选1种作为副词条，其他都是0。</p>
          <p>副词条池：生命%、攻击%、防御%、冲击力%、暴击率、暴伤、异常掌控%、异常精通、能量回复%</p>
        </GuideCallout>
      </div>

      <h3><span class="guide-tag guide-tag--drive">驱动盘</span>主词条 + 副词条</h3>
      <div class="guide-card">
        <h4>主词条数值（都是固定值）</h4>
        <p>每个位置的主词条属性是固定的，数值也是<strong>固定的</strong>，不会随机变化。</p>
        <GuideTable :head="['位置', '主词条属性', '固定数值', '可选范围']">
          <tr>
            <td>1号</td><td>固定生命</td><td><strong>+2200</strong></td><td>唯一，没有选择</td>
          </tr>
          <tr>
            <td>2号</td><td>固定攻击</td><td><strong>+316</strong></td><td>唯一，没有选择</td>
          </tr>
          <tr>
            <td>3号</td><td>固定防御</td><td><strong>+184</strong></td><td>唯一，没有选择</td>
          </tr>
          <tr>
            <td>4号</td><td>6选1</td>
            <td>攻击30% / 生命30% / 防御48%<br />暴击率24% / 暴伤48% / 异常精通92</td>
            <td>从6种里选1种</td>
          </tr>
          <tr>
            <td>5号</td><td>5选1</td>
            <td>攻击30% / 生命30% / 防御48%<br />穿透率24% / 增伤30%</td>
            <td>从5种里选1种</td>
          </tr>
          <tr>
            <td>6号</td><td>6选1</td>
            <td>攻击30% / 生命30% / 防御48%<br />冲击力24% / 异常掌控30% / 能量回复60%</td>
            <td>从6种里选1种</td>
          </tr>
        </GuideTable>

        <h4>副词条单条数值（都是固定值）</h4>
        <p>
          副词条的<strong>单条数值也是固定的</strong>，每一条提供的数值都一样。10种词条各自的固定值如下：
        </p>
        <GuideTable :head="['词条名称', '单条数值', '类型', '对应主词条']" compact>
          <tr><td>小生命（固定生命）</td><td><strong>+112</strong></td><td>固定值</td><td>1号主词条，主副不重复</td></tr>
          <tr><td>大生命%</td><td><strong>+3%</strong></td><td>百分比</td><td>4/5/6号可选</td></tr>
          <tr><td>小攻击（固定攻击）</td><td><strong>+19</strong></td><td>固定值</td><td>2号主词条，主副不重复</td></tr>
          <tr><td>大攻击%</td><td><strong>+3%</strong></td><td>百分比</td><td>4/5/6号可选</td></tr>
          <tr><td>小防御（固定防御）</td><td><strong>+15</strong></td><td>固定值</td><td>3号主词条，主副不重复</td></tr>
          <tr><td>大防御%</td><td><strong>+4.8%</strong></td><td>百分比</td><td>4/5/6号可选</td></tr>
          <tr><td>暴击率</td><td><strong>+2.4%</strong></td><td>百分比</td><td>4号可选</td></tr>
          <tr><td>暴击伤害</td><td><strong>+4.8%</strong></td><td>百分比</td><td>4号可选</td></tr>
          <tr><td>穿透值</td><td><strong>+9</strong></td><td>数值型</td><td>不在主词条（5号是穿透率）</td></tr>
          <tr><td>异常精通</td><td><strong>+9</strong></td><td>数值型</td><td>4号可选</td></tr>
        </GuideTable>
        <GuideCallout title="📌 副词条3条核心规则">
          <p><strong>1. 10选4：</strong>从上面10种里随机选4种作为初始副词条</p>
          <p><strong>2. 5次强化：</strong>每个盘有5次强化机会，<strong>随机加到已有的4条副词条上</strong>（不会新增词条种类）</p>
          <p><strong>3. 主副不重复：</strong>副词条不会出现和主词条一样的属性</p>
        </GuideCallout>
      </div>

      <h3><span class="guide-tag guide-tag--set">2件套效果</span>套装加成</h3>
      <div class="guide-card">
        <p>装上2件/4件同套装驱动盘，触发套装效果。<strong>每组2件套提供的数值也是固定的</strong>。</p>
        <GuideTable :head="['套装属性', '单组2件套数值', '说明']" compact>
          <tr><td>生命</td><td><strong>+10%</strong></td><td>百分比</td></tr>
          <tr><td>攻击力</td><td><strong>+10%</strong></td><td>百分比</td></tr>
          <tr><td>防御力</td><td><strong>+10%</strong></td><td>百分比</td></tr>
          <tr><td>暴击率</td><td><strong>+8%</strong></td><td>百分比</td></tr>
          <tr><td>暴击伤害</td><td><strong>+16%</strong></td><td>百分比</td></tr>
          <tr><td>异常掌控</td><td><strong>+8%</strong></td><td>百分比</td></tr>
          <tr><td>能量回复</td><td><strong>+20%</strong></td><td>百分比</td></tr>
          <tr><td>增伤</td><td><strong>+10%</strong></td><td>百分比</td></tr>
          <tr><td>异常精通</td><td><strong>+30</strong></td><td>数值型</td></tr>
          <tr><td>冲击力</td><td><strong>+6%</strong></td><td>百分比</td></tr>
        </GuideTable>
        <GuideCallout tone="blue" title="📌 套装搭配：最少0组，最多3组">
          <p>6个驱动盘，每2件触发1组2件套效果：</p>
          <p>• <strong>2+2+2 搭配</strong>：3套各2件 → 共 <strong>3组</strong> 2件套（最多）</p>
          <p>• <strong>4+2 搭配</strong>：1套4件 + 1套2件 → 共 <strong>2组</strong> 2件套</p>
          <p>　💡 4件套只算1组2件套效果（4件套有自己的特殊效果，但不多加一组2件套）</p>
          <p>• <strong>2+散件</strong>：只有2件套装 → 共 <strong>1组</strong> 2件套</p>
          <p>• <strong>全散件</strong>：6件都不是套装 → 共 <strong>0组</strong> 2件套（最少）</p>
        </GuideCallout>
      </div>
    </GuideSection>

    <!-- 攻防血通用计算 -->
    <GuideSection title="三、攻防血通用计算" anchor="attack">
      <div class="guide-card">
        <div class="guide-formula guide-formula--purple">
          <p class="guide-formula__label">⭐ 通用公式（攻击/生命/防御都一样）</p>
          最终属性 = ( 基础总值 ) × ( 1 + 所有百分比加成 ) + 所有固定值加成
        </div>

        <div class="guide-step guide-step--1">
          <div class="guide-step__label">第一步：算基础总值</div>
          基础总值 = 基础面板 (角色自带 + 核心基础，但不包括核心百分比) + 武器基础值
        </div>
        <div class="guide-step guide-step--2">
          <div class="guide-step__label">第二步：算百分比总和</div>
          百分比总和 = 核心% + 2件套% + 驱动盘4/5/6号主词条% + 副词条大%
        </div>
        <div class="guide-step guide-step--3">
          <div class="guide-step__label">第三步：算固定值总和</div>
          固定值总和 = 驱动盘对应主词条 + 副词条固定值总和
        </div>
        <div class="guide-step">
          <div class="guide-step__label">第三步：算固定值，得出结果</div>
          最终属性 = 基础总值 × (1 + 百分比总和) + 固定值总和
        </div>
      </div>

      <h3>🔴 示例：攻击力计算</h3>
      <div class="guide-card">
        <p>我们来一步步算“夏潾”的最终攻击力（4号暴伤 / 5号穿透% / 6号攻击%，2件爆伤套）：</p>
        <GuideTable :head="['项目', '来源', '数值']" numeric>
          <tr class="guide-table__section"><td colspan="3">📦 基础总值</td></tr>
          <tr><td>基础面板攻击</td><td>角色自带 813 + 核心基础 75</td><td>888</td></tr>
          <tr><td>+ 武器基础攻击</td><td>武器</td><td>+ 713</td></tr>
          <tr class="guide-table__total"><td colspan="2">基础攻击总值</td><td>1601</td></tr>

          <tr class="guide-table__section"><td colspan="3">📈 百分比加成</td></tr>
          <tr><td>核心攻击%</td><td>0（核心为基础攻击，不是攻击%）</td><td>+ 0%</td></tr>
          <tr><td>2件套攻击%</td><td>1组攻击套（10%/组）</td><td>+ 10%</td></tr>
          <tr><td>驱动盘6号主词条</td><td>攻击%（固定30%）</td><td>+ 30%</td></tr>
          <tr><td>副词条大攻击%</td><td>9条 × 3%/条</td><td>+ 27%</td></tr>
          <tr class="guide-table__total"><td colspan="2">百分比加成总和</td><td>+ 67%</td></tr>

          <tr class="guide-table__section"><td colspan="3">➕ 固定值加成</td></tr>
          <tr><td>驱动盘2号固定攻击</td><td>主词条（固定316）</td><td>+ 316</td></tr>
          <tr><td>副词条小攻击</td><td>4条 × 19/条</td><td>+ 76</td></tr>
          <tr class="guide-table__total"><td colspan="2">固定值加成总和</td><td>+ 392</td></tr>
        </GuideTable>
        <div class="guide-formula guide-formula--green">
          <p class="guide-formula__label">代入公式计算</p>
          最终攻击力 = 1601 × (1 + 67%) + 392<br />
          　　　　= 1601 × 1.67 + 392<br />
          　　　　= 2672.75 + 392<br />
          　　　　= <strong>3064.75</strong>
        </div>
      </div>

      <h3>💚 示例：生命值计算</h3>
      <div class="guide-card">
        <p>同样的公式，换套数字就行：</p>
        <GuideTable :head="['项目', '来源', '数值']" numeric>
          <tr class="guide-table__section"><td colspan="3">📦 基础总值</td></tr>
          <tr><td>基础面板生命</td><td>角色自带 + 核心基础值</td><td>7673</td></tr>
          <tr><td>+ 武器基础生命</td><td>武器不加生命</td><td>+ 0</td></tr>
          <tr class="guide-table__total"><td colspan="2">基础生命总值</td><td>7673</td></tr>

          <tr class="guide-table__section"><td colspan="3">📈 百分比加成</td></tr>
          <tr><td>核心生命%</td><td>核心</td><td>+ 0%</td></tr>
          <tr><td>2件套生命%</td><td>0组</td><td>+ 0%</td></tr>
          <tr><td>驱动盘主词条生命%</td><td>4号+5号+6号</td><td>+ 0%</td></tr>
          <tr><td>副词条大生命%</td><td>2条 × 3%/条</td><td>+ 6%</td></tr>
          <tr class="guide-table__total"><td colspan="2">百分比加成总和</td><td>+ 6%</td></tr>

          <tr class="guide-table__section"><td colspan="3">➕ 固定值加成</td></tr>
          <tr><td>驱动盘1号固定生命</td><td>主词条（固定2200）</td><td>+ 2200</td></tr>
          <tr><td>副词条小生命</td><td>4条 × 112/条</td><td>+ 448</td></tr>
          <tr class="guide-table__total"><td colspan="2">固定值加成总和</td><td>+ 2648</td></tr>
        </GuideTable>
        <div class="guide-formula guide-formula--green">
          <p class="guide-formula__label">代入公式计算</p>
          最终生命值 = 7673 × (1 + 6%) + 2648<br />
          　　　　= 8133.38 + 2648<br />
          　　　　= <strong>10781.38</strong>
        </div>
        <p>💡 如果百分比为0，看起来公式就会转变为“基础+固定值”，但公式是通用的。</p>
      </div>
    </GuideSection>

    <!-- 双爆与其他属性 -->
    <GuideSection title="四、双爆与其他属性" anchor="crit">
      <h3>🟠 暴击率（纯加法）</h3>
      <div class="guide-card">
        <div class="guide-formula">
          <p class="guide-formula__label">最终暴击率 = 基础暴击率 + 其他所有来源</p>
        </div>
        <p>暴击率是<strong>纯加法</strong>，所有来源直接加起来。</p>
        <GuideTable :head="['项目', '来源', '数值']" numeric>
          <tr><td>基础暴击率（已含核心14.4%）</td><td>角色自带 5% + 核心 14.4%</td><td>19.4%</td></tr>
          <tr><td>武器副词条暴击率</td><td>武器副词条提供</td><td>24%</td></tr>
          <tr><td>2件套暴击率</td><td>0组（本配置选的是4增伤2攻击套）</td><td>+ 0%</td></tr>
          <tr><td>驱动盘4号主词条</td><td>0（选的是暴伤不是暴击率）</td><td>+ 0%</td></tr>
          <tr><td>驱动盘副词条暴击率</td><td>12条 × 2.4%/条</td><td>+ 28.8%</td></tr>
          <tr class="guide-table__total"><td colspan="2">最终暴击率</td><td>72.2%</td></tr>
        </GuideTable>
        <GuideCallout tone="blue" title="📌 注意！核心已经算在基础里了">
          <p>基础暴击率 = 角色自带 + 核心暴击率。所以<strong>不要再加一遍核心暴击率</strong>，会重复计算！</p>
        </GuideCallout>
      </div>

      <h3>🟡 暴击伤害（纯加法）</h3>
      <div class="guide-card">
        <div class="guide-formula">
          <p class="guide-formula__label">最终暴伤 = 基础暴伤 + 其他所有来源</p>
        </div>
        <GuideTable :head="['项目', '来源', '数值']" numeric>
          <tr><td>基础暴伤（已含核心）</td><td>角色自带 + 核心暴伤（核心为0%）</td><td>50%</td></tr>
          <tr><td>武器副词条暴击伤害</td><td>武器副词条提供</td><td>+ 0%</td></tr>
          <tr><td>驱动盘4号暴伤</td><td>主词条（固定48%）</td><td>+ 48%</td></tr>
          <tr><td>2件套暴伤</td><td>0组暴伤套（16%/组）</td><td>+ 0%</td></tr>
          <tr><td>驱动盘副词条暴伤</td><td>12条 × 4.8%/条</td><td>+ 57.6%</td></tr>
          <tr class="guide-table__total"><td colspan="2">最终暴击伤害</td><td>155.6%</td></tr>
        </GuideTable>
        <p>💡 和暴击率一样，纯加法，核心暴伤已包含在基础里。</p>
      </div>

      <h3>🟢 增伤 &amp; 穿透率（面板显示百分比）</h3>
      <div class="guide-card">
        <p>增伤、穿透率——这两个<strong>面板显示为百分比</strong>，计算方式是纯加法：</p>
        <div class="guide-formula guide-formula--green">
          <p class="guide-formula__label">增伤计算示例</p>
          最终增伤 = 2件套增伤 + 驱动盘5号增伤<br />
          　　　　　= 10% + 0%<br />
          　　　　　= <strong>10%</strong>
          <p>（1组增伤套 = 10%，5号主词条选择了穿透%）</p>
        </div>
        <GuideCallout tone="green" title="🎯 面板百分比只有4种">
          <p>暴击率、暴击伤害、增伤、穿透率 —— 全都是纯加法。</p>
        </GuideCallout>
      </div>

      <h3>🟠 冲击力 / 异常掌控 / 能量回复（先乘后加，面板显示数值）</h3>
      <div class="guide-card">
        <p>
          这三个属性<strong>面板上显示的是数值</strong>，但计算方式和攻防血一样，是 <strong>基础值 × (1 + 百分比)</strong>：
        </p>
        <p>💡 和攻防血的区别：<strong>没有固定值加成</strong>（没有“小冲击”“小异常掌控”这种副词条）</p>
        <div class="guide-formula guide-formula--orange">
          <p class="guide-formula__label">冲击力计算示例假设</p>
          基础冲击力：93（角色自带）<br />
          百分比加成：假设武器副词条选冲击力% = 20%，其余所有来源为0%（本示例没有其他来源）<br />
          最终冲击力 = 93 × (1 + 20%)<br />
          　　　　= 93 × 1.2<br />
          　　　　= <strong>111.6</strong>
          <p>（百分比来源：6号主词条24% / 武器副词条 / 冲击力2件套 = 6%/组）</p>
        </div>
        <div class="guide-formula guide-formula--orange">
          <p class="guide-formula__label">异常掌控计算示例假设</p>
          基础异常掌控：94（角色自带）<br />
          百分比加成：8%（2件套）= 8%<br />
          最终异常掌控 = 94 × (1 + 8%)<br />
          　　　　　= 94 × 1.08<br />
          　　　　　= <strong>102.4</strong>
          <p>（百分比来源：6号主词条30% / 异常掌控2件套 = 8%/组）</p>
        </div>
        <div class="guide-formula guide-formula--orange">
          <p class="guide-formula__label">能量自动回复计算示例假设</p>
          基础能量回复：0.5/s（角色自带）<br />
          百分比加成：0（本示例没有能量回复来源）<br />
          最终能量回复 = 0.5 × (1 + 0%) = <strong>0.5/s</strong>
          <p>（百分比来源：6号主词条60% / 能量回复2件套 = 20%/组）</p>
        </div>
        <GuideCallout tone="yellow" title="📌 关键区分">
          <p>• <strong>攻防血</strong>：基础 × (1+%) <strong>+ 固定值</strong>（有小攻击/小生命/小防御等副词条）</p>
          <p>• <strong>冲击力/异常掌控/能量回复</strong>：基础 × (1+%) <strong>无固定值</strong></p>
          <p>• 百分比来源：驱动盘6号主词条、2件套、武器副词条</p>
        </GuideCallout>
      </div>

      <h3>🔵 穿透值 &amp; 异常精通（纯加法，数值型）</h3>
      <div class="guide-card">
        <p>这两个比较特殊——它们<strong>本身就是数值</strong>，不是百分比，纯加法直接加：</p>
        <div class="guide-formula">
          <p class="guide-formula__label">穿透值 = 所有来源穿透值相加</p>
          示例：副词条穿透值 4条 × 9/条 = 36 → 最终穿透值 = 36
        </div>
        <p>💡 穿透值和穿透率是两回事！穿透值是固定数值，穿透率是百分比（5号主词条有24%穿透率）。</p>
        <GuideCallout tone="purple" title="📌 异常精通也是数值型">
          <p>4号主词条异常精通 = 92，副词条每条异常精通 = 9，都是直接加。</p>
          <p>2件套异常精通 = 30/组，也是直接加。</p>
        </GuideCallout>
      </div>
    </GuideSection>

    <!-- 驱动盘进阶 -->
    <GuideSection title="五、驱动盘进阶知识" anchor="drive">
      <h3>📊 副词条数量基础</h3>
      <div class="guide-card">
        <GuideTable :head="['项目', '数量', '说明']">
          <tr><td>每盘初始副词条</td><td>4条</td><td>从10种里随机选4种</td></tr>
          <tr><td>每盘强化次数</td><td>5次</td><td>随机加到已有的4条上，不新增种类</td></tr>
          <tr><td>每盘词条总数</td><td>9条</td><td>4条初始 + 5次强化 = 9条</td></tr>
          <tr><td>6盘物理总数</td><td><strong>54条</strong></td><td>9条 × 6盘 = 54条（固定不变）</td></tr>
        </GuideTable>
      </div>

      <h3>🎯 不同职业的有效词条</h3>
      <div class="guide-card">
        <p>不是所有词条都有用。不同职业，“有效词条”不一样，当然他们的优先级也不一样，需要根据职业来选择：</p>
        <GuideTable :head="['职业', '有效副词条', '种数']">
          <tr><td class="guide-role guide-role--assault">强攻</td><td>暴击率、暴伤、大攻击%、小攻击、穿透值</td><td>5种</td></tr>
          <tr><td class="guide-role guide-role--defense">锋御</td><td>暴击率、大防御%、小防御、暴伤、穿透值</td><td>5种</td></tr>
          <tr><td class="guide-role guide-role--abnormal">异常</td><td>异常精通、大攻击%、小攻击、穿透值</td><td>4种</td></tr>
          <tr><td class="guide-role guide-role--stun">击破</td><td>暴击率、暴伤、大攻击%、小攻击、穿透值</td><td>5种</td></tr>
          <tr><td class="guide-role guide-role--rupture">命破</td><td>暴击率、暴伤、大生命%、小生命、大攻击%、小攻击</td><td>6种</td></tr>
          <tr><td class="guide-role guide-role--support">辅助</td><td>生命占模（堆生命）/ 攻击占模（堆攻击）</td><td>视情况</td></tr>
        </GuideTable>
        <p>💡 “占模”的意思：辅助的技能吃什么属性就堆什么。吃生命就堆生命，吃攻击就堆攻击。</p>
      </div>

      <h3>📐 有效副词条总数怎么算？</h3>
      <div class="guide-card">
        <GuideCallout tone="blue" title="核心逻辑">
          <p>因为“主副不重复”——主词条如果是有效词条，副词条里就不能有这个了，有效词条会少1种。</p>
          <p><strong>判断规则：</strong></p>
          <p>• 有效词条种数 ≥ 4 → 初始4条全是有效 → 每盘 <strong>9条有效</strong>（4+5）</p>
          <p>• 有效词条种数 &lt; 4 → 初始只能选到N种有效 → 每盘 <strong>N+5条有效</strong></p>
        </GuideCallout>

        <h4>示例1：强攻（暴伤/增伤/攻击）→ 54条有效</h4>
        <GuideTable :head="['位置', '主词条', '被排除的有效词条', '剩余有效种数', '有效词条数']" compact>
          <tr><td>1号</td><td>固定生命</td><td>无（不是有效词条）</td><td>5种（≥4）</td><td><strong>9条</strong></td></tr>
          <tr><td>2号</td><td>固定攻击</td><td>小攻击</td><td>4种（≥4）</td><td><strong>9条</strong></td></tr>
          <tr><td>3号</td><td>固定防御</td><td>无</td><td>5种（≥4）</td><td><strong>9条</strong></td></tr>
          <tr><td>4号</td><td>暴伤</td><td>暴伤</td><td>4种（≥4）</td><td><strong>9条</strong></td></tr>
          <tr><td>5号</td><td>增伤</td><td>无（不在副词条池）</td><td>5种（≥4）</td><td><strong>9条</strong></td></tr>
          <tr><td>6号</td><td>攻击%</td><td>大攻击%</td><td>4种（≥4）</td><td><strong>9条</strong></td></tr>
        </GuideTable>
        <p><strong>合计：9+9+9+9+9+9 = 54条有效</strong></p>
        <p>强攻有5种有效词条，就算被排除1种也还剩4种，刚好填满4条初始，所以每盘都是9条。</p>

        <h4>示例2：异常（异常精通/攻击/攻击）→ 50条有效</h4>
        <GuideTable :head="['位置', '主词条', '被排除的有效词条', '剩余有效种数', '有效词条数']" compact>
          <tr><td>1号</td><td>固定生命</td><td>无</td><td>4种（≥4）</td><td><strong>9条</strong></td></tr>
          <tr><td>2号</td><td>固定攻击</td><td>小攻击</td><td>3种（&lt;4）</td><td><strong>8条</strong>（3+5）</td></tr>
          <tr><td>3号</td><td>固定防御</td><td>无</td><td>4种（≥4）</td><td><strong>9条</strong></td></tr>
          <tr><td>4号</td><td>异常精通</td><td>异常精通</td><td>3种（&lt;4）</td><td><strong>8条</strong>（3+5）</td></tr>
          <tr><td>5号</td><td>攻击%</td><td>大攻击%</td><td>3种（&lt;4）</td><td><strong>8条</strong>（3+5）</td></tr>
          <tr><td>6号</td><td>攻击%</td><td>大攻击%</td><td>3种（&lt;4）</td><td><strong>8条</strong>（3+5）</td></tr>
        </GuideTable>
        <p><strong>合计：9+8+9+8+8+8 = 50条有效</strong></p>
        <p>异常只有4种有效词条，被排除1种就只剩3种（不足4），所以有4个盘只有8条有效。</p>
      </div>
    </GuideSection>

    <!-- 总结 -->
    <GuideSection title="六、规律与概念总结" anchor="summary">
      <div class="guide-summary">
        <h3>📌 一张表看懂所有属性怎么算</h3>
        <GuideTable :head="['属性类型', '计算方式', '面板显示']">
          <tr>
            <td><strong>攻击/生命/防御</strong></td>
            <td>先乘后加：基础 × (1+百分比) + 固定值</td>
            <td class="guide-num">数值</td>
          </tr>
          <tr>
            <td><strong>冲击力/异常掌控/能量回复</strong></td>
            <td>先乘后加：基础 × (1+百分比) <span class="guide-warn">⚠ 无固定值</span></td>
            <td class="guide-num">数值</td>
          </tr>
          <tr>
            <td>暴击率/暴伤/增伤/穿透率</td>
            <td>纯加法：所有来源直接相加</td>
            <td class="guide-pct">百分比%</td>
          </tr>
          <tr>
            <td>穿透值/异常精通</td>
            <td>纯加法（数值型，直接加）</td>
            <td class="guide-num">数值</td>
          </tr>
        </GuideTable>
        <p>
          💡 <strong>记忆口诀：</strong>先乘后加6种——攻防血（有固定值）+ 冲异能（无固定值）；面板百分比只有4种——暴击率、暴伤、增伤、穿透率。
        </p>
      </div>

      <div class="guide-card">
        <h3>💡 基础值 vs 百分比 vs 固定值</h3>
        <GuideTable :head="['类型', '特点', '举个例子']">
          <tr>
            <td class="guide-kind guide-kind--base">基础值</td>
            <td>计算百分比的“本金”</td>
            <td>角色攻击1000 + 武器攻击500 = 1500</td>
          </tr>
          <tr>
            <td class="guide-kind guide-kind--pct">百分比%</td>
            <td>按基础值的比例增加</td>
            <td>大攻击%、核心攻击%、套装攻击%</td>
          </tr>
          <tr>
            <td class="guide-kind guide-kind--flat">固定值</td>
            <td>直接加数字，不吃百分比</td>
            <td>小攻击、2号位固定攻击</td>
          </tr>
        </GuideTable>
        <GuideCallout title="🎯 提升小技巧">
          <p>百分比加成是乘以基础总值的，所以<strong>基础总值越高，百分比越赚</strong>。</p>
          <p>高基础角色优先堆百分比，低基础角色固定值也很香。</p>
          <p>* 仅限攻防血哦，其他属性都是纯加法，没有这个区别。</p>
        </GuideCallout>
      </div>

      <div class="guide-card guide-final">
        <h3>🏆 最终面板一览 · 夏潾</h3>
        <p class="guide-final__config">
          　　配置：<br />
          · 基础攻击75+暴击率14.4%核心<br />
          · 武器攻击713暴击率24%<br />
          · 4号暴伤/5号穿透%/6号攻击%<br />
          · 4+2（攻击10%+增伤10%）
        </p>
        <GuideAttrGrid :items="FINAL_ATTRS" :columns="4" on-dark />
        <p class="guide-final__note">💡 以上数值为示例，基于“夏潾”的虚构配置计算得出。</p>
      </div>

      <div class="guide-card guide-done">
        <h3>🎉 恭喜你学完了！</h3>
        <p>再回顾一下最重要的3件事：</p>
        <ol>
          <li><strong>先乘后加6种：</strong>攻防血 + 冲击力/异常掌控/能量回复</li>
          <li><strong>纯加法5种：</strong>双爆/增伤/穿透率/穿透值/异常精通</li>
          <li><strong>核心：</strong>基础值在基础面板里，百分比单独算，别重复加</li>
        </ol>
      </div>
    </GuideSection>
  </main>
</template>
