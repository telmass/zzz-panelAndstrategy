/**
 * 执行 legacy 的 `fmt`，供 backend/tests/test_fmt_parity.py 取期望值。
 * 用法：node _fmt_driver.cjs <calculator.js 路径> <JSON 数值数组>
 */
const fs = require('fs');

const src = fs.readFileSync(process.argv[2], 'utf8');

// legacy 的 fmt 嵌套在另一个函数内，缩进 4 空格，函数体以 `\n    }` 结束。
const match = src.match(/function fmt\(n\) \{[\s\S]*?\n {4}\}/);
if (!match) {
  console.error('未能从 calculator.js 提取 fmt');
  process.exit(2);
}
eval(match[0]);

const values = JSON.parse(process.argv[3]);
process.stdout.write(JSON.stringify(values.map((v) => fmt(v))));
