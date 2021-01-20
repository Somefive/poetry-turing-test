from turing_poet.manager import PoetryTestManager
from turing_poet.daemon import Daemon

manager = PoetryTestManager(poetry_tests_filename='data/v2/poetry-turing-tests.jsonl')
daemon = Daemon(
    poetry_ctr_filename='data/v2/ctr.csv',
    user_record_filename='data/v2/user-record.csv',
    log_filename='logs/record.log',
    poetry_tests=manager.poetry_tests
)
daemon.analyze_log()