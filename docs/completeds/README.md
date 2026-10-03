# 已完成事项归档

本目录存放**所描述的任务已全部完成**的文档。

> ⚠️ **归档文档不描述当前状态，只记录已完成的过程。**
> 想知道项目现在是什么样，请看上一级的文档，不要读这里。

## 归档清单

| 文档 | 归档原因 | 替代它的当前文档 |
| --- | --- | --- |
| [migration-vue3.md](migration-vue3.md) | Vue3 迁移 6 个步骤全部完成（2026-10-03） | [requirements.md](../requirements.md)、[architecture.md](../architecture.md) |
| [legacy-pages.md](legacy-pages.md) | `frontend/legacy/` 与根目录 6 个重定向页已全部删除（2026-10-03） | [directory-layout.md](../directory-layout.md) 第 4 节 |

## 各文档的价值

### migration-vue3.md

迁移的**全过程记录**：每一步的产出文件、验收标准、当时踩的坑、
以及逐步的「已验证」结论。

它的价值主要在两处：

1. **`legacy-parity.spec.ts` 的 jsdom 作用域问题**记录在第 2 步
   「测试中的两个坑」里。那两个坑（必须 `runScripts: 'dangerously'`、
   多脚本必须合并为一段内联脚本）至今仍在生效，改对拍测试前必读。
2. **决策理由**。例如为什么预设走接口而规则表走本地、为什么 `to-legacy`
   要做成字节幂等——这些在当前文档里只留了结论，过程与取舍在这里。

### legacy-pages.md

旧原生页面的**来历与删除记录**：文件对照表、逐页去向、维护约束。

其中的「迁移期已知特性」一节仍然有效——尤其是
**`scripts/calculator-config.js` 是数据抓取脚本的正则解析源**，
改它的格式会让抓取脚本静默失效。

## 归档时该做什么

归档一份文档时：

1. `git mv docs/<name>.md docs/completeds/<name>.md`（保留历史）
2. 搜索所有指向它的链接，改为新路径
   ```powershell
   Select-String -Path (Get-ChildItem -Recurse -File -Include *.md).FullName -Pattern 'migration-vue3'
   ```
3. 更新 [../README.md](../README.md) 的索引，注明已归档及替代文档
4. 检查文档内部的相对链接：深度多了一层，`../` 需要相应增加
5. 在 [../changelog.md](../changelog.md) 记一笔

## 相关文档

- [../README.md](../README.md) —— 文档总索引
- [../changelog.md](../changelog.md) —— 变更记录
- [../requirements.md](../requirements.md) —— 当前项目范围与已知限制