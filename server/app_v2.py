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
from collections import Counter
from turing_poet.manager import PoetryTestManager
from turing_poet.backend import Backend
from datetime import datetime
import sys
app = Flask(__name__, static_folder='poetry-turing-test')
app.config['JSON_AS_ASCII'] = False
CORS(app)

logging.basicConfig(format="%(asctime)s: %(message)s", level=logging.INFO, datefmt="%Y-%m-%dT%H:%M:%S")

def init_recorder(log_path: str):
  recorder = logging.getLogger('Recorder')
  recorder.setLevel(logging.INFO)
  handler = logging.StreamHandler(sys.stdout)
  handler.setLevel(logging.INFO)
  recorder.addHandler(handler)
  handler = logging.FileHandler(log_path)
  handler.setLevel(logging.INFO)
  recorder.addHandler(handler)
  return recorder

recorder = init_recorder('logs/record.log')

poetry_tests_manager = PoetryTestManager(
  poetry_tests_filename='data/v2/poetry-turing-tests.jsonl'
)

backend = Backend(
  turing_test_configs_filename='turing_poet/configs.json',
  score_board_filename='data/v2/score_board.json'
)

@app.route('/')
def hello():
  return {
    'version': 'v2',
    'name': 'turing-poet'
  }

@app.route('/get-turing-tests', methods=['POST'])
def get_turing_tests():
  username = request.json['username']
  mode = request.json['mode']
  # session_key = backend.generate_session_key(mode, username)
  config_key, config = backend.get_config(mode, username)
  session_id, session_key = backend.generate_session_key(username, config_key)
  tests = poetry_tests_manager.generate_testcases(config.num_testcases, config.num_options, config.ground_truth_prob)
  recorder.info("[get_turing_test] session_id: %s tests: %s" % (session_id, '|'.join([test.as_logstr() for test in tests])))
  return {
    'session_id': session_id,
    'session_key': session_key,
    'config': config.as_json(),
    'tests': [test.as_json(config.exclude_fields) for test in tests]
  }

# Answer format: {
#   'options': <lines id>[]
#   'select_id': <id>
#   'time': <seconds used in this case>
# }
@app.route('/get-score', methods=['POST'])
def get_score():
  global human_ids
  username = request.json['username']
  mode = request.json['mode']
  session_id = request.json['session_id']
  session_key = request.json['session_key']
  if not validate_session(session_id, session_key):
    return 'Bad session', 400
  score, answers = poetry_tests_manager.submit_answers(request.json['answers'])
  submit_date = datetime.now().strftime('%y-%m-%dT%H:%M:%S')
  timecost = sum([answer.time for answer in answers if answer.time > 0])
  best_record, (rank, total) = backend.submit_score(username, score, mode, timecost, submit_date)
  recorder.info("[get_score] session_key: %s score: %d answers: %s" % (session_key, score, '|'.join([answer.as_logstr() for answer in answers])))
  return {
    'score': score,
    'rank': rank,
    'total': total,
    'best_record': best_record,
    'submit_date': submit_date,
    'timecost': timecost
  }

@app.route('/get-ranks/<mode>/<content_type>', methods=['GET'])
def get_ranks(mode, content_type):
  ranks = backend.get_ranks(mode)
  if content_type == 'table':
    divs = []
    for data in ranks:
      divs.append('<div>Score: %s Users: %d</div>' % (data['score'], len(data['users'])))
      for username, timecost, updatedate in data['users']:
        divs.append('<div>%15s%10s%20s</div>' % (username, '%5dsec' % timecost if timecost else 'NA', updatedate))
      divs.append('<hr/>')
    return '<html>%s</html>' % ''.join(divs)
  else:
    return {
      'mode': mode,
      'rank': ranks
    }
