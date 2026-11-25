#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''CET-4/6 翻译译文表层筛查工具。

定位：只查能机械判断的表层错误（标点、主谓一致、冠词、数字、句数骤减等）。
它不能判断语义是否完整、搭配是否地道、是否真的落在 10-12 分档。
脚本给出的 band 是筛查参考值，不是评分。

用法：
    python check_translation.py --source 原文.txt --target 译文.txt
    python check_translation.py --case 1
    python check_translation.py --batch
    python check_translation.py --batch --json

使用原则：
    issues 必须逐条人工判断。标注正确但被脚本命中的表达，保留原文并记录为误报，
    不得为了消除告警而改写正确表达。
'''

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

BASE = Path(__file__).resolve().parent.parent
CASES_PATH = BASE / 'assets' / 'test-cases.json'

# 只收录“任何语境下都错误”的复数形式，避免 works of art 这类合法复数被误报
ALWAYS_WRONG_PLURALS = {
    'informations', 'advices', 'equipments', 'furnitures', 'knowledges',
    'luggages', 'baggages', 'homeworks', 'softwares', 'newses', 'researchs',
}

# 六级常见超纲词：仅作提示，不强制替换
ADVANCED = set('''
abundant accelerate accommodate accumulate acknowledge adequate advocate aesthetic
aggravate alleviate ambiguous anticipate arbitrary articulate assess attribute authentic
autonomous beneficial boost cease coherent coincide collapse commence commodity
compensate competent comprehensive comprise conceive concurrent confine conform
consecutive consensus considerable constitute constrain consume contemporary contradict
controversy conventional convert convey cooperate coordinate cope corporate correlate
correspond crucial cultivate cumulative decline dedicate deficiency demonstrate denote
deprive derive descend desirable deteriorate deviate devise diminish discrete
discriminate displace dispose dispute distinct distinguish distort diverse domain
domestic dominate drastic duration dynamic elaborate elevate eliminate emerge
emphasize empirical encounter endure enhance enormous entail entitle equivalent erode
evaluate eventually evident evolve exaggerate exceed exceptional excess exclude
execute exert exhibit expand explicit exploit expose extend extract facilitate
feasible fluctuate formulate foster framework fundamental generate genuine guarantee
hierarchy highlight hypothesis identical identify ideology illustrate implement imply
impose incentive incorporate indicate induce inevitable infer inhibit initiate
innovative insight integrate integrity intense interact interpret intervene intrinsic
justify legitimate magnitude maintain manipulate maximize mechanism mediate merge
minimize modify monitor motivate mutual negotiate notion objective obligation obscure
occupy offset optimal originate outcome overlap participate perceive persist
perspective phenomenon portion potential precede precise predict preliminary prescribe
preserve prevail priority proceed profound prohibit prominent promote proportion
prospect pursue radical random rational reinforce reject reluctant render resemble
reside restrict retain reveal revenue rigid scarce scenario scheme secure simultaneous
sophisticated speculate stimulate strategy subsequent subsidy substantial substitute
sufficient supplement suppress sustain tedious temporary terminate thereby thorough
transform transmit transparent tremendous trigger ultimate undergo underlying
undertake unique utilize valid vary verify viable vital vulnerable whereas widespread
yield
'''.split())

SINGULAR_VERBS = {'is', 'was', 'has', 'does', 'goes'}

BASE_VERBS = {
    'go', 'have', 'do', 'make', 'take', 'say', 'come', 'know', 'think', 'want',
    'need', 'like', 'look', 'feel', 'live', 'play', 'work', 'study', 'help',
    'seem', 'become', 'get', 'give', 'show', 'use', 'try', 'start', 'begin',
    'keep', 'find', 'tell', 'bring', 'build', 'change', 'grow', 'move',
    'produce', 'provide',
}

BE_WORDS = {'is', 'are', 'was', 'were', 'be', 'been', 'being'}

IRREGULAR_PARTICIPLES = {
    'built', 'made', 'done', 'known', 'given', 'taken', 'seen', 'shown',
    'written', 'held', 'found', 'used', 'sold', 'told',
}

CLAUSE_WORDS = {'which', 'who', 'whom', 'whose', 'where'}

COUNTRY_WORDS = {'china', 'japan', 'france', 'germany', 'india'}

A_EXCEPTIONS = {
    'university', 'european', 'one', 'useful', 'unique', 'united',
    'usual', 'uniform', 'universal', 'unit', 'us', 'uk', 'eu', 'ufo',
    'url', 'usb', 'nba', 'mba', 'hr',
}

AN_EXCEPTIONS = {'hour', 'honest', 'honor', 'honour'}

VOWELS = 'aeiou'

CN_PUNCT = set('，。；：！？、（）【】“”‘’《》')

TIME_MARKERS = {
    'now', 'today', 'yesterday', 'ago', 'since', 'recently', 'currently',
    'present', 'past', 'last', 'tomorrow',
}

IRREGULAR_PAST = {
    'went', 'came', 'took', 'made', 'said', 'saw', 'knew', 'thought', 'found',
    'gave', 'got', 'had', 'did', 'was', 'were', 'built', 'grew', 'began',
    'kept', 'left', 'met', 'paid', 'sold', 'told', 'wrote', 'read', 'ran',
    'spoke', 'bought', 'brought', 'chose', 'drove', 'ate', 'fell', 'felt',
    'flew', 'forgot', 'heard', 'held', 'lost', 'meant', 'sent', 'sat',
    'slept', 'spent', 'stood', 'taught', 'understood', 'won', 'wore',
}


def load_file(path):
    return Path(path).read_text(encoding='utf-8').strip()


def tokenize(text):
    return re.findall('[A-Za-z][A-Za-z-]*', text)


def split_sentences(text):
    text = text.strip()
    if not text:
        return []
    parts = []
    buf = ''
    for ch in text:
        buf += ch
        if ch in '.!?':
            if buf.strip():
                parts.append(buf.strip())
            buf = ''
    if buf.strip():
        parts.append(buf.strip())
    return [p for p in parts if p]


def count_source_sentences(text):
    count = 0
    buf = ''
    for ch in text:
        if ch in '。！？':
            if buf.strip():
                count += 1
            buf = ''
        else:
            buf += ch
    if buf.strip():
        count += 1
    return count


def issue(level, code, message):
    return {'level': level, 'code': code, 'message': message}


def sentence_tense(sentence):
    low = [t.lower() for t in tokenize(sentence)]
    if not low:
        return 'unknown'
    for a, b in zip(low, low[1:]):
        if a in {'has', 'have'} and b.endswith('ed'):
            return 'perfect'
    if any(w in IRREGULAR_PAST for w in low):
        return 'past'
    if any(w.endswith('ed') and len(w) > 3 for w in low):
        return 'past'
    for a, b in zip(low, low[1:]):
        if a in {'he', 'she', 'it', 'they', 'we', 'i', 'people'}:
            if b in BASE_VERBS or (b.endswith('s') and len(b) > 3 and not b.endswith('ss')):
                return 'present'
    if any(w in {'is', 'are', 'do', 'does'} for w in low):
        return 'present'
    return 'unknown'


def analyze(source, target):
    issues = []
    target = target.strip()

    if not target:
        issues.append(issue('critical', 'empty', '译文为空'))
        return {
            'score': 0,
            'band': '需复核',
            'pass': False,
            'metrics': {},
            'issues': issues,
            'self_eval_line': '【自评】译文为空',
        }

    sentences = split_sentences(target)
    tokens = tokenize(target)
    lower = [t.lower() for t in tokens]
    pairs = list(zip(lower, lower[1:]))
    triples = list(zip(lower, lower[1:], lower[2:]))

    word_count = len(tokens)
    lengths = [len(tokenize(s)) for s in sentences] or [0]
    avg_len = round(sum(lengths) / len(lengths), 1)
    max_len = max(lengths)

    advanced_hits = sorted({w for w in lower if w in ADVANCED})
    long_ratio = round(sum(1 for w in tokens if len(w) >= 9) / max(word_count, 1), 3)

    passive = sum(
        1 for a, b in pairs
        if a in BE_WORDS and (b.endswith('ed') or b in IRREGULAR_PARTICIPLES)
    )
    clauses = sum(1 for w in lower if w in CLAUSE_WORDS)

    # 复杂句式只作为提示，不作为修改命令
    complex_markers = []
    if any(a == 'having' and b.endswith('ed') for a, b in pairs):
        complex_markers.append('having done')
    if any(a == 'were' and b == 'to' for a, b in pairs):
        complex_markers.append('were to')
    if any(a == 'would' and b == 'have' for a, b in pairs):
        complex_markers.append('would have')
    if complex_markers:
        issues.append(issue(
            'info', 'complex',
            '出现较复杂结构（提示，非错误）：' + '、'.join(complex_markers),
        ))

    for a, b in pairs:
        if a in {'he', 'she', 'it'} and b in BASE_VERBS:
            issues.append(issue('critical', 'sv', '主谓不一致：{} {}'.format(a, b)))
        if a in {'i', 'we', 'you', 'they'} and b in SINGULAR_VERBS:
            issues.append(issue('critical', 'sv', '主谓不一致：{} {}'.format(a, b)))
        if a == 'people' and b in SINGULAR_VERBS:
            issues.append(issue('critical', 'sv', '主谓不一致：people {}'.format(b)))

    for a, b, c in triples:
        if a == 'there' and b in {'have', 'has'} and c != 'been':
            issues.append(issue('critical', 'there', '应为 there are/is：there {}'.format(b)))

    for w in lower:
        if w in ALWAYS_WRONG_PLURALS:
            issues.append(issue('critical', 'uncountable', '不可数名词误加复数：' + w))

    for a, b in pairs:
        if a == b and len(a) > 2 and a not in {'that', 'had'}:
            issues.append(issue('critical', 'repeat', '重复单词：{} {}'.format(a, b)))

    if ('although' in lower or 'though' in lower) and ', but' in target.lower():
        issues.append(issue('warning', 'although_but', 'although 与 but 同时出现'))

    if 'because' in lower and ', so' in target.lower():
        issues.append(issue('warning', 'because_so', 'because 与 so 同时出现'))

    if any(a == 'the' and b in COUNTRY_WORDS for a, b in pairs):
        issues.append(issue('warning', 'the_country', '国家名前不加 the'))

    found_cn = sorted({ch for ch in target if ch in CN_PUNCT})
    if found_cn:
        issues.append(issue('critical', 'cn_punct', '译文含中文标点：' + ''.join(found_cn)))

    if '  ' in target:
        issues.append(issue('info', 'space', '存在连续空格'))

    if any(' ' + ch in target for ch in ',.;:!?'):
        issues.append(issue('info', 'space_punct', '标点前有多余空格'))

    if target[-1:] not in '.!?':
        issues.append(issue('warning', 'end_punct', '结尾缺句末标点'))

    if sentences and sentences[0][:1].islower():
        issues.append(issue('warning', 'capital', '句首未大写'))

    for a, b in pairs:
        if a == 'a' and b[:1] in VOWELS and b not in A_EXCEPTIONS:
            issues.append(issue('warning', 'article', '冠词疑似错误：a ' + b))
            break
    for a, b in pairs:
        if a == 'an' and b[:1] not in VOWELS and b[:1].isalpha() and b not in AN_EXCEPTIONS:
            issues.append(issue('warning', 'article', '冠词疑似错误：an ' + b))
            break

    # 数字保留
    src_nums = re.findall('[0-9][0-9.%]*', source)
    tgt_nums = re.findall('[0-9][0-9.%]*', target)
    if len(src_nums) != len(tgt_nums):
        issues.append(issue(
            'warning', 'number',
            '数字数量不一致：原文 {} 个，译文 {} 个'.format(len(src_nums), len(tgt_nums)),
        ))

    # 句数骤减：比字符比值更能发现整句漏译，但仍需人工确认
    src_sentences = count_source_sentences(source)
    if src_sentences >= 2 and len(sentences) < src_sentences * 0.6:
        issues.append(issue(
            'warning', 'sentence_drop',
            '原文 {} 句，译文仅 {} 句，疑似整句漏译或过度合并，请逐条核对信息点'.format(
                src_sentences, len(sentences)),
        ))

    src_chars = len(''.join(
        ch for ch in source
        if not ch.isspace() and ch not in CN_PUNCT
    ))
    coverage = round(word_count / max(src_chars, 1), 3)

    # 时态：句间反复切换且无时间标记时提示
    tenses = [sentence_tense(s) for s in sentences]
    known = [t for t in tenses if t != 'unknown']
    switches = sum(1 for a, b in zip(known, known[1:]) if a != b)
    has_marker = any(w in TIME_MARKERS for w in lower) or bool(re.findall('[0-9]{4}', target))
    if switches >= 2 and not has_marker:
        issues.append(issue(
            'warning', 'tense_shift',
            '句间时态切换 {} 次且无时间状语，请确认时间线是否统一'.format(switches),
        ))

    critical = sum(1 for i in issues if i['level'] == 'critical')
    warning = sum(1 for i in issues if i['level'] == 'warning')
    info = sum(1 for i in issues if i['level'] == 'info')
    score = max(0, min(100, 100 - 12 * critical - 4 * warning - 1 * info))

    if critical or warning >= 5:
        band = '需复核'
    elif len(advanced_hits) <= 2 and max_len <= 28 and avg_len <= 20:
        band = '10-12（筛查值）'
    else:
        band = '7-9（筛查值）'

    self_eval = (
        '【自评】难词 {} 处｜最长句 {} 词｜critical {}｜warning {}｜机器筛查 {}'
        .format(len(advanced_hits), max_len, critical, warning, band)
    )

    return {
        'score': score,
        'band': band,
        'pass': critical == 0 and score >= 80,
        'pass_note': 'pass 仅表示表层筛查未发现硬错误，不代表语义完整或达到 10-12 分档',
        'metrics': {
            'sentences': len(sentences),
            'source_sentences': src_sentences,
            'words': word_count,
            'avg_sentence_len': avg_len,
            'max_sentence_len': max_len,
            'advanced_hits': advanced_hits,
            'advanced_count': len(advanced_hits),
            'long_word_ratio': long_ratio,
            'passive_voice': passive,
            'relative_clauses': clauses,
            'coverage_ratio': coverage,
            'tense_switches': switches,
        },
        'issues': issues,
        'self_eval_line': self_eval,
    }


def print_report(name, result):
    m = result['metrics']
    print('')
    print('=== {} ==='.format(name))
    print('筛查分 {}｜band {}｜表层 pass {}'.format(
        result['score'], result['band'], result['pass']))
    print(
        '句数 {}/原句 {}｜词数 {}｜句均长 {}｜最长 {}｜难词 {}｜长词比 {}｜时态切换 {}'.format(
            m.get('sentences'), m.get('source_sentences'), m.get('words'),
            m.get('avg_sentence_len'), m.get('max_sentence_len'),
            m.get('advanced_count'), m.get('long_word_ratio'), m.get('tense_switches'),
        )
    )
    if m.get('advanced_hits'):
        print('超纲词提示（不强制替换）：' + ', '.join(m['advanced_hits']))
    if result['issues']:
        for i in result['issues']:
            print('  [{}] {}: {}'.format(i['level'], i['code'], i['message']))
    else:
        print('  未发现可机械判断的错误')
    print('  ' + result['self_eval_line'])


def load_cases():
    if not CASES_PATH.exists():
        raise SystemExit('找不到样例题：{}'.format(CASES_PATH))
    return json.loads(CASES_PATH.read_text(encoding='utf-8'))


def main():
    parser = argparse.ArgumentParser(description='CET-4/6 翻译译文表层筛查')
    parser.add_argument('--source', help='原文文件路径')
    parser.add_argument('--target', help='译文文件路径')
    parser.add_argument('--case', type=int, help='运行第 N 条内置样例（从 1 开始）')
    parser.add_argument('--batch', action='store_true', help='运行全部内置样例')
    parser.add_argument('--json', action='store_true', help='以 JSON 输出')
    args = parser.parse_args()

    if args.batch or args.case:
        cases = load_cases()
        selected = cases if args.batch else [cases[args.case - 1]]
        all_match = True
        results = []
        for case in selected:
            result = analyze(case['source'], case['target'])
            expect_pass = case.get('expect_pass')
            expect_band = case.get('expect_band')
            expect_codes = case.get('expect_codes', [])
            actual_codes = [i['code'] for i in result['issues']]
            match = True
            if expect_pass is not None and result['pass'] != expect_pass:
                match = False
            if expect_band and not result['band'].startswith(expect_band):
                match = False
            for code in expect_codes:
                if code not in actual_codes:
                    match = False
            result['case'] = case['name']
            result['expectation_match'] = match
            results.append(result)
            all_match = all_match and match
            if not args.json:
                print_report(case['name'], result)
                print('  期望：pass={} band={} codes={} → {}'.format(
                    expect_pass, expect_band, expect_codes,
                    '符合' if match else '不符合'))
        if args.json:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            print('')
            print('合计 {} 条，全部符合预期：{}'.format(len(results), all_match))
        return 0 if all_match else 1

    if not (args.source and args.target):
        parser.error('需要同时提供 --source 与 --target，或使用 --case/--batch')

    source = load_file(args.source)
    target = load_file(args.target)
    result = analyze(source, target)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_report('自检', result)
        print('  说明：' + result['pass_note'])
    return 0 if result['pass'] else 1


if __name__ == '__main__':
    sys.exit(main())
