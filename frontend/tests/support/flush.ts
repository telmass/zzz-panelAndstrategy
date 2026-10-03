/** 测试公用等待工具。 */

/**
 * 等一次防抖计算完成。
 *
 * `usePanelCalc` 有 200ms 防抖，因此断言前必须等过防抖窗口 + 一次微任务 +
 * 一次网络往返。分成三段 await 是为了让 Vue 的响应式刷新先落定，
 * 再让 promise 结果回来，最后再触发一次渲染。
 */
export async function flushCalc(): Promise<void> {
  // 越过防抖窗口
  await new Promise((r) => setTimeout(r, 260));
  // 等待 fetch promise 落定
  await Promise.resolve();
  await new Promise((r) => setTimeout(r, 0));
  // 触发 Vue 重新渲染
  await new Promise((r) => setTimeout(r, 0));
}
