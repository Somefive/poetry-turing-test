from flask import Flask, request
from flask_cors import CORS
import json
from datetime import datetime
import time
import logging
import random
from threading import Lock, Thread
import numpy as np
import math
import os
app = Flask(__name__, static_folder='poetry-turing-test')
app.config['JSON_AS_ASCII'] = False
CORS(app)

SCORE_BOARD_FILE='data/score_board.json'
POETRY_HIT_FILE='data/poetry_hit.json'
POETRY_VIEW_FILE='data/poetry_view.json'

logging.basicConfig(format="%(asctime)s: %(message)s", level=logging.INFO, datefmt="%Y-%m-%dT%H:%M:%S")

def get_size(mode):
  if mode == 'easy':
    return 5
  elif mode == 'hard':
    return 10
  else:
    return 20

poetry_tests = []
for line in open('poetry-turing-tests.jsonl'):
  poetry_tests.append(json.loads(line.strip()))
human_ids = set()
for obj in poetry_tests:
  for line in obj['lines']:
    human_ids.add(line['id'])
logging.info('[preprocess] load %d poetry tests and %d human ids' % (len(poetry_tests), len(human_ids)))

score_board = json.load(open(SCORE_BOARD_FILE)) if os.path.isfile(SCORE_BOARD_FILE) else {}
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
      score_board[key][tester_name] = max(min(round(np.random.normal(loc=loc, scale=scale)), size), 0)
    tester_id += 1
json.dump(score_board, open(SCORE_BOARD_FILE, 'w'), ensure_ascii=False)

def get_score_board(username, score, mode):
  score_board[mode][username] = score
  total = len(score_board[mode])
  rank = list(sorted(score_board[mode].values(), reverse=True)).index(score)
  return rank, total

poetry_hit = json.load(open(POETRY_HIT_FILE)) if os.path.isfile(POETRY_HIT_FILE) else {}
poetry_view = json.load(open(POETRY_VIEW_FILE)) if os.path.isfile(POETRY_VIEW_FILE) else {}
def record_poetry_hit(answers):
  for ans in answers:
    for _id in ans['options']:
      if _id not in poetry_view:
        poetry_view[_id] = 1
      else:
        poetry_view[_id] += 1
    if ans['select_id'] not in poetry_hit:
      poetry_hit[ans['select_id']] = 1
    else:
      poetry_hit[ans['select_id']] += 1

@app.route('/get-turing-tests/<mode>')
def get_turing_tests(mode):
  logging.info("[get_turing_tests] mode: %s" % mode)
  global poetry_tests
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
      obj = {'cases': cases}
      if mode != 'lunatic':
        obj['title'] = poetry['title']
      if mode == 'easy':
        obj['author'] = poetry['author']
        obj['dynasty'] = poetry['dynasty']
      tests.append(obj)
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
  record_poetry_hit(request.json['answers'])
  logging.info("[get_score] username: %s mode: %s score: %d" % (username, mode, score))
  return {
    'score': score,
    'rank': rank,
    'total': total
  }

def run_dump():
  global poetry_hit, poetry_view, score_board
  while True:
    time.sleep(60)
    json.dump(poetry_hit, open(POETRY_HIT_FILE, 'w'), ensure_ascii=False)
    json.dump(poetry_view, open(POETRY_VIEW_FILE, 'w'), ensure_ascii=False)
    json.dump(score_board, open(SCORE_BOARD_FILE, 'w'), ensure_ascii=False)
    logging.info('[run_dump] update finished')


Thread(target=run_dump).start()