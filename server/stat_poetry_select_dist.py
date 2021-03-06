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

ai_hist = []
jiuge_hist = []

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
            # if mode != 'extra' and mode != 'easy-jiuge-or-ai':
            if mode != 'extra':
            # if mode != 'easy-jiuge-or-ai':
                continue
            # print('session_id: %s' % session_id)
            answers = parts[6].split('|')
            view_ai, view_jiuge, hit_ai, hit_jiuge = 0, 0, 0, 0
            view_human, hit_human = 0, 0
            for answer in answers:
                options, selected, time, correct = answer.split(';')
                if float(time) < 1:
                    continue
                for _id in options.split(','):
                    if _id in ai_set:
                        view_ai += 1
                    elif _id in jiuge_set:
                        view_jiuge += 1
                    else:
                        view_human += 1
                if selected in ai_set:
                    hit_ai += 1
                elif selected in jiuge_set:
                    hit_jiuge += 1
                else:
                    hit_human += 1
            if view_ai > 0:
                ai_hist.append(hit_ai / view_ai)
            if view_jiuge > 0:
                jiuge_hist.append(hit_jiuge / view_jiuge)
            # Xs.append((hit_ai, hit_jiuge))
            print('%20s AI: %3d/%3d Jiuge: %3d/%3d Human: %3d/%3d %s' % (mode, hit_ai, view_ai, hit_jiuge, view_jiuge, hit_human, view_human, user))


import matplotlib.pyplot as plt
fig, axs = plt.subplots(2)
axs[0].hist(ai_hist)
axs[0].set_title('Easy AI')
axs[1].hist(jiuge_hist)
axs[1].set_title('Easy Jiuge')
plt.savefig('easy.jpg')

# print('jiuge: %7d / %7d / %.4f' % (hit_jiuge, view_jiuge, hit_jiuge / view_jiuge))
# print('ai:    %7d / %7d / %.4f' % (hit_ai, view_ai, hit_ai / view_ai))