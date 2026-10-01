"""预留：计算明细（来源追溯）生成。

必须对齐 ``frontend/legacy/scripts/calculator.js:567-583`` 的 ``b_*`` 结构，
否则 Vue3 迁移后右侧「计算明细」面板会变样。
建议输出结构化数组（``{label, value}``）而非 HTML 字符串，渲染交由前端。
"""
