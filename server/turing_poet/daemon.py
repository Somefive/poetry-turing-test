from collections import Counter, defaultdict
from .poetry import PoetryTest
from .manager import PoetryTestManager
import shutil
from typing import List, Tuple, Optional
import time
from threading import Thread
import logging
import os
import json

class Daemon(object):

    def __init__(self, poetry_ctr_filename: str,
                       user_record_filename: str,
                       hard_samples_filename: str,
                       previous_poetry_hit_view_filenames: Optional[Tuple[str, str]],
                       log_filename: str,
                       poetry_tests: List[PoetryTest],
                       top_hard: int = 50,
                       update_interval: int = 300):
        self.poetry_ctr_filename = poetry_ctr_filename
        self.user_record_filename = user_record_filename
        self.log_filename = log_filename
        self.hard_samples_filename = hard_samples_filename
        self.previous_poetry_hit_view_filenames = previous_poetry_hit_view_filenames
        self.top_hard = top_hard
        self.poetry_lines_mapping = {}
        for test in poetry_tests:
            for row in test.human:
                self.poetry_lines_mapping[row._id] = ('human', ''.join(row.content), test)
            for row in test.ai:
                self.poetry_lines_mapping[row._id] = ('ai', ''.join(row.content), test)
            for row in test.jiuge:
                self.poetry_lines_mapping[row._id] = ('jiuge', ''.join(row.content), test)
        self.hard_samples: List[str] = []
        if os.path.exists(hard_samples_filename):
            with open(hard_samples_filename) as f:
                for line in f:
                    self.hard_samples.append(line.strip().split(' ')[0])
            self.hard_samples = self.hard_samples[:top_hard]
        self.thread = Thread(target=self.run_analyze_log, args=(update_interval,))
        self.thread.start()

    def run_analyze_log(self, interval):
        logging.info('[Daemon] launched analyze logs')
        while True:
            self.analyze_log()
            time.sleep(interval)

    def analyze_log(self):
        logging.info('[Daemon] analyzing logs')
        hit = Counter()
        view = Counter()
        hits = defaultdict(Counter)
        views = defaultdict(Counter)
        user_records = []
        sessions = {}
        with open(self.log_filename) as f:
            for line in f:
                if line.startswith('[get_score]'):
                    parts = line.strip().split()
                    session_id = parts[2]
                    score = int(parts[4])
                    answers = parts[6]
                    username, mode, datestr = session_id.split('::')
                    total_time = 0
                    for testcase in answers.split('|'):
                        options, selected_id, timecost, correct = testcase.split(';')
                        options = options.split(',')
                        timecost = float(timecost)
                        if timecost <= 0:
                            continue
                        total_time += timecost
                        for option in options:
                            view[option] += 1
                            views[mode][option] += 1
                        hit[selected_id] += 1
                        hits[mode][selected_id] += 1
                    sessions[session_id] = (score, total_time)
                if line.startswith('[get_user_rank]'):
                    parts = line.strip().split()
                    session_id = parts[2]
                    email = parts[4]
                    if session_id in sessions:
                        score, total_time = sessions[session_id]
                        del sessions[session_id]
                        username, mode, datestr = session_id.split('::')
                        user_records.append({
                            'username': username,
                            'mode': mode,
                            'date': datestr,
                            'score': score,
                            'time': total_time,
                            'email': email
                        })

        if self.previous_poetry_hit_view_filenames:
            ext_views = json.load(open(self.previous_poetry_hit_view_filenames[1]))
            ext_hits = json.load(open(self.previous_poetry_hit_view_filenames[0]))
            for _id, cnt in ext_views.items():
                if _id in self.poetry_lines_mapping:
                    view[_id] += cnt
                    if _id in ext_hits:
                        hit[_id] += ext_hits[_id]

        for session_id, (score, total_time) in sessions.items():
            username, mode, datestr = session_id.split('::')
            user_records.append({
                'username': username,
                'mode': mode,
                'date': datestr,
                'score': score,
                'time': total_time,
                'email': ''
            })
        with open(self.user_record_filename + '.tmp', 'w') as f:
            headers = ['username', 'mode', 'date', 'score', 'time', 'email']
            f.write('%s\n' % ';'.join(headers))
            for record in sorted(user_records, key=lambda x: x['date'], reverse=True):
                f.write('%s\n' % ';'.join(['%s' % record[key] if isinstance(record[key], str) else '%.1f' % float(record[key]) for key in headers]))
        shutil.move(self.user_record_filename + '.tmp', self.user_record_filename)

        def stat_ctr(_view, _hit, filename):
            ctrs = []
            for poetry_id, viewcnt in _view.items():
                if poetry_id in self.poetry_lines_mapping:
                    t, content, test = self.poetry_lines_mapping[poetry_id]
                    hitcnt = _hit[poetry_id]
                    title, author, dynasty = test.title, test.author, test.dynasty
                    ctrs.append({
                        'id': poetry_id,
                        'ctr': hitcnt / viewcnt,
                        'ctr_smooth': hitcnt / (viewcnt + 1),
                        'title': title,
                        'author': author,
                        'dynasty': dynasty,
                        'hit': hitcnt,
                        'view': viewcnt,
                        'content': content,
                        'type': t
                    })
            with open(filename + '.tmp', 'w') as f:
                headers = ['id', 'ctr_smooth', 'type', 'title', 'author', 'dynasty', 'content', 'ctr', 'hit', 'view']
                f.write('%s\n' % ';'.join(headers))
                for record in sorted(ctrs, key=lambda r: -r['ctr_smooth']):
                    f.write('%s\n' % ';'.join(['%s' % record[key] if isinstance(record[key], str) else '%.2f' % float(record[key]) for key in headers]))
            shutil.move(filename + '.tmp', filename)
            return ctrs

        global_ctrs = stat_ctr(view, hit, self.poetry_ctr_filename)
        for mode in views:
            stat_ctr(views[mode], hits[mode], self.poetry_ctr_filename.replace('.csv', '-%s.csv' % mode))

        hard_sample_ids = set()
        with open(self.hard_samples_filename + '.tmp', 'w') as f:
            for record in sorted(filter(lambda r: r['type'] != 'human', global_ctrs), key=lambda r: (r['hit'] > 5, r['ctr_smooth']), reverse=True):
                _, _, test = self.poetry_lines_mapping[record['id']]
                if test._id in hard_sample_ids:
                    continue
                hard_sample_ids.add(test._id)
                f.write('%s %s\n' % (test._id, json.dumps(record, ensure_ascii=False)))
                if len(hard_sample_ids) >= self.top_hard:
                    break
        shutil.move(self.hard_samples_filename + '.tmp', self.hard_samples_filename)
        self.hard_samples = list(hard_sample_ids)
        logging.info('[Daemon] analyzed logs')
