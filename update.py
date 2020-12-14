import json
import delegator
from utils import mirror_control


jobs = json.loads(delegator.run("tunasynctl list --all").out.strip('\n'))
for job in jobs:
    mirror = job['name']
    print(mirror)
    print(mirror_control(mirror).refresh(), end='')
    if job['status'] == 'failed':
        print("执行失败，开始重试...", mirror_control(mirror).ctl_control('start'), end='')
    print('----------')
