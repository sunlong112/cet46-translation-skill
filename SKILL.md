---
name: cet46-translation
description: Translate Chinese exam passages into simple, accurate English for CET-4/CET-6. Use when the user asks for 四级/六级翻译, CET translation practice, or plain-English rendering. Not for literary translation.
---

# 四六级翻译（简单词汇版）

把中文段落译成**只用基础词汇、语义完整**的英文，稳定落在六级翻译 10–12 分档。

## 适用与边界

- 适用：四级/六级段落翻译、真题练习、译文批改。
- 不适用：文学翻译、追求文采的润色、英译中。

## 铁律

1. **语义优先**：原文信息点一个都不能丢；宁可句子短，不可意思缺。
2. **词汇降级**：主动避开六级难词，替换表见 `references/word-swap.md`。
3. **句式降级**：以简单句为主；一句最多一个从句；禁止倒装、虚拟语气、独立主格、插入语。
4. **不增不删**：不加原文没有的评价、背景或议论性连接。
5. **长度控制**：单句 ≤ 20 词，平均句长 12–18 词。

## 执行流程

### 1. 拆信息点

按「谁—做什么—结果/评价」把原文切成编号信息点。中文一个逗号长链常含 2–3 个信息点，不要合并成一句。

### 2. 逐点定主干

每个信息点先写「主语 + 谓语 + 宾语」。先保证对，再谈顺。无主句补主语：中国 / 人们 / 我们 / 政府。

### 3. 词汇降级

按 `references/word-swap.md` 把六级词换成四级词：utilize→use，approximately→about，numerous→many，enhance→improve。文化词用「拼音或常用译名 + 类别词」：剪纸 paper cutting，长城 the Great Wall。

### 4. 句式控制

- 一句话只放一个信息点；最多一个定语从句或状语从句。
- 中文排比 → 拆成并列简单句。
- 中文四字词 → 译意思，不译字面。
- 时态：历史用过去时，现状用现在时，变化用现在完成时。

### 5. 回填核对

逐条比对信息点清单与译文：顺序可调，**一个都不能少**；数字、人名、地名、年代必须对上。

### 6. 语法自检

主谓一致、单复数、冠词、时态统一、拼写。中文标点必须清干净。

### 7. 机器自检

```bash
python scripts/check_translation.py --source 原文.txt --target 译文.txt
```

输出 `score` / `band` / `issues`。出现 critical 必须改到 0 再交付；band 不是 10–12 就继续降级词汇。

### 8. 输出格式

```text
【译文】
……

【信息点核对】
- 信息点 1 → 对应译文片段 ✓
- 信息点 2 → ……

【自评】六级 10–12 分档｜替换难词 X 处｜最长句 Y 词
```

## 高频扣分点

- 主谓不一致；时态一句一变
- 无主句不补主语
- 成语四字词逐字直译
- 专有名词漏译或乱译
- 数字、人名、年代丢失
- although 与 but、because 与 so 同时出现
- 一篇里三种时态混用

## 参考文件

- `references/scoring-guide.md` — 评分档位与 10–12 分档特征
- `references/word-swap.md` — 难词 → 基础词替换表
- `references/sentence-patterns.md` — 中文常见句式转换模板
- `scripts/check_translation.py` — 译文自检脚本
- `assets/test-cases.json` — 三条样例题与参考译文
