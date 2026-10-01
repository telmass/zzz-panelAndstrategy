"""预留：预设数据加载与校验。

计划中的文件：
- ``loader.py``   读取仓库根 ``data/*.json``，按 mtime 缓存
- ``validate.py`` 迁移 ``frontend/legacy/scripts/calculator.js:47-58`` 的
  防御性校验（缺 roleTag、重复 id、核心加成无法由选项表示等），
  改为启动时一次性校验，失败即报错
"""
