function fillSelect(id, opts, noneLabel) {
      const sel = document.getElementById(id);
      let html = '';
      if (noneLabel) html += `<option value="-1">${noneLabel}</option>`;
      opts.forEach((o, i) => {
        html += `<option value="${i}">${o.label}</option>`;
      });
      sel.innerHTML = html;
    }

    fillSelect('core1', CORE_OPTIONS, '请选择');
    fillSelect('core2', CORE_OPTIONS, '请选择');
    fillSelect('disc4', DISC4_OPTIONS, '请选择');
    fillSelect('disc5', DISC5_OPTIONS, '请选择');
    fillSelect('disc6', DISC6_OPTIONS, '请选择');

    // 副词条网格
    const subGrid = document.getElementById('sub_grid');
    subGrid.innerHTML = SUB_STATS.map(s => `
  <div class="field">
    <label>${s.label} <span class="unit">+${s.value}${s.kind === 'pct' ? '%' : ''}/条</span></label>
    <div class="sub-count">
      <button type="button" class="sub-count-btn" data-delta="-1" aria-label="减少${s.label}副词条数量" onclick="adjustSubInput('sub_${s.id}', -1)">−</button>
      <input type="number" id="sub_${s.id}" value="0" min="0" max="36" step="1" oninput="handleSubInput(this)" aria-label="${s.label}副词条数量">
      <button type="button" class="sub-count-btn" data-delta="1" aria-label="增加${s.label}副词条数量" onclick="adjustSubInput('sub_${s.id}', 1)">+</button>
      <span class="total" id="sub_v_${s.id}">0</span>
    </div>
  </div>
`).join('');
    // 二件套
    const setsContainer = document.getElementById('sets_container');
    function buildSets() {
      setsContainer.innerHTML = Array.from({ length: 3 }, (_, i) => `
    <div class="set-item">
      <label class="helper">第${i + 1}组</label>
      <select id="set${i}" onchange="calc()">
        <option value="-1">请选择</option>
        <option value="-1">无</option>
        ${SET_OPTIONS.map((o, j) => `<option value="${j}">${o.label}</option>`).join('')}
      </select>
    </div>
  `).join('');
    }
    buildSets();

    const agentRoleSelect = document.getElementById('agent_role');
    const agentPresetSelect = document.getElementById('agent_preset');
    const agentRoles = ['强攻', '击破', '异常', '支援', '防护', '命破', '锋御'];
    const invalidAgentPresets = AGENT_PRESETS.filter(agent =>
      !agent.id || !agent.name || !agentRoles.includes(agent.roleTag)
    );
    if (invalidAgentPresets.length) {
      throw new Error(`代理人预设存在缺少专属标签或无效数据的条目：${invalidAgentPresets.map(agent => agent.name || agent.id || '未知条目').join('、')}`);
    }
    const duplicateAgentIds = AGENT_PRESETS.filter((agent, index) =>
      AGENT_PRESETS.findIndex(candidate => candidate.id === agent.id) !== index
    );
    if (duplicateAgentIds.length) {
      throw new Error(`代理人预设存在重复ID：${[...new Set(duplicateAgentIds.map(agent => agent.id))].join('、')}`);
    }
    [...new Set(AGENT_PRESETS.map(agent => agent.roleTag))]
      .forEach(role => agentRoleSelect.add(new Option(role, role)));
    let appliedAgentPresetId = '';
    const panelModeLabels = {
      standard: '通用',
      rupture: '命破',
      fengyu: '锋御',
    };
    const weaponGradeSelect = document.getElementById('weapon_grade');
    const weaponRoleSelect = document.getElementById('weapon_role');
    const weaponPresetSelect = document.getElementById('weapon_preset');
    const weaponPresets = window.WEAPON_PRESETS;
    [...new Set(weaponPresets.map(weapon => weapon.grade))]
      .sort((a, b) => ['S', 'A', 'B'].indexOf(a) - ['S', 'A', 'B'].indexOf(b))
      .forEach(grade => {
        const option = document.createElement('option');
        option.value = grade;
        option.textContent = `${grade}级`;
        weaponGradeSelect.append(option);
      });

    function updateWeaponGrade() {
      weaponRoleSelect.replaceChildren(new Option('请选择', ''));
      weaponPresetSelect.replaceChildren(new Option('请选择', ''));
      weaponRoleSelect.disabled = !weaponGradeSelect.value;
      weaponPresetSelect.disabled = true;
      if (weaponGradeSelect.value) {
        const roles = [...new Set(weaponPresets
          .filter(weapon => weapon.grade === weaponGradeSelect.value)
          .map(weapon => weapon.roleTag))];
        roles.forEach(role => weaponRoleSelect.add(new Option(role, role)));
      }
      clearWeaponStats();
      calc();
    }

    function adjustSubInput(inputId, delta) {
      const input = document.getElementById(inputId);
      if (!input) return;
      input.value = String((parseInt(input.value, 10) || 0) + delta);
      handleSubInput(input);
    }

    function updateWeaponRole() {
      weaponPresetSelect.replaceChildren(new Option('请选择', ''));
      weaponPresetSelect.disabled = !weaponGradeSelect.value || !weaponRoleSelect.value;
      if (!weaponPresetSelect.disabled) {
        weaponPresets
          .filter(weapon => weapon.grade === weaponGradeSelect.value && weapon.roleTag === weaponRoleSelect.value)
          .forEach(weapon => weaponPresetSelect.add(new Option(weapon.name, weapon.id)));
      }
      clearWeaponStats();
      calc();
    }

    function clearWeaponStats() {
      document.getElementById('weapon_base_label').textContent = '基础攻击力';
      document.getElementById('weapon_base_value').value = 0;
      document.getElementById('weapon_sub_type').value = '—';
      document.getElementById('weapon_sub_val').value = 0;
    }

    function updateWeaponSelection() {
      const weapon = weaponPresets.find(item => item.id === weaponPresetSelect.value);
      const baseKind = weapon ? (weapon.baseKind ?? 'atk') : 'atk';
      document.getElementById('weapon_base_label').textContent = baseKind === 'def' ? '基础防御力' : '基础攻击力';
      document.getElementById('weapon_base_value').value = weapon
        ? (baseKind === 'def' ? weapon.baseDefense : weapon.baseAttack)
        : 0;
      document.getElementById('weapon_sub_type').value = weapon
        ? displayEnergyAttributeLabel(weapon.substat.label)
        : '—';
      document.getElementById('weapon_sub_val').value = weapon?.substat.value ?? 0;
      calc();
    }

    function resetWeaponSelection() {
      weaponGradeSelect.value = '';
      weaponRoleSelect.replaceChildren(new Option('请选择', ''));
      weaponRoleSelect.disabled = true;
      weaponPresetSelect.replaceChildren(new Option('请选择', ''));
      weaponPresetSelect.disabled = true;
      clearWeaponStats();
      calc();
    }

    let activePanelMode = new URLSearchParams(location.search).get('mode') || 'standard';
    if (!Object.hasOwn(panelModeLabels, activePanelMode)) activePanelMode = 'standard';

    function updatePanelMode(mode) {
      activePanelMode = mode;
      document.getElementById('rupture_result').hidden = mode !== 'rupture';
      document.getElementById('fengyu_result').hidden = mode !== 'fengyu';
      document.getElementById('fengyu_blast_result').hidden = mode !== 'fengyu';
      document.getElementById('base_pr_field').hidden = mode === 'rupture';
      document.getElementById('base_er_field').hidden = mode === 'rupture';
      document.getElementById('base_penforce_field').hidden = mode !== 'rupture';
      document.getElementById('base_energy_accumulation_field').hidden = mode !== 'rupture';
      updateEnergyAttributeLabels(mode);
    }

    function displayEnergyAttributeLabel(label, mode = activePanelMode) {
      if (mode !== 'fengyu') return label;
      return label
        .replaceAll('基础能量自动回复', '基础锐能自动累积')
        .replaceAll('能量自动回复', '锐能自动累积')
        .replaceAll('能量回复', '锐能自动累积');
    }

    function updateEnergyAttributeLabels(mode) {
      const label = mode === 'fengyu' ? '锐能自动累积' : '能量自动回复';
      document.querySelector('#base_er_field label').textContent = label;
      document.querySelector('#r_er').closest('.r-row').querySelector('.r-label').textContent =
        mode === 'fengyu' ? '锐能自动累积' : '能量回复';

      document.querySelectorAll('#core1, #core2, #disc4, #disc5, #disc6, #set0, #set1, #set2')
        .forEach(select => {
          Array.from(select.options).forEach(option => {
            if (!option.dataset.standardLabel) option.dataset.standardLabel = option.textContent;
            option.textContent = displayEnergyAttributeLabel(option.dataset.standardLabel, mode);
          });
        });
    }

    AGENT_PRESETS.forEach(agent => {
      const option = document.createElement('option');
      option.value = agent.id;
      const tags = [...new Set([agent.roleTag, panelModeLabels[agent.panelMode]].filter(Boolean))];
      option.textContent = `${agent.name}（${tags.join(' / ')}）`;
      agentPresetSelect.append(option);
    });
    updatePanelMode(activePanelMode);

    function clearAgentPresetFields() {
      const baseFieldIds = [
        'base_hp', 'base_atk', 'base_def', 'base_impact', 'base_cr',
        'base_cd', 'base_ac', 'base_am', 'base_pr', 'base_er',
      ];
      baseFieldIds.forEach(id => {
        const input = document.getElementById(id);
        input.value = input.defaultValue;
      });
      document.getElementById('base_penforce').value = '0';
      document.getElementById('base_energy_accumulation').value = '0';
      document.getElementById('core1').value = '-1';
      document.getElementById('core2').value = '-1';
      for (let i = 0; i < 3; i++) {
        document.getElementById(`set${i}`).value = '-1';
      }
      appliedAgentPresetId = '';
    }

    function updateAgentRole() {
      agentPresetSelect.replaceChildren(new Option('请选择代理人', ''));
      agentPresetSelect.disabled = !agentRoleSelect.value;

      if (agentRoleSelect.value) {
        AGENT_PRESETS
          .filter(agent => agent.roleTag === agentRoleSelect.value)
          .forEach(agent => agentPresetSelect.add(new Option(agent.name, agent.id)));
      }

      if (appliedAgentPresetId) clearAgentPresetFields();
      const requestedMode = new URLSearchParams(location.search).get('mode');
      updatePanelMode(Object.hasOwn(panelModeLabels, requestedMode) ? requestedMode : 'standard');
      resetWeaponSelection();
      document.getElementById('agent_preset_note').textContent = agentRoleSelect.value
        ? `已筛选“${agentRoleSelect.value}”标签，请选择具体代理人载入基础面板和核心加成；确认代理人后音擎与套装选择会重置。`
        : '请先选择代理人标签，再选择具体代理人。';
      document.getElementById('agent_preset_note').style.color = '';
      calc();
    }

    function applyAgentPreset(agentId) {
      const note = document.getElementById('agent_preset_note');
      resetWeaponSelection();
      if (!agentId) {
        if (appliedAgentPresetId) clearAgentPresetFields();
        const requestedMode = new URLSearchParams(location.search).get('mode');
        updatePanelMode(Object.hasOwn(panelModeLabels, requestedMode) ? requestedMode : 'standard');
        note.textContent = agentRoleSelect.value
          ? `已筛选“${agentRoleSelect.value}”标签，请选择具体代理人载入基础面板和核心加成。`
          : '请先选择代理人标签，再选择具体代理人。';
        note.style.color = '';
        calc();
        return;
      }

      const agent = AGENT_PRESETS.find(item => item.id === agentId);
      if (!agent) {
        note.textContent = `代理人预设加载失败：找不到“${agentId}”的数据。`;
        note.style.color = '#dc2626';
        console.error(note.textContent);
        return;
      }
      if (!agentRoleSelect.value || agent.roleTag !== agentRoleSelect.value) {
        agentPresetSelect.value = '';
        note.textContent = `代理人预设加载失败：“${agent.name}”不属于当前选择的“${agentRoleSelect.value || '无'}”标签。请先选择正确标签。`;
        note.style.color = '#dc2626';
        console.error(note.textContent);
        return;
      }

      try {
        const baseFields = {
          hp: 'base_hp',
          atk: 'base_atk',
          def: 'base_def',
          impact: 'base_impact',
          cr: 'base_cr',
          cd: 'base_cd',
          ac: 'base_ac',
          am: 'base_am',
          pr: 'base_pr',
          er: 'base_er',
        };
        const unavailableBaseStats = new Set(agent.unavailableBaseStats || []);
        Object.entries(baseFields).forEach(([key, inputId]) => {
          const value = agent.base?.[key];
          if (!Number.isFinite(value) && !unavailableBaseStats.has(key)) {
            throw new Error(`${agent.name}的基础面板缺少有效的${key}数值。`);
          }
        });
        const extraBaseFields = {
          penforce: 'base_penforce',
          energyAccumulation: 'base_energy_accumulation',
        };
        Object.entries(agent.additionalBaseStats || {}).forEach(([key, value]) => {
          if (!extraBaseFields[key] || !Number.isFinite(value)) {
            throw new Error(`${agent.name}包含无法识别的额外基础属性“${key}”。`);
          }
        });
        if (agent.panelMode === 'rupture' &&
            Object.keys(extraBaseFields).some(key =>
              !Number.isFinite(agent.additionalBaseStats?.[key])
            )) {
          throw new Error(`${agent.name}的命破基础面板缺少官方基础贯穿力或闪能自动累积数值。`);
        }

        if (!Array.isArray(agent.coreBonuses) || agent.coreBonuses.length === 0) {
          throw new Error(`${agent.name}缺少有效的核心加成数据。`);
        }
        if (!Object.hasOwn(panelModeLabels, agent.panelMode)) {
          throw new Error(`${agent.name}缺少有效的计算类型标签。`);
        }
        const coreIndexes = [];
        agent.coreBonuses.forEach(bonus => {
          const index = CORE_OPTIONS.findIndex(option => option.id === bonus.optionId);
          const option = CORE_OPTIONS[index];
          const optionCount = bonus.optionCount ?? 1;
          if (!option || !Number.isInteger(optionCount) || optionCount < 1 ||
              !Number.isFinite(bonus.totalValue) ||
              Math.abs(option.value * optionCount - bonus.totalValue) > 0.0000001) {
            throw new Error(`${agent.name}的核心加成“${bonus.label}”无法由当前核心选项准确表示。`);
          }
          if (!Array.isArray(bonus.ranks) || bonus.ranks.length === 0 ||
              !Number.isFinite(bonus.perRankValue) ||
              Math.abs(bonus.perRankValue * bonus.ranks.length - bonus.totalValue) > 0.0000001) {
            throw new Error(`${agent.name}的核心加成“${bonus.label}”数据不一致。`);
          }
          for (let count = 0; count < optionCount; count++) coreIndexes.push(index);
        });
        if (coreIndexes.length !== 2) {
          throw new Error(`${agent.name}的核心加成无法准确填入两个计算器核心选项。`);
        }

        const rawUnmodeledStats = agent.unmodeledBaseStats || [];
        if (!Array.isArray(rawUnmodeledStats) || rawUnmodeledStats.some(stat =>
          typeof stat.label !== 'string' || !Number.isFinite(stat.value) || typeof stat.unit !== 'string'
        )) {
          throw new Error(`${agent.name}包含无法识别的未建模基础属性。`);
        }
        // 结构校验覆盖全部条目；仅在生成提示文案时剔除已建模的同名属性。
        const unmodeledBaseStats = rawUnmodeledStats.filter(
          stat => !MODELED_BASE_STAT_LABELS.has(stat.label)
        );

        Object.entries(baseFields).forEach(([key, inputId]) => {
          document.getElementById(inputId).value = Number.isFinite(agent.base?.[key]) ? agent.base[key] : '';
        });
        Object.values(extraBaseFields).forEach(inputId => {
          document.getElementById(inputId).value = '0';
        });
        Object.entries(agent.additionalBaseStats || {}).forEach(([key, value]) => {
          document.getElementById(extraBaseFields[key]).value = value;
        });
        document.getElementById('core1').value = String(coreIndexes[0]);
        document.getElementById('core2').value = String(coreIndexes[1]);
        updatePanelMode(agent.panelMode);
        for (let i = 0; i < 3; i++) {
          document.getElementById(`set${i}`).value = '-1';
        }

        const unavailableVisibleStats = [...unavailableBaseStats].filter(
          key => agent.panelMode !== 'rupture' || !['pr', 'er'].includes(key)
        );
        const unavailableSummary = unavailableVisibleStats.length
          ? `官方基础面板未提供${unavailableVisibleStats.map(key => ({
            pr: '穿透率',
            er: displayEnergyAttributeLabel('能量自动回复', agent.panelMode),
          }[key] || key)).join('、')}。`
          : '';
        const agentTags = [...new Set([agent.roleTag, panelModeLabels[agent.panelMode]].filter(Boolean))];
        const coreSummary = agent.coreBonuses.map(bonus =>
          `${bonus.ranks.join('/')}：${bonus.label}每级 +${fmt(bonus.perRankValue)}${bonus.unit}，合计 +${fmt(bonus.totalValue)}${bonus.unit}`
        ).join('；');
        const unmodeledSummary = unmodeledBaseStats.length
          ? `官方还列有当前计算器尚未建模的属性：${unmodeledBaseStats.map(stat => `${stat.label} ${fmt(stat.value)}${stat.unit}`).join('、')}。`
          : '';
        note.replaceChildren(
          document.createTextNode(`已载入${agent.name}（${agentTags.join(' / ')}）的60级基础面板（不含核心）及满级核心加成。${coreSummary}。${unavailableSummary}${unmodeledSummary}数据来源：`)
        );
        const sourceLink = document.createElement('a');
        sourceLink.href = agent.source;
        sourceLink.target = '_blank';
        sourceLink.rel = 'noopener noreferrer';
        sourceLink.textContent = '米游社官方WIKI';
        note.append(sourceLink);
        note.style.color = '';
        appliedAgentPresetId = agent.id;
        calc();
      } catch (error) {
        note.textContent = `代理人预设加载失败：${error.message}`;
        note.style.color = '#dc2626';
        console.error(error);
      }
    }

    function handleSubInput(el) {
      el.value = Math.min(36, Math.max(0, Math.floor(parseFloat(el.value) || 0)));
      const total = Array.from(document.querySelectorAll('#sub_grid input')).reduce((sum, input) => sum + (parseInt(input.value, 10) || 0), 0);
      if (total > 54) {
        const current = parseInt(el.value, 10) || 0;
        const reduced = Math.max(0, current - (total - 54));
        el.value = reduced;
      }
      calc();
    }

    /* ====== 固有属性（不随任何词条、音擎或套装变化） ====== */
    // 锋御代理人「锐暴伤害」为固有属性，恒定 150%，不参与任何加成与修正计算。
    const FENGYU_BLAST_DMG = 150;
    // 官方 WIKI 基础面板中与上述固有属性同名的条目。已在最终面板中固定展示，
    // 因此不再计入「尚未建模的属性」提示。预设数据重新生成并将其移入建模字段后，
    // 可从本集合移除。
    const MODELED_BASE_STAT_LABELS = new Set(['锐暴伤害']);

    /* ====== 计算逻辑 ====== */
    function num(id) {
      const el = document.getElementById(id);
      if (!el) return 0;
      const v = parseFloat(el.value);
      return isNaN(v) ? 0 : v;
    }
    function sel(id) {
      return parseInt(document.getElementById(id).value);
    }
    function fmt(n) {
      const fixed = Number(n.toFixed(10));
      if (Math.abs(fixed - Math.round(fixed)) < 0.0000001) return Math.round(fixed).toLocaleString();
      return Number(fixed.toFixed(2)).toString();
    }

    function calc() {
      // 1. 基础面板
      const baseHp = num('base_hp');
      const baseAtk = num('base_atk');
      const baseDef = num('base_def');
      const baseCr = num('base_cr');
      const baseCd = num('base_cd');
      const basePr = num('base_pr');
      const baseImpact = num('base_impact');
      const baseAc = num('base_ac');
      const baseAm = num('base_am');
      const baseEr = num('base_er');

      // 2. 武器（锋御音擎提供基础防御力，其余提供基础攻击力）
      const weaponBaseValue = num('weapon_base_value');
      const weapon = weaponPresets.find(item => item.id === weaponPresetSelect.value);
      const weaponBaseKind = weapon ? (weapon.baseKind ?? 'atk') : 'atk';
      const wAtk = weapon && weaponBaseKind === 'atk' ? weaponBaseValue : 0;
      const wDef = weapon && weaponBaseKind === 'def' ? weaponBaseValue : 0;
      const wSubVal = num('weapon_sub_val');

      // 3. 核心（2选）
      const core1 = CORE_OPTIONS[sel('core1')];
      const core2 = CORE_OPTIONS[sel('core2')];
      const corePicks = [core1, core2];

      // 累加器
      const S = {
        // 攻防血
        hp_pct: 0, atk_pct: 0, def_pct: 0,
        hp_flat: 0, atk_flat: 0, def_flat: 0,
        hp_base: 0, atk_base: 0, def_base: 0,  // 核心基础值（进入基础面板）
        // 纯加法
        cr: 0, cd: 0, dmg: 0, pr: 0,
        pen_val: 0, am: 0,
        ac_flat: 0, ac_pct: 0,
        impact_flat: 0, impact_pct: 0,
        er_flat: 0, er_pct: 0,
      };

      // 来源记录
      const src = {
        hp_pct: [], atk_pct: [], def_pct: [],
        hp_flat: [], atk_flat: [], def_flat: [], hp_base: [],
        cr: [], cd: [], dmg: [], pr: [], pen_val: [], am: [],
        ac_flat: [], ac_pct: [], impact_flat: [], impact_pct: [], er_flat: [], er_pct: [],
      };
      function add(key, val, label) {
        if (val === undefined || val === 0) return;
        S[key] = (S[key] || 0) + val;
        if (label) src[key] = (src[key] || []).concat(label);
      }

      // 核心
      const coreLabels = [];
      corePicks.forEach((c, i) => {
        if (!c) return;
        const lb = `核心${i + 1}(${displayEnergyAttributeLabel(c.label)})`;
        coreLabels.push(lb);
        if (c.kind === 'base') {
          // 基础攻击力/防御力 → 进入基础面板
          add(c.to, c.value, lb);
        } else if (c.kind === 'pct') {
          add(c.to, c.value, lb);
        } else {
          add(c.to, c.value, lb);
        }
      });

      // 武器副词条
      if (weapon && wSubVal) {
        add(
          weapon.substat.to,
          wSubVal,
          `音擎固定副词条(${displayEnergyAttributeLabel(weapon.substat.label)} ${wSubVal}${weapon.substat.kind === 'pct' ? '%' : ''})`
        );
      }

      // 驱动盘主词条 1/2/3 固定
      add('hp_flat', 2200, '1号固定生命+2200');
      add('atk_flat', 316, '2号固定攻击+316');
      add('def_flat', 184, '3号固定防御+184');
      // 4/5/6
      const d4 = DISC4_OPTIONS[sel('disc4')];
      const d5 = DISC5_OPTIONS[sel('disc5')];
      const d6 = DISC6_OPTIONS[sel('disc6')];
      if (d4) add(d4.to, d4.value, `4号(${d4.label})`);
      if (d5) add(d5.to, d5.value, `5号(${d5.label})`);
      if (d6) add(d6.to, d6.value, `6号(${displayEnergyAttributeLabel(d6.label)})`);

      // 副词条（按条数 × 单条数值）
      let subTotal = 0;
      const subFixed = { hp_flat: 0, atk_flat: 0, def_flat: 0 };
      SUB_STATS.forEach(s => {
        const cnt = Math.max(0, Math.floor(num('sub_' + s.id)));
        subTotal += cnt;
        const val = cnt * s.value;
        if (cnt > 0) {
          add(s.to, val, `副词条·${s.label}×${cnt}=${fmt(val)}${s.kind === 'pct' ? '%' : ''}`);
          if (Object.hasOwn(subFixed, s.to)) subFixed[s.to] += val;
          document.getElementById('sub_v_' + s.id).textContent = (s.kind === 'pct' ? fmt(val) + '%' : fmt(val));
        } else {
          document.getElementById('sub_v_' + s.id).textContent = '0';
        }
      });
      SUB_STATS.forEach(s => {
        const input = document.getElementById('sub_' + s.id);
        input.parentElement.querySelector('[data-delta="-1"]').disabled =
          Math.max(0, Math.floor(num(input.id))) <= 0;
        input.parentElement.querySelector('[data-delta="1"]').disabled =
          Math.max(0, Math.floor(num(input.id))) >= 36 || subTotal >= 54;
      });
      document.getElementById('sub_total').textContent = subTotal;
      if (subTotal > 54) {
        document.getElementById('sub_total').style.color = '#ef4444';
      } else {
        document.getElementById('sub_total').style.color = '#111827';
      }

      // 二件套（0~3组）
      for (let i = 0; i < 3; i++) {
        const idx = sel('set' + i);
        if (idx >= 0 && idx < SET_OPTIONS.length) {
          const st = SET_OPTIONS[idx];
          add(st.to, st.value, `2件套·${displayEnergyAttributeLabel(st.label)}`);
        }
      }

      /* ====== 最终面板 ====== */
      // 攻防血：(基础 + 核心基础值 + 武器基础值) × (1 + 百分比) + 固定值
      const atkBase = baseAtk + S.atk_base + wAtk;
      const defBase = baseDef + S.def_base + wDef;
      const hpBase = baseHp + S.hp_base;

      const totalHp = hpBase * (1 + S.hp_pct / 100) + S.hp_flat;
      const totalAtk = atkBase * (1 + S.atk_pct / 100) + S.atk_flat;
      const totalDef = defBase * (1 + S.def_pct / 100) + S.def_flat;
      const totalPenForce = 0.3 * totalAtk + 0.1 * totalHp;

      // 纯加法
      const totalCr = baseCr + S.cr;
      const totalCd = baseCd + S.cd;
      const actualCr = totalCd * 0.35 + totalCr;
      const blastDmg = activePanelMode === 'fengyu' ? FENGYU_BLAST_DMG : null;
      const totalDmg = S.dmg;
      const totalPr = basePr + S.pr;
      const totalPv = S.pen_val;
      const totalAm = baseAm + S.am;
      const totalAc = (baseAc + S.ac_flat) * (1 + S.ac_pct / 100);
      const totalImp = (baseImpact + S.impact_flat) * (1 + S.impact_pct / 100);
      const totalEr = (baseEr + S.er_flat) * (1 + S.er_pct / 100);

      // 渲染
      document.getElementById('r_hp').textContent = fmt(totalHp);
      document.getElementById('r_atk').textContent = fmt(totalAtk);
      document.getElementById('r_def').textContent = fmt(totalDef);
      document.getElementById('r_penforce').textContent = fmt(totalPenForce);
      document.getElementById('r_actual_cr').textContent = fmt(actualCr) + '%';
      document.getElementById('r_blast_dmg').textContent = blastDmg === null ? '—' : fmt(blastDmg) + '%';
      document.getElementById('r_cr').textContent = fmt(totalCr) + '%';
      document.getElementById('r_cd').textContent = fmt(totalCd) + '%';
      document.getElementById('r_dmg').textContent = fmt(totalDmg) + '%';
      document.getElementById('r_pr').textContent = fmt(totalPr) + '%';
      document.getElementById('r_pv').textContent = fmt(totalPv);
      document.getElementById('r_am').textContent = fmt(totalAm);
      document.getElementById('r_ac').textContent = fmt(totalAc);
      document.getElementById('r_imp').textContent = fmt(totalImp);
      document.getElementById('r_er').textContent = fmt(totalEr);

      // 明细
      const escapeHtml = value => value.replace(/[&<>"']/g, char => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
      })[char]);
      const j = arr => arr.map(value =>
        `<span class="breakdown-item">${escapeHtml(value.replace(/ ([0-9])/g, '\u00a0$1'))}</span>`
      ).join(' + ') || '无';
      const fixedBreakdown = (main, sub, mainLabel) =>
        `${fmt(main)}（${mainLabel}）+${fmt(sub)}（副词条）`;
      document.getElementById('b_hp').innerHTML = `<span class="breakdown-line">(${fmt(baseHp)}${S.hp_base ? `+核心${fmt(S.hp_base)}` : ''})×(1+<span class="kw">${fmt(S.hp_pct)}%</span>)</span><span class="breakdown-line">+${fixedBreakdown(2200, subFixed.hp_flat, '1号主词条')} = <b>${fmt(totalHp)}</b></span>`;
      document.getElementById('b_atk').innerHTML = `<span class="breakdown-line">(${fmt(baseAtk)}${S.atk_base ? `+核心${fmt(S.atk_base)}` : ''}+音擎${fmt(wAtk)})</span><span class="breakdown-line">×(1+<span class="kw">${fmt(S.atk_pct)}%</span>)+${fixedBreakdown(316, subFixed.atk_flat, '2号主词条')} = <b>${fmt(totalAtk)}</b></span>`;
      document.getElementById('b_def').innerHTML = `<span class="breakdown-line">(${fmt(baseDef)}${S.def_base ? `+核心${fmt(S.def_base)}` : ''}+音擎${fmt(wDef)})</span><span class="breakdown-line">×(1+<span class="kw">${fmt(S.def_pct)}%</span>)+${fixedBreakdown(184, subFixed.def_flat, '3号主词条')} = <b>${fmt(totalDef)}</b></span>`;
      document.getElementById('b_penforce').innerHTML = `<span class="breakdown-line">0.3×${fmt(totalAtk)} + 0.1×${fmt(totalHp)}</span><span class="breakdown-line">= <b>${fmt(totalPenForce)}</b></span>`;
      document.getElementById('b_cr').innerHTML = `${baseCr}% + ${j(src.cr)} = ${fmt(totalCr)}%`;
      document.getElementById('b_actual_cr').innerHTML = `<span class="breakdown-line">${fmt(totalCd)}%×35% + ${fmt(totalCr)}%</span><span class="breakdown-line">= <b>${fmt(actualCr)}%</b></span>`;
      document.getElementById('b_blast_dmg').innerHTML = blastDmg === null
        ? ''
        : `<span class="breakdown-line">固有属性，不受词条、音擎与套装影响</span><span class="breakdown-line">= <b>${fmt(blastDmg)}%</b></span>`;
      document.getElementById('b_cd').innerHTML = `${baseCd}% + ${j(src.cd)} = ${fmt(totalCd)}%`;
      document.getElementById('b_dmg').innerHTML = `${j(src.dmg)} = ${fmt(totalDmg)}%`;
      document.getElementById('b_pr').innerHTML = `${basePr}% + ${j(src.pr)} = ${fmt(totalPr)}%`;
      document.getElementById('b_pv').innerHTML = `${j(src.pen_val)} = ${fmt(totalPv)}`;
      document.getElementById('b_am').innerHTML = `${baseAm ? `基础${fmt(baseAm)} + ` : ''}${j(src.am)} = ${fmt(totalAm)}`;
      const anomalyBaseParts = [`基础${fmt(baseAc)}`, ...src.ac_flat];
      document.getElementById('b_ac').innerHTML = `<span class="breakdown-line">(${j(anomalyBaseParts)})×(1+<span class="kw">${fmt(S.ac_pct)}%</span>)</span><span class="breakdown-line">${j(src.ac_pct)} = <b>${fmt(totalAc)}</b></span>`;
      const impactBaseParts = [`基础${fmt(baseImpact)}`, ...src.impact_flat];
      document.getElementById('b_imp').innerHTML = `<span class="breakdown-line">(${j(impactBaseParts)})×(1+<span class="kw">${fmt(S.impact_pct)}%</span>)</span><span class="breakdown-line">${j(src.impact_pct)} = <b>${fmt(totalImp)}</b></span>`;
      const energyBaseParts = [`基础${fmt(baseEr)}`, ...src.er_flat];
      document.getElementById('b_er').innerHTML = `<span class="breakdown-line">(${j(energyBaseParts)})×(1+<span class="kw">${fmt(S.er_pct)}%</span>)</span><span class="breakdown-line">${j(src.er_pct)} = <b>${fmt(totalEr)}</b></span>`;

      // 核心摘要
      document.getElementById('core_summary').innerHTML = coreLabels.length
        ? `已选：${coreLabels.join('，')}`
        : '<span style="color:#dc2626">未选择核心</span>';
    }

    function resetAll() { location.reload(); }

    // 实时计算
    document.addEventListener('input', calc);
    document.addEventListener('change', calc);
    calc();
