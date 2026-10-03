/**
 * 指南页（/guide）的展示组件。内容来自 legacy/pages/guide.html，
 * 这里只拆出重复出现的四类结构（章节、提示框、属性网格、表格），
 * 具体文字与单元格内容仍由 GuideView 持有。
 */

export { default as GuideAttrGrid } from './GuideAttrGrid.vue';
export { default as GuideCallout } from './GuideCallout.vue';
export { default as GuideSection } from './GuideSection.vue';
export { default as GuideTable } from './GuideTable.vue';
