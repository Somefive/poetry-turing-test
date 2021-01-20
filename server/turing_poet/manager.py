from typing import List, Dict, Set, Tuple
from .poetry import PoetryTest, PoetryTestCase, PoetryLines, PoetryLinesType, PoetryTestCaseAnswer
import random


class PoetryTestManager(object):


    def __init__(self, poetry_tests_filename: str):
        self.poetry_tests: List[PoetryTest] = [PoetryTest(line) for line in open(poetry_tests_filename)]
        self.poetry_tests_mapping: Dict[str, PoetryTest] = {}
        self.poetry_lines_type_mapping: Dict[str, PoetryLinesType] = {}
        for test in self.poetry_tests:
            self.poetry_tests_mapping[test._id] = test
            for lines in test.human:
                self.poetry_lines_type_mapping[lines._id] = PoetryLinesType.HUMAN
            for lines in test.ai:
                self.poetry_lines_type_mapping[lines._id] = PoetryLinesType.AI
            for lines in test.jiuge:
                self.poetry_lines_type_mapping[lines._id] = PoetryLinesType.JIUGE


    def generate_testcases(self, num_testcases: int,
                                 num_options: int,
                                 ground_truth_prob: float = 1.0,
                                 candidate_ids: List[str] = [],
                                 max_retry_ratio: float = 5.0,
                                 include_jiuge: bool = False) -> List[PoetryTestCase]:
        self.testcases: List[PoetryTestCase] = []
        self.testcase_ids: Set[str] = set()
        for _id in candidate_ids:
            test = self.poetry_tests_mapping.get(_id, None)
            if test is not None:
                testcase = test.generate_testcase(num_options, ground_truth_prob)
                if testcase is not None:
                    self.testcases.append(testcase)
                    self.testcase_ids.add(testcase._id)
                    if len(self.testcases) >= num_testcases:
                        break
        retry_times, max_retry_times = 0, int(max_retry_ratio * num_options)
        while len(self.testcases) < num_testcases and retry_times < max_retry_times:
            test = random.choice(self.poetry_tests)
            if test._id in self.testcase_ids:
                retry_times += 1
                continue
            testcase = test.generate_testcase(num_options, ground_truth_prob, include_jiuge=include_jiuge)
            if testcase is None:
                retry_times += 1
                continue
            self.testcases.append(testcase)
            self.testcase_ids.add(testcase._id)
        return self.testcases


    def submit_answers(self, raw_answers: List[dict]) -> Tuple[int, List[PoetryTestCaseAnswer]]:
        answers = [PoetryTestCaseAnswer(raw_answer) for raw_answer in raw_answers]
        return self._submit_answers(answers), answers


    def _submit_answers(self, answers: List[PoetryTestCaseAnswer]) -> int:
        score = 0
        for answer in answers:
            if answer.time <= 0:
                continue
            real_answer = ''
            for option in answer.options:
                if self.poetry_lines_type_mapping.get(option, None) == PoetryLinesType.HUMAN:
                    real_answer = option
                    break
            answer.correct = real_answer == answer.select_id
            score += answer.correct
        return score
