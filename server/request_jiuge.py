import json
import requests
import random
import time
import string
import hashlib

def request_jiuge(title, genre, yan):
    print('> getting %s, genre: %d, yan: %d' % (title, genre, yan))
    resp = requests.post('http://jiuge.thunlp.org/getKeyword', data={
        'level': 1, 'genre': genre, 'keywords': title
    })
    if resp.status_code != 200:
        raise Exception('get keywords failed: %d' % resp.status_code)
    keywords = json.dumps(resp.json()['data'], ensure_ascii=False)
    print('  got keywords: %s' % keywords)
    user_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
    resp = requests.post('http://jiuge.thunlp.org/sendPoem', data={
        'style': 0, 'genre': genre, 'yan': yan, 'keywords': keywords,
        'user_id': user_id
    })
    if resp.status_code != 200:
        raise Exception('send poem failed: %d' % resp.status_code)
    print('  poem sent')
    poem = None
    retry = 0
    while True:
        retry += 1
        resp = requests.post('http://jiuge.thunlp.org/getPoem', data={
            'style': 0, 'genre': genre, 'yan': yan, 'keywords': keywords,
            'user_id': user_id
        })
        if resp.status_code != 200:
            raise Exception('get poem failed: %d' % resp.status_code)
        obj = resp.json()
        if obj['code'] == '0':
            print('\r  got poem')
            poem = obj['data']['poem']
            break
        print('\r  waiting poem[%d]' % retry, end='')
        time.sleep(1)
    lines = []
    for idx, line in enumerate(poem):
        if idx % 2 == 0:
            lines.append(line + '，')
        else:
            lines[-1] += line + '。'
    return lines

def hashc(content):
    return hashlib.sha1(hashlib.md5(content.encode()).digest()).hexdigest()[:8]

fold = open('data/v2/poetry-turing-tests-ext.jsonl')
fsrc = open('data/v2/poetry-turing-tests.jsonl')
fout = open('data/v2/poetry-turing-tests-ext-v2.jsonl', 'w')
idx = 0
skipped = 0
for line in fold:
    fsrc.readline()
    obj = json.loads(line)
    if len(obj.get('jiuge', [])) > 0:
        idx += 1
    else:
        skipped += 1
    fout.write('%s\n' % line.strip())
fold.close()
for line in fsrc:
    obj = json.loads(line.strip())
    g, yan = obj['scheme']
    genre = 1 if g == 2 else 7
    try:
        idx += 1
        lines = request_jiuge(obj['title'], genre, yan)
        obj['jiuge'] = [{'id': hashc(''.join(lines)), 'content': lines}]
    except Exception as e:
        skipped += 1
        print('  unexpected err: %s, skipped' % e)
    print('< finished %d poetry generated, skipped %d poetry' % (idx, skipped))
    fout.write('%s\n' % json.dumps(obj, ensure_ascii=False))
