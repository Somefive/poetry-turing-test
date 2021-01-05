from flask import Flask, request
from flask_cors import CORS
import json
from datetime import datetime
import time
import logging
import random
from threading import Lock
import numpy as np
import math
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
CORS(app)

poetry_tests = []
human_ids = set()
last_time = 0
def load_poetry_tests():
  global poetry_tests, last_time, human_ids, loader_lock
  _t = time.time()
  if _t - last_time > 600:
    _pt = []
    for line in open('poetry-turing-tests.jsonl'):
      _pt.append(json.loads(line.strip()))
    _human_ids = set()
    for obj in _pt:
      for line in obj['lines']:
        _human_ids.add(line['id'])
    poetry_tests, human_ids = _pt, _human_ids
    logging.info('reload poetries, %d loaded' % len(poetry_tests))
    last_time = _t
  return poetry_tests

score_board = json.load(open('score_board.json'))
for key in ['easy', 'hard', 'lunatic']:
  if key not in score_board:
    score_board[key] = {}
  tester_id = 0
  size = get_size(key)
  loc = 3 if key == 'easy' else (5 if key == 'hard' else 8)
  scale = 1 if key == 'easy' else (2 if key == 'hard' else 3)
  while len(score_board[key]) < 50:
    tester_name = 'Tester-%d' % tester_id
    if tester_name not in score_board[key]:
      score_board[key][tester_name] = max(min(math.floor(np.random.normal(loc=loc, scale=scale)), size), 0)
    tester_id += 1
json.dump(score_board, open('score_board.json', 'w'), ensure_ascii=False)

score_board_lock = Lock()
def get_score_board(username, score, mode):
  with score_board_lock:
    if mode not in score_board:
      score_board[mode] = {}
    score_board[mode][username] = score
    json.dump(score_board, open('score_board.json', 'w'), ensure_ascii=False)
  total = len(score_board[mode])
  rank = list(sorted(score_board[mode].values(), reverse=True)).index(score)
  return rank, total

def get_size(mode):
  if mode == 'easy':
    return 5
  elif mode == 'hard':
    return 10
  else:
    return 20

@app.route('/get-turing-tests/<mode>')
def get_turing_tests(mode):
  global poetry_tests
  _tests = load_poetry_tests()
  poetry_ids = set()
  size = get_size(mode)
  tests = []
  while len(tests) < size:
    poetry = random.choice(poetry_tests)
    if poetry['id'] in poetry_ids:
      continue
    if len(poetry['ai-lines']) == 0 or len(poetry['lines']) == 0:
      continue
    if mode == 'easy' and len(poetry['ai-lines']) >= 1:
      poetry_ids.add(poetry['id'])
      cases = [random.choice(poetry['lines']), random.choice(poetry['ai-lines'])]
      random.shuffle(cases)
      tests.append({
        'title': poetry['title'], 'author': poetry['author'], 'dynasty': poetry['dynasty'],
        'cases': cases
      })
    elif mode != 'easy' and len(poetry['ai-lines']) >= 2:
      ai_first_sents = {}
      for line in poetry['ai-lines']:
        if line['content'][0][:3] not in ai_first_sents:
          ai_first_sents[line['content'][0][:3]] = [line]
        else:
          ai_first_sents[line['content'][0][:3]].append(line)
      if len(ai_first_sents) < 2:
        continue
      cases = []
      if mode == 'hard' or random.random() < 0.75:
        cases.append(random.choice(poetry['lines']))
      if len(ai_first_sents) + len(cases) < 3:
        continue
      keys = list(ai_first_sents.keys())
      random.shuffle(keys)
      rest_size = 3 - len(cases)
      for key in keys[:rest_size]:
        cases.append(random.choice(ai_first_sents[key]))
      random.shuffle(cases)
      tests.append({
        'title': poetry['title'], 'author': poetry['author'], 'dynasty': poetry['dynasty'],
        'cases': cases
      })
  return {
    'tests': tests
  }

@app.route('/get-score', methods=['POST'])
def get_score():
  global human_ids
  username = request.json['username']
  mode = request.json['mode']
  score = 0
  for row in request.json['answers']:
    answer = [_id for _id in row['options'] if _id in human_ids]
    if len(answer) == 0 and row['select_id'] == '':
      score += 1
    elif len(answer) > 0 and answer[0] == row['select_id']:
      score += 1
  rank, total = get_score_board(username, score, mode)
  return {
    'score': score,
    'rank': rank,
    'total': total
  }