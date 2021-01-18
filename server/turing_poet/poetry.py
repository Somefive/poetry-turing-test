from typing import Tuple, List, Optional, Set
import json
import random
import numpy as np
from enum import Enum

class PoetryLinesType(Enum):
    HUMAN = 0
    AI = 1


class PoetryLines(object):

    def __init__(self, _id: str, content: List[str]):
        self._id = _id
        self.content = content

    def as_json(self):
        return {
            'id': self._id,
            'content': self.content
        }


class PoetryBase(object):

    def __init__(self, _id: str, title: str, author: str, dynasty: str, scheme: Tuple[int, int]):
        self._id = _id
        self.title = title
        self.author = author
        self.dynasty = dynasty
        self.scheme = scheme


class PoetryTestCase(PoetryBase):

    def __init__(self, _id: str, title: str, author: str, dynasty: str, scheme: Tuple[int, int], choices: List[PoetryLines]):
        super().__init__(_id, title, author, dynasty, scheme)
        self.choices = choices

    def as_json(self, exclude_fields: List[str]):
        obj = {
            'id': self._id,
            'title': self.title,
            'author': self.author,
            'dynasty': self.dynasty,
            'scheme': list(self.scheme),
            'choices': [choice.as_json() for choice in self.choices]
        }
        for field in exclude_fields:
            if field in obj:
                del obj[field]
        return obj

    def as_logstr(self):
        return '%s:%s' % (self._id, ','.join([choice._id for choice in self.choices]))


class PoetryTest(PoetryBase):

    def __init__(self, jsonstr: str):
        obj = json.loads(jsonstr.strip())
        super().__init__(_id=obj.get('id', ''),
                         title=obj.get('title', ''),
                         author=obj.get('author', ''),
                         dynasty=obj.get('dynasty', ''),
                         scheme=tuple(obj.get('scheme', [0, 0])))
        self.human: List[PoetryLines] = [
            PoetryLines(obj.get('id', ''), obj.get('content', []))
        for obj in obj.get('human', [])]
        self.ai: List[PoetryLines] = [
            PoetryLines(obj.get('id', ''), obj.get('content', []))
        for obj in obj.get('ai', [])]

    def generate_testcase(self, num_options: int, ground_truth_prob: float = 1.0) -> Optional[PoetryTestCase]:
        if len(self.human) == 0 or len(self.ai) + 1 < num_options:
            return None
        ground_truth = random.choice(self.human)
        choices = []
        if len(self.ai) >= num_options and random.random() > ground_truth_prob:
            for i in np.random.permutation(len(self.ai))[:num_options]:
                choices.append(self.ai[i])
        else:
            choices = [ground_truth]
            for i in np.random.permutation(len(self.ai))[:num_options - 1]:
                choices.append(self.ai[i])
            random.shuffle(choices)
        return PoetryTestCase(self._id, self.title, self.author, self.dynasty, self.scheme, choices)


class PoetryTestCaseAnswer(object):

    def __init__(self, obj: dict):
        self.options: List[str] = obj.get('options', [])
        self.select_id: str = obj.get('select_id', '')
        self.time: int = obj.get('time', -1)
        self.correct: Optional[bool] = None

    def as_logstr(self):
        return '%s|%s|%d|%s' % (','.join(self.options), self.select_id, self.time, self.correct)