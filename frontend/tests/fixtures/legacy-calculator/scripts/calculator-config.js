const CORE_OPTIONS = [
      { id: 'er_base', label: '基础能量自动回复 +0.36', value: 0.36, kind: 'flat', to: 'er_flat' },
      { id: 'atk_base', label: '基础攻击力 +75', value: 75, kind: 'base', to: 'atk_base' },
      { id: 'impact_base', label: '基础冲击力 +18', value: 18, kind: 'flat', to: 'impact_flat' },
      { id: 'cd', label: '暴击伤害 +28.8%', value: 28.8, kind: 'pct', to: 'cd' },
      { id: 'cr', label: '暴击率 +14.4%', value: 14.4, kind: 'pct', to: 'cr' },
      { id: 'hp_pct', label: '生命值百分比 +18%', value: 18, kind: 'pct', to: 'hp_pct' },
      { id: 'hp_base', label: '基础生命值 +420', value: 420, kind: 'base', to: 'hp_base' },
      { id: 'ac', label: '异常掌控 +36', value: 36, kind: 'flat', to: 'ac_flat' },
      { id: 'am', label: '异常精通 +54', value: 54, kind: 'flat', to: 'am' },
      { id: 'pr', label: '穿透率 +14.4%', value: 14.4, kind: 'pct', to: 'pr' },
      { id: 'am_90', label: '异常精通 +90', value: 90, kind: 'flat', to: 'am' },
      { id: 'atk_pct_21', label: '攻击力 +21%', value: 21, kind: 'pct', to: 'atk_pct' },
    ];

    // 4号主词条（6选1）
    const DISC4_OPTIONS = [
      { label: '攻击力 30%', value: 30, kind: 'pct', to: 'atk_pct' },
      { label: '生命值 30%', value: 30, kind: 'pct', to: 'hp_pct' },
      { label: '防御力 48%', value: 48, kind: 'pct', to: 'def_pct' },
      { label: '暴击率 24%', value: 24, kind: 'pct', to: 'cr' },
      { label: '暴击伤害 48%', value: 48, kind: 'pct', to: 'cd' },
      { label: '异常精通 92', value: 92, kind: 'flat', to: 'am' },
    ];
    // 5号主词条（5选1）
    const DISC5_OPTIONS = [
      { label: '攻击力 30%', value: 30, kind: 'pct', to: 'atk_pct' },
      { label: '生命值 30%', value: 30, kind: 'pct', to: 'hp_pct' },
      { label: '防御力 48%', value: 48, kind: 'pct', to: 'def_pct' },
      { label: '穿透率 24%', value: 24, kind: 'pct', to: 'pr' },
      { label: '增伤 30%', value: 30, kind: 'pct', to: 'dmg' },
    ];
    // 6号主词条（6选1）
    const DISC6_OPTIONS = [
      { label: '攻击力 30%', value: 30, kind: 'pct', to: 'atk_pct' },
      { label: '生命值 30%', value: 30, kind: 'pct', to: 'hp_pct' },
      { label: '防御力 48%', value: 48, kind: 'pct', to: 'def_pct' },
      { label: '冲击力 24%', value: 24, kind: 'pct', to: 'impact_pct' },
      { label: '异常掌控 30%', value: 30, kind: 'pct', to: 'ac_pct' },
      { label: '能量回复 60%', value: 60, kind: 'pct', to: 'er_pct' },
    ];

    // 副词条单条数值（10种）
    const SUB_STATS = [
      { id: 'hp_flat', label: '小生命', value: 112, kind: 'flat', to: 'hp_flat' },
      { id: 'hp_pct', label: '大生命%', value: 3, kind: 'pct', to: 'hp_pct' },
      { id: 'atk_flat', label: '小攻击', value: 19, kind: 'flat', to: 'atk_flat' },
      { id: 'atk_pct', label: '大攻击%', value: 3, kind: 'pct', to: 'atk_pct' },
      { id: 'def_flat', label: '小防御', value: 15, kind: 'flat', to: 'def_flat' },
      { id: 'def_pct', label: '大防御%', value: 4.8, kind: 'pct', to: 'def_pct' },
      { id: 'cr', label: '暴击率', value: 2.4, kind: 'pct', to: 'cr' },
      { id: 'cd', label: '暴击伤害', value: 4.8, kind: 'pct', to: 'cd' },
      { id: 'pen_val', label: '穿透值', value: 9, kind: 'flat', to: 'pen_val' },
      { id: 'am', label: '异常精通', value: 9, kind: 'flat', to: 'am' },
    ];

    // 二件套效果（10种）
    const SET_OPTIONS = [
      { label: '生命 +10%', value: 10, kind: 'pct', to: 'hp_pct' },
      { label: '攻击力 +10%', value: 10, kind: 'pct', to: 'atk_pct' },
      { label: '防御力 +10%', value: 10, kind: 'pct', to: 'def_pct' },
      { label: '暴击率 +8%', value: 8, kind: 'pct', to: 'cr' },
      { label: '暴击伤害 +16%', value: 16, kind: 'pct', to: 'cd' },
      { label: '冲击力 +6%', value: 6, kind: 'pct', to: 'impact_pct' },
      { label: '异常掌控 +8%', value: 8, kind: 'pct', to: 'ac_pct' },
      { label: '能量回复 +20%', value: 20, kind: 'pct', to: 'er_pct' },
      { label: '增伤 +10%', value: 10, kind: 'pct', to: 'dmg' },
      { label: '异常精通 +30', value: 30, kind: 'flat', to: 'am' },
    ];

    /* ====== 初始化下拉框 ====== */
