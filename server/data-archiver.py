import subprocess
from datetime import datetime
import time

while True:
    target_path = 'data/archived/%s.tar.gz' % datetime.now().strftime('%Y%m%d%H')
    subprocess.call([
        'tar', '-cf', target_path, 'data/v2', 'logs'
    ])
    print('[%s] saved to %s' % (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), target_path))
    time.sleep(600)