# cet46-translation

四级 / 六级段落翻译技能：用基础词汇把中文段落译成英文，目标六级翻译 10–12 分档。

## 它做什么

- 按「拆信息点 → 定主干 → 降级词汇 → 控制句式 → 回填核对」流程翻译
- 提供难词替换表、中文句式模板、评分档位说明
- 附带表层筛查脚本，检查中文标点、主谓一致、冠词、数字缺失、句数骤减、无理由的句间时态切换

## 它不做什么

- 不判断语义是否完整
- 不判断搭配是否地道
- 不给真实分数；`band` 只是筛查值
- `pass` 只表示没有抓到表层硬错，不代表译文合格

## 使用

把本目录放到 `<workspace>/.trae/skills/cet46-translation/`，或安装 zip 包。

```bash
python scripts/check_translation.py --source 原文.txt --target 译文.txt
python scripts/check_translation.py --batch
python scripts/check_translation.py --batch --json
```

## 目录结构

```text
cet46-translation/
├── SKILL.md
├── references/
│   ├── scoring-guide.md
│   ├── word-swap.md
│   └── sentence-patterns.md
├── scripts/
│   └── check_translation.py
└── assets/
    └── test-cases.json
```

## 已知局限

1. 句数骤减只能提示，合并句与漏译无法自动区分
2. 时态检查按句判断，句内时态混用查不出
3. 主谓一致只覆盖常见代词与基础动词
4. 语义完整性依赖人工信息点核对
5. 命中但正确的表达应保留原文，不做自动改写

## License

MIT
