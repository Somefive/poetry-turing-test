import json
import os

human_set = set()
ai_set = set()
jiuge_set = set()
for line in open('data/poetry-turing-tests-ext.jsonl'):
    obj = json.loads(line.strip())
    human_set.update([row['id'] for row in obj.get('human', [])])
    ai_set.update([row['id'] for row in obj.get('ai', [])])
    jiuge_set.update([row['id'] for row in obj.get('jiuge', [])])

print(len(human_set), len(ai_set), len(jiuge_set))

hit_jiuge = 0
hit_ai = 0
view_jiuge = 0
view_ai = 0

for filename in os.listdir('logs'):
    if not filename.startswith('record.log'):
        continue
    for line in open('logs/' + filename):
        if len(line.strip()) == 0:
            continue
        if line.startswith('[get_score]'):
            parts = line.split(' ')
            session_id = parts[2]
            user, mode, datestr = session_id.split('::')
            if user.lower() in ['yinda', 'somefive']:
                continue
            if mode != 'extra':
                continue
            print('session_id: %s' % session_id)
            answers = parts[6].split('|')
            for answer in answers:
                options, selected, time, correct = answer.split(';')
                for _id in options.split(','):
                    if _id in ai_set:
                        view_ai += 1
                    elif _id in jiuge_set:
                        view_jiuge += 1
                if selected in ai_set:
                    hit_ai += 1
                if selected in jiuge_set:
                    hit_jiuge += 1

print('jiuge: %7d / %7d / %.4f' % (hit_jiuge, view_jiuge, hit_jiuge / view_jiuge))
print('ai:    %7d / %7d / %.4f' % (hit_ai, view_ai, hit_ai / view_ai))