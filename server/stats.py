from collections import Counter
import json
import numpy as np
score_board = json.load(open('data/score_board.json'))
users = set()
for key in score_board:
    users.update([key for key in score_board[key].keys() if not key.startswith('Tester')])
print('Total users: %d' % len(users))
for key in score_board:
    values = []
    for user in score_board[key]:
        if not user.startswith('Tester'):
            values.append(score_board[key][user])
    counter = Counter(values)
    print('mode: %s avg: %.2f max: %.2f' % (key, np.mean(values), np.max(values)))
    for key in sorted(counter.keys()):
        print('  [%d]: %d' % (key, counter[key]))
    print('')
