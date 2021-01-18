from enum import Enum
from typing import Optional, List, Tuple, Union, Dict
import json
from .utils import hashc
import random
from datetime import datetime
from threading import Lock, Thread
import shutil
import logging
import time


class TuringTestConfig(object):

    def __init__(self, obj: dict):
        self.mode = obj.get('mode', 'easy')
        self.exclude_fields: List[str] = obj.get('exclude_fields', [])
        self.num_options = obj.get('num_options', 2)
        self.num_testcases = obj.get('num_testcases', 5)
        self.base_timelimit: Optional[int] = obj.get('base_timelimit', None)
        self.timelimit_boost: float = obj.get('timelimit_boost', 1.5)
        self.allow_backward: bool = obj.get('allow_backward', False)
        self.ground_truth_prob: float = obj.get('ground_truth_prob', 1.0)

    def as_json(self):
        return {
            'mode': self.mode,
            'exclude_fields': self.exclude_fields,
            'num_options': self.num_options,
            'num_testcases': self.num_testcases,
            'base_timelimit': self.base_timelimit,
            'timelimit_boost': self.timelimit_boost,
            'allow_backward': self.allow_backward,
            'ground_truth_prob': self.ground_truth_prob
        }


class Backend(object):

    def __init__(self, turing_test_configs_filename: str, score_board_filename: str, dump_interval: int = 60):
        self.configs = {config_key: TuringTestConfig(obj) for config_key, obj in json.load(open(turing_test_configs_filename)).items()}
        self.score_board_filename = score_board_filename
        self.score_board: Dict[str, Dict[str, Tuple[int, int, str]]] = {}
        for mode, data in json.load(open(score_board_filename)).items():
            self.score_board[mode] = {}
            for k, v in data.items():
                if isinstance(v, int):
                    self.score_board[mode][k] = [v, 1000000, '2121-01-01T00:00:00']
                else:
                    self.score_board[mode][k] = v
        self.thread = Thread(target=self.run_dump, args=(dump_interval,))
        self.thread.start()

    def get_config(self, mode: str, username: str) -> Tuple[str, TuringTestConfig]:
        # TODO
        config_key = mode
        return config_key, self.configs[config_key]

    def generate_session_key(self, username: str, config_key: str) -> Tuple[str, str]:
        session_id = '%s::%s::%s' % (username, config_key, datetime.now().strftime('%Y-%m-%dT%H:%M:%S'))
        return session_id, hashc(session_id + "::THUKEG2020")

    def validate_session(self, session_id: str, session_key: str):
        return hashc(session_id + "::THUKEG2020") == session_key

    def submit_score(self, username: str, score: int, mode: str, timecost: int, submit_date: str) -> Tuple[Tuple[int, int, str], Tuple[int, int]]:
        if mode not in self.score_board:
            self.score_board = {}
        if username not in self.score_board[mode]:
            self.score_board[mode][username] = [score, timecost, submit_date]
        else:
            best_score, best_timecost, best_date = self.score_board[mode][username]
            if score > best_score or (score == best_score and timecost < best_timecost):
                self.score_board[mode][username] = [score, timecost, submit_date]

        best_score, best_timecost, best_date = self.score_board[mode][username]
        better, worse = 0, 0
        for _score, _timecost, _date in self.score_board[mode].values():
            if best_score > _score or (best_score == _score and best_timecost < _timecost):
                better += 1
            else:
                worse += 1
        return (best_score, best_timecost, best_date), (better + 1, (better + worse))

    def run_dump(self, interval: int = 60):
        logging.info('[Backend] launched running dump')
        while True:
            time.sleep(interval)
            json.dump(self.score_board, open(self.score_board_filename + '.tmp', 'w'), ensure_ascii=False)
            shutil.copy(self.score_board_filename, self.score_board_filename + '.%s' % datetime.now().strftime('%y%m%d%H'))
            shutil.move(self.score_board_filename + '.tmp', self.score_board_filename)
            logging.info('[Backend] score board dumped')

    def get_ranks(self, mode: str):
        ranks = []
        for username, tup in sorted(self.score_board[mode].items(), key=lambda pair: (-pair[1][0], pair[1][1], pair[1][2])):
            if len(ranks) == 0 or ranks[-1]['score'] != tup[0]:
                ranks.append({'score': tup[0], 'users': []})
            ranks[-1]['users'].append([username, tup[1] if tup[1] < 1000000 else None, tup[2] if tup[2] != '2121-01-01T00:00:00' else 'NA'])
        return ranks