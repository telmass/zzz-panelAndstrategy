/**
 * 测试里没有安装真实 router，`RouterLink` 拿不到注入的 router 实例。
 * 统一用这个只渲染 `to` 的 `<a>` 桩，断言 `href` 即可验证跳转目标，
 * 避免每个 mount 点各写一份。
 */
export const RouterLinkStub = {
  name: 'RouterLink',
  props: ['to'],
  template: '<a :href="to"><slot /></a>',
};
