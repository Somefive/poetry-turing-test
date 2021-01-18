import re
import json
import random
from collections import defaultdict
import os
import hashlib
import shutil

def load_source_poetry():
    poetries = []
    data_path = 'data/poetries.jsonl'
    source_data_path = 'data/poetry-utf8.txt'
    if os.path.exists(data_path):
        print('load poetries from %s' % data_path)
        for line in open(data_path):
            obj = json.loads(line.strip())
            poetries.append((obj['title'], obj['author'], obj['lines']))
        print('%d poetries loaded' % len(poetries))
    else:
        print('cannot find %s, extract from source file %s' % (data_path, source_data_path))
        with open(source_data_path) as f:
            title, author, lines = None, None, []
            for line in f:
                line = line.strip()
                obj = re.match(r'◎卷.+【(?P<title>.+)】(?P<author>\w+)', line)
                if obj:
                    if title and author and lines:
                        poetries.append((title, author, ''.join(lines)))
                    title, author, lines = obj.groupdict()['title'], obj.groupdict()['author'], []
                elif title and author:
                    if len(line) == 0:
                        if title and author and lines:
                            poetries.append((title, author, ''.join(lines)))
                        title, author, lines = None, None, []
                    else:
                        lines.append(line)
            if title and author and lines:
                poetries.append((title, author, ''.join(lines)))
        print('%d poetries extracted' % len(poetries))
        with open(data_path, 'w') as f:
            for title, author, lines in poetries:
                f.write('%s\n' % json.dumps({'title': title, 'author': author, 'lines': lines}, ensure_ascii=False))
        print('poetries saved')
    return poetries


def init_poetry_mapping(poetries):
    format_poetries = {}
    for title, author, lines in poetries:
        if not re.match(r'^[\u4e00-\u9fa5]{3,7}$', title) and not re.match(r'^[\u4e00-\u9fa5]{2,4}$', author):
            continue
        if re.search('·|（|）|：', title):
            continue
        is_valid = re.match(r'^(((\w{5})，(\w{5})。){2}){1,2}$', lines) is not None or re.match(r'^(((\w{7})，(\w{7})。){2}){1,2}$', lines) is not None
        if not is_valid:
            continue
        _lines = [line + '。' for line in lines.split('。') if len(line) > 0]
        key = '%s %s %d-%d' % (title, author, len(_lines), len(_lines[0]) // 2 - 1)
        if key not in format_poetries:
            format_poetries[key] = {'title': title, 'author': author, 'dynasty': '唐', 'lines': [], 'ai-lines': []}
        format_poetries[key]['lines'].append(_lines)
    return format_poetries


def match_ai_outputs_with_poetries(poetry_mapping, source_dir='data/ai'):
    selected_keys = set()
    cnt = 0
    total = 0
    for filename in os.listdir(source_dir):
        total += 1
        for line in open(os.path.join(source_dir, filename)):
            obj = json.loads(line.strip())
            _lines = []
            is_end = True
            for idx, text in enumerate(re.findall(r'[\u4e00-\u9fa5]{5,7}', obj['context'])):
                if idx % 2 == 0:
                    _lines.append(text + '，')
                    is_end = False
                else:
                    _lines[-1] += text + '。'
                    is_end = True
            key = obj['title'] + ' ' + obj['author'].split(' ')[1] + ' %d-%d' % (len(_lines), len(_lines[0]) // 2 - 1)
            if key in poetry_mapping and is_end:
                poetry_mapping[key]['ai-lines'].append(_lines)
                selected_keys.add(key)
                cnt += 1
    print('%d ai poetries loaded for %d poetries' % (cnt, total))
    return selected_keys

def hashc(content):
    return hashlib.sha1(hashlib.md5(content.encode()).digest()).hexdigest()[:8]

def print_candidates(poetry_mapping):
    for k, v in poetry_mapping.items():
        for _lines in v['lines']:
            print('%s %s %d %d %s' % (v['title'], v['author'], len(_lines[0]) // 2 - 1, len(_lines) * 2, ''.join(_lines)))

def generate_poetries_for_test(poetry_mapping, selected_keys=set(), output_path='data/poetry-turing-tests.jsonl'):
    with open('%s.tmp' % output_path, 'w') as f:
        for key in selected_keys:
            poetry = poetry_mapping[key]
            poetry['id'] = hashc(key)
            poetry['scheme'] = [len(poetry['lines'][0]), len(poetry['lines'][0][1]) // 2 - 1]
            poetry['human'] = [{'content': line, 'id': hashc(''.join(line))} for line in poetry['lines']]
            poetry['ai'] = [{'content': line, 'id': hashc(''.join(line))} for line in poetry['ai-lines']]
            del poetry['lines'], poetry['ai-lines']
            f.write('%s\n' % json.dumps(poetry, ensure_ascii=False))

    shutil.move('%s.tmp' % output_path, output_path)
    print('%d poetries for test generated at %s' % (len(selected_keys), output_path))


if __name__ == '__main__':
    poetries = load_source_poetry()
    poetry_mapping = init_poetry_mapping(poetries)
    selected_keys = match_ai_outputs_with_poetries(poetry_mapping, 'data/ai')
    generate_poetries_for_test(poetry_mapping, selected_keys, 'data/poetry-turing-tests.v2.jsonl')