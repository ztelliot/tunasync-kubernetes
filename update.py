import json
import delegator
from utils import mirror_control


jobs = json.loads(delegator.run("tunasynctl list --all").out.strip('\n'))
for job in jobs:
    mirror = job['name']
    print(mirror, ':', mirror_control(mirror).refresh())
    if job['status'] == 'failed':
        print(mirror, "执行失败，开始重试...")
        print(mirror_control(mirror).ctl_control('start'))
