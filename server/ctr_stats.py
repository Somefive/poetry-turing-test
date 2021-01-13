import json

poetry_hit = json.load(open('data/poetry_hit.json'))
poetry_view = json.load(open('data/poetry_view.json'))

poetry_mapping = {}
for line in open('poetry-turing-tests.jsonl'):
    poetry = json.loads(line.strip())
    key = poetry['title'] + ' ' + poetry['author']
    for lines in poetry['lines']:
        poetry_mapping[lines['id']] = 'human ' + key + ' ' + ''.join(lines['content'])
    for lines in poetry['ai-lines']:
        poetry_mapping[lines['id']] = 'ai ' + key + ' ' + ''.join(lines['content'])

ctr = {}
for k, v in poetry_hit.items():
    if k in poetry_view and k in poetry_mapping:
        ctr[k] = v / poetry_view[k]

for k in poetry_view:
    if k not in ctr:
        ctr[k] = 0

for k, v in sorted(ctr.items(), key=lambda x: -x[1]):
    print('%.2f%% (%d / %d) %s %s' % (v * 100, poetry_hit.get(k, 0), poetry_view.get(k, 0), k, poetry_mapping.get(k, '')))