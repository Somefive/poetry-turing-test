from flask import Flask, request, send_file
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
import logging.handlers
import sys
from turing_poet.filter import DFAFilter
from turing_poet.daemon import Daemon
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
  handler = logging.handlers.TimedRotatingFileHandler(log_path)
  handler.setLevel(logging.INFO)
  recorder.addHandler(handler)
  return recorder

recorder = init_recorder('logs/record.log')

gfw = DFAFilter()
gfw.parse('data/v2/keywords')

def process_username(username):
  return gfw.filter(username).replace(' ', '').replace('\n', '').replace('\t', '')

poetry_tests_manager = PoetryTestManager(
  poetry_tests_filename='data/v2/poetry-turing-tests-ext.jsonl'
)

backend = Backend(
  turing_test_configs_filename='turing_poet/configs.json',
  score_board_filename='data/v2/score_board.json',
  process_name_func=process_username
)

daemon = Daemon(
    poetry_ctr_filename='data/v2/ctr.csv',
    user_record_filename='data/v2/user-record.csv',
    hard_samples_filename='data/v2/hard-samples.jsonl',
    previous_poetry_hit_view_filenames=('data/poetry_hit.json', 'data/poetry_view.json'),
    top_hard=50,
    log_filename='logs/record.log',
    poetry_tests=poetry_tests_manager.poetry_tests
)

@app.route('/')
def hello():
  return {
    'version': 'v2',
    'name': 'turing-poet'
  }

@app.route('/get-turing-tests', methods=['POST'])
def get_turing_tests():
  username = process_username(request.json['username'])
  mode = request.json['mode']
  config_key, config = backend.get_config(mode, username)
  session_id, session_key = backend.generate_session_key(username, config_key)
  # candidate_ids = [] if mode != 'extra' else [_id for _id in daemon.hard_samples]
  # random.shuffle(candidate_ids)
  candidate_ids = []
  tests = poetry_tests_manager.generate_testcases(config.num_testcases, config.num_options, config.ground_truth_prob, candidate_ids=candidate_ids, include_jiuge=config.include_jiuge)
  recorder.info("[get_turing_test] session_id: %s tests: %s" % (session_id, '|'.join([test.as_logstr() for test in tests])))
  return {
    'session_id': session_id,
    'session_key': session_key,
    'config': config.as_json(),
    'tests': [test.as_json(config.exclude_fields) for test in tests]
  }

@app.route('/get-score', methods=['POST'])
def get_score():
  global human_ids
  username = process_username(request.json['username'])
  mode = request.json['mode']
  session_id = request.json['session_id']
  session_key = request.json['session_key']
  if not backend.validate_session(session_id, session_key):
    return 'Bad session', 400
  score, answers = poetry_tests_manager.submit_answers(request.json['answers'])
  submit_date = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
  timecost = sum([answer.time for answer in answers if answer.time > 0])
  best_record, (rank, total) = backend.submit_score(username, score, mode, timecost, submit_date)
  recorder.info("[get_score] session_id: %s score: %d answers: %s" % (session_id, score, '|'.join([answer.as_logstr() for answer in answers])))
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

@app.route('/get-user-rank', methods=['POST'])
def get_user_rank():
  username = process_username(request.json['username'])
  mode = request.json['mode']
  session_id = request.json['session_id']
  session_key = request.json['session_key']
  email = request.json['email']
  if not backend.validate_session(session_id, session_key):
    return 'Bad session', 400
  ranks, userrank = backend.get_user_rank(mode, username)
  recorder.info('[get_user_rank] session_id: %s email: %s userrank: %d' % (session_id, email, userrank))
  return {
    'ranks': ranks,
    'userrank': userrank
  }

@app.route('/stats/<name>', methods=['GET'])
def stat_file(name):
  if name not in ['ctr', 'ctr-easy', 'ctr-hard', 'ctr-lunatic', 'ctr-extra', 'user-record']:
    return '', 404
  return send_file('data/v2/%s.csv' % name, as_attachment=True)