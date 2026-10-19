import { computed } from 'vue';

import { CORE_OPTIONS } from '@/constants/calculatorOptions';
import { displayEnergyAttributeLabel } from '@/composables/usePanelMode';
import { usePanelStore } from '@/stores/panelStore';

type CoreOption = (typeof CORE_OPTIONS)[number];

function optionById(options: typeof CORE_OPTIONS, id: string): CoreOption | undefined {
  return options.find((option) => option.id === id);
}

/**
 * 核心选择摘要（对应 legacy 的 `core_summary`）。
 *
 * 轻量 composable：只读 store，不发请求、不建防抖——
 * CoreModule 无需实例化完整的 usePanelCalc。
 */
export function useCoreSummary() {
  const panel = usePanelStore();

  const coreSummary = computed(() => {
    const mode = panel.panelMode;
    const picks = [optionById(CORE_OPTIONS, panel.core.core1), optionById(CORE_OPTIONS, panel.core.core2)];
    const labels = picks
      .map((option, index) =>
        option ? `核心${index + 1}(${displayEnergyAttributeLabel(option.label, mode)})` : '',
      )
      .filter(Boolean);
    return labels.length ? `已选：${labels.join('，')}` : '<span style="color:#dc2626">未选择核心</span>';
  });

  return { coreSummary };
}
