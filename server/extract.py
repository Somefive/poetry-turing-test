import re
import json
import random
from collections import defaultdict
import os
import hashlib
import shutil

poetries = []
with open('poetry-utf8.txt') as f:
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

with open('poetries.jsonl', 'w') as f:
    for title, author, lines in poetries:
        f.write('%s\n' % json.dumps({'title': title, 'author': author, 'lines': lines}))

format_poetries = {}
for title, author, lines in poetries:
    if not re.match(r'^[\u4e00-\u9fa5]{3,7}$', title) or not re.match(r'^[\u4e00-\u9fa5]{2,4}$', author):
        continue
    if re.search('·|（|）|：', title):
        continue
    is_valid = re.match(r'^(((\w{5})，(\w{5})。){2}){1,2}$', lines) is not None or re.match(r'^(((\w{7})，(\w{7})。){2}){1,2}$', lines) is not None
    if not is_valid:
        continue
    key = '%s %s' % (title, author)
    if key not in format_poetries:
        format_poetries[key] = {'title': title, 'author': author, 'dynasty': '唐', 'lines': [], 'ai-lines': []}
    _lines = [line + '。' for line in lines.split('。') if len(line) > 0]
    format_poetries[key]['lines'].append(_lines)

selected_keys = set()
for filename in os.listdir('../../poems_save2/poems_save2'):
    for line in open('../../poems_save2/poems_save2/' + filename):
        obj = json.loads(line.strip())
        key = obj['title'] + ' ' + obj['author'].split(' ')[1]
        if key in format_poetries:
            _lines = []
            is_end = True
            for idx, text in enumerate(re.findall(r'[\u4e00-\u9fa5]{5,7}', obj['context'])):
                if idx % 2 == 0:
                    _lines.append(text + '，')
                    is_end = False
                else:
                    _lines[-1] += text + '。'
                    is_end = True
            if is_end:
                format_poetries[key]['ai-lines'].append(_lines)
                selected_keys.add(key)

def hashc(content):
    return hashlib.sha1(hashlib.md5(content.encode()).digest()).hexdigest()[:8]

with open('./poetry-turing-tests.jsonl.tmp', 'w') as f:
    for key in selected_keys:
        poetry = format_poetries[key]
        poetry['id'] = hashc(('%s %s' % (poetry['title'], poetry['author'])))
        poetry['lines'] = [{'content': line, 'id': hashc(''.join(line))} for line in poetry['lines']]
        poetry['ai-lines'] = [{'content': line, 'id': hashc(''.join(line))} for line in poetry['ai-lines']]
        f.write('%s\n' % json.dumps(poetry, ensure_ascii=False))

shutil.move('./poetry-turing-tests.jsonl.tmp', './poetry-turing-tests.jsonl')
# json.dump([format_poetries[key] for key in selected_keys], open('./poetry-turing-tests.json', 'w'), ensure_ascii=False)
