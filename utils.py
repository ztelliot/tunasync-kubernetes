import delegator
import json
import re
import time
from configobj import ConfigObj
from prettytable import PrettyTable


def get_config():
    with open('config.json', 'r') as rf:
        mir = rf.read()
    return json.loads(mir)


config = get_config()


def ctl(cmd):
    res = Kubernetes.exec(config['name'], config['namespace'], "tunasynctl " + cmd)
    return res


def check():
    if ctl("-v") != -1:
        return 1
    else:
        return 0


def init():
    with open('manager/manager.yaml') as f:
        with open('conf/manager.yaml', 'w') as wf:
            wf.write(f.read().format(name=config['name'], namespace=config['namespace'], image=config['image'],
                                     sc=config['sc'], port=config['port']))
    res = Kubernetes.apply("conf/manager.yaml")
    if res > 0:
        pass


def color(msg):
    if 'ing' in msg:
        msg = "\033[33mO\033[0m"
    elif 'fail' in msg:
        msg = "\033[31mO\033[0m"
    elif 'success' in msg:
        msg = "\033[32mO\033[0m"
    else:
        pass
    return msg


class size_tools(object):
    @staticmethod
    def format(size_k):
        size_m = size_k / 1024
        size_g = size_m / 1024
        size_t = size_g / 1024
        if size_t > 1:
            human_readable_size = str(round(size_t, 2)) + 'T'
        elif size_g > 1:
            human_readable_size = str(round(size_g, 2)) + 'G'
        elif size_m > 1:
            human_readable_size = str(round(size_m, 2)) + 'M'
        else:
            human_readable_size = str(round(size_k, 2)) + 'K'
        return human_readable_size

    @staticmethod
    def XB_XiB(size_b: str):
        if 'T' in size_b.upper():
            size_b = str(
                round((float(size_b.split('T')[0]) * 1000 * 1000 * 1000 * 1000 / (1024 * 1024 * 1024 * 1024)), 2)) + 'T'
        elif 'G' in size_b.upper():
            size_b = str(round((float(size_b.split('G')[0]) * 1000 * 1000 * 1000 / (1024 * 1024 * 1024)), 2)) + 'G'
        elif 'K' in size_b.upper():
            size_b = str(round((float(size_b.split('K')[0]) * 1000 * 1000 / (1024 * 1024)), 2)) + 'K'
        else:
            pass
        return size_b


def manager_stat():
    infos = status()
    table = PrettyTable(['Pod状态', 'cpu', 'mem'])
    table.align = 'l'
    info = infos.process(config['name'])
    if not info['pod']:
        info['pod']['status'] = '-'
    if not info['top']:
        info['top']['cpu'] = info['top']['mem'] = '-'
    table.add_row([info['pod']['status'], info['top']['cpu'], info['top']['mem']])
    print(table)


def control():
    while 1:
        config = get_config()
        infos = status()
        table = PrettyTable(
            ['', '名称', '状态', 'Pod状态', '大小(本次)', '上次同步(用时)', '下次同步', '进度', '速度', '剩余时间', '文件进度', '当前文件(序号)', 'cpu', 'mem'])
        table.align = 'l'
        for i, name in enumerate(config['mirrors']):
            info = infos.process(name)
            if not info['pod']:
                info['pod']['status'] = '-'
            if not info['top']:
                info['top']['cpu'] = info['top']['mem'] = '-'
            try:
                last_time = time.strftime("%m-%d %H:%M:%S", time.localtime(int(info['job']['last_time'])))
                next_time = time.strftime("%m-%d %H:%M:%S", time.localtime(int(info['job']['next_time'])))
                if last_time == next_time:
                    last_time = '正在首次同步'
                    next_time = '-'
                if info['job']['status'] == 'syncing' and config['mirrors'][name]['type'] == 'rsync':
                    try:
                        if info['job']['chk_remain'] and info['job']['total']:
                            chk_rate = str(round(100 * (1 - info['job']['chk_remain'] / info['job']['total']), 2)) + '%'
                        else:
                            chk_rate = 'null'
                        table.add_row([i + 1, name, color(info['job']['status']), info['pod']['status'],
                                       '{}({})'.format(info['job']['size'], info['job']['now_size']),
                                       '{}({})'.format(last_time, info['job']['pass_time']), next_time,
                                       info['job']['rate'], info['job']['speed'], info['job']['remain'], chk_rate,
                                       '{}({})'.format(info['job']['file_name'], info['job']['chk_now']),
                                       info['top']['cpu'], info['top']['mem']])
                    except:
                        table.add_row(
                            [i + 1, name, color(info['job']['status']), info['pod']['status'], info['job']['size'],
                             '{}({})'.format(last_time, info['job']['pass_time']), next_time, '获', '取', '失', '败', '...',
                             info['top']['cpu'], info['top']['mem']])
                else:
                    table.add_row(
                        [i + 1, name, color(info['job']['status']), info['pod']['status'], info['job']['size'],
                         '{}({})'.format(last_time, info['job']['pass_time']), next_time, '-', '-', '-', '-', '-',
                         info['top']['cpu'], info['top']['mem']])
            except:
                try:
                    table.add_row(
                        [i + 1, name, color('disabled'), info['pod']['status'], '', '', '', '', '', '', '', '',
                         info['top']['cpu'], info['top']['mem']])
                except:
                    pass
        del infos
        print(table)
        id = input("输入需要操作的镜像序号：")
        i = 1
        name = ''
        for mirror in config['mirrors']:
            if str(i) == id:
                name = mirror
                break
            i += 1
        if name == '':
            print("序号不存在")
            break
        else:
            mirror = mirror_control(name)
        while 1:
            mode = input("请选择操作：\n1.删除镜像\n2.禁用镜像\n3.启用镜像\n4.停止同步\n5.开始同步\n6.更新大小\n7.立即重试\n8.日志最后10行\n9.返回\n")
            if mode:
                mode = int(mode)
            else:
                return 0
            if mode == 1:
                mirror.delete()
                break
            elif mode == 2:
                mirror.disable()
            elif mode == 3:
                mirror.enable()
            elif mode == 4:
                print(mirror.ctl_control('stop', name))
            elif mode == 5:
                print(mirror.ctl_control('start', name))
            elif mode == 6:
                print(mirror.refresh())
            elif mode == 7:
                mirror.ctl_control('restart', name)
            elif mode == 8:
                print(mirror.logs())
            else:
                break
        del mirror


class Kubernetes(object):
    @staticmethod
    def apply(file):
        res = delegator.run("kubectl apply -f " + file).out
        if "created" in res:
            print("Create Success")
            print(delegator.run("kubectl describe pod -f " + file).out)
            return 1
        else:
            print(res)
            return -1

    @staticmethod
    def exec(name, ns, cmd):
        command = "kubectl exec deploy/{name} -n {ns} -- {cmd}".format(name=name, ns=ns, cmd=cmd)
        res = delegator.run(command).out
        return res

    @staticmethod
    def delete(file=''):
        if file:
            res = delegator.run("kubectl delete -f " + file).out
        else:
            res = "Err"
            pass
        return res

    @staticmethod
    def info(ns=''):
        status = {'pods': [], 'tops': []}
        if ns:
            pods = delegator.run("kubectl get pods -n {ns}".format(ns=ns)).out.split('\n')
            for pod in pods:
                if pod:
                    infos = pod.split()
                    info = {"name": infos[0], "ready": infos[1], "status": infos[2], "restarts": infos[3]}
                    status['pods'].append(info)
            tops = delegator.run("kubectl top pods -n {ns}".format(ns=ns)).out.split('\n')
            for top in tops:
                if top:
                    infos = top.split()
                    info = {'name': infos[0], 'cpu': infos[1], 'mem': infos[2]}
                    status['tops'].append(info)
        return status

    @staticmethod
    def logs(name, ns):
        return delegator.run("kubectl logs deployment/{} -n {}".format(name, ns)).out


class mirror_control(object):
    def __init__(self, name):
        self.name = name
        self.conf = get_config()
        self.ns = self.conf['namespace']

    def ctl_control(self, action, size=''):
        worker = self.name
        mirror = self.name
        actions = ['start', 'stop', 'disable', 'restart']
        worker_actions = ['reload', 'rm-worker']
        if action == 'flush':
            return ctl("flush")
        elif action == 'set-size':
            return ctl("set-size -w {} {} {}".format(worker, mirror, size))
        elif action in actions:
            return ctl(action + " -w " + worker + " " + mirror)
        elif action in worker_actions:
            return ctl(action + " -w " + worker)
        else:
            return 0

    def add(self):
        mirror_conf = ConfigObj(list_values=False)
        mirror_conf.filename = 'conf/' + self.name + '.conf'
        provider = input("同步方式[rsync]：") or 'rsync'
        upstream = input("同步源(rsync方式的链接结尾必须为/)：")
        con = input("线程数[10]：") or '10'
        interval = input("同步周期(分)[1440]：") or '1440'
        memory_limit = input("内存限制(不填不限制)：") or ''
        image = input("使用的容器镜像(ztelliot/tunasync_worker:rsync)：") or 'ztelliot/tunasync_worker:rsync'
        data_size = input("镜像最大占用大小(1Ti)：") or '1Ti'
        log_size = '1Gi'
        command = ''
        if provider == "command":
            command = '\"' + input("同步脚本位置(绝对路径)：") + '\"'
        elif "rsync" in provider:
            other_options = input("额外的rsync选项(按空格划分)：").split()
            rsync_options = "["
            for option in other_options:
                if option:
                    rsync_options += "\"{}\", ".format(option)
            rsync_options += "\"--info=progress2\"]"
        else:
            pass
        use_ipv6 = 'false'
        mirror = {"name": '\"' + self.name + '\"', "provider": '\"' + provider + '\"',
                  "upstream": '\"' + upstream + '\"', "use_ipv6": use_ipv6}
        if command:
            mirror['command'] = command
        if "rsync" in provider:
            mirror['rsync_options'] = rsync_options
        if memory_limit:
            mirror['memory_limit'] = '\"' + memory_limit + '\"'
        options = []
        addition_option = input('同步额外选项：')
        while addition_option:
            options.append(addition_option)
            addition_option = input()
        mirror_conf['[mirrors]'] = mirror
        self.conf['mirrors'][self.name] = {'type': provider}
        mirror_conf.write()
        if options:
            print("您设置的同步选项有:", options)
            with open('conf/' + self.name + '.conf', 'a+') as af:
                af.write('\n        [mirrors.env] \n')
                for addition_option in options:
                    af.write('        {}\n'.format(addition_option))
        with open('config.json', 'w') as cf:
            cf.write(json.dumps(self.conf))
        worker = ''
        with open('conf/{}.conf'.format(self.name)) as f:
            with open('worker/worker.conf') as wf:
                lines = wf.read().format(concurrent=con, interval=interval, mirrors=f.read(), name=self.name,
                                         manager=self.conf['name'], port=self.conf['port']).split('\n')
                for line in lines:
                    worker += '    {}\n'.format(line)
        if self.conf['node']:
            node = "nodeSelector:\n        kubernetes.io/hostname: " + self.conf['node']
        else:
            node = ""
        with open('worker/worker.yaml') as f:
            with open('conf/{}.yaml'.format(self.name), 'w') as wf:
                wf.write(
                    f.read().format(name=self.name, namespace=self.ns, sc=self.conf['sc'], conf=worker, image=image,
                                    data_size=data_size, log_size=log_size, node=node))
        Kubernetes.apply('conf/{}.yaml'.format(self.name))
        return 0

    def job(self):
        jobs = json.loads(ctl("list --all"))
        for job in jobs:
            if job['name'] == self.name:
                return job

    def size(self):
        size = ''
        if self.conf['mirrors'][self.name]['type'] == 'rsync':
            if self.job()['status'] == 'success':
                size = Kubernetes.exec(name=self.name, ns=self.ns,
                                       cmd="tac /var/log/tunasync/latest | grep \"^Total file size: \" | head -n 1 | grep -Po \"[0-9\\.]+[MGT]\"")
        if size:
            pass
        else:
            size = size_tools.format(int(Kubernetes.exec(name=self.name, ns=self.ns,
                                                   cmd="df /data/mirrors/" + self.name + " | grep " + self.name + " | awk '{print $3}'")))
            if size == '-1K':
                return self.job()['size']
        return size

    def delete(self):
        print(Kubernetes.delete('conf/{}.yaml'.format(self.name)))
        print(self.ctl_control('disable'))
        print(self.ctl_control('flush'))
        print(self.ctl_control('rm-worker'))
        self.conf['mirrors'].pop(self.name)
        with open('config.json', 'w') as df:
            df.write(json.dumps(self.conf))
        df.close()
        return 1

    def disable(self):
        print("禁用中...")
        print(self.ctl_control('disable'))
        print(self.ctl_control('flush'))
        return 0

    def enable(self):
        print("启用中...")
        print(self.ctl_control('start'))
        print(self.ctl_control('flush'))
        return 0

    def refresh(self):
        return self.ctl_control('set-size', self.size())

    def pod_logs(self):
        return Kubernetes.logs(self.name, self.ns)

    def logs(self, num=10):
        return Kubernetes.exec(self.name, self.ns, "tail -n {}  /var/log/tunasync/latest".format(num))


class status(object):
    def __init__(self):
        self.conf = get_config()
        self.workers = Kubernetes.info(self.conf['namespace'])
        self.jobs = json.loads(ctl("list --all").strip('\n'))

    def match_name(self, pod_name, job_name):
        pod_name = pod_name.split('-')[:-2]
        job_name = job_name.split('-')
        if len(pod_name) == len(job_name):
            for i in range(len(pod_name)):
                if pod_name[i] != job_name[i]:
                    return 0
            return 1
        else:
            return 0

    def match(self, name):
        base = {'job': {}, 'pod': {}, 'top': {}}
        try:
            base['type'] = self.conf['mirrors'][name]['type']
        except:
            base['type'] = ''
        for job in self.jobs:
            if job['name'] == name:
                base['job'] = job
                break
        for pod in self.workers['pods']:
            if self.match_name(pod['name'], name):
                base['pod'] = pod
                break
        for top in self.workers['tops']:
            if self.match_name(top['name'], name):
                base['top'] = top
                break
        return base

    def process(self, name):
        info = self.match(name)
        job_info = {}
        if info['job']:
            job = info['job']
            last_begin_time = job['last_started_ts']
            last_time = job['last_ended_ts']
            next_time = job['next_schedule_ts']
            pass_time = str(last_time - last_begin_time)
            if int(pass_time) <= 0:
                pass_time = '-'
            size = job['size']
            status = job['status']
            rsync_size = file_name = remain = speed = rate = total = chk_now = chk_remain = '-'
            if status == 'syncing' and info['type'] == 'rsync':
                logs = mirror_control(name).logs(5).split("\n")
                for log in logs:
                    if 'B/s' in log:
                        if 'xfr' in log:
                            chk = str(re.findall(r'[(](.*?)[)]', log)[0])
                            chk_now = re.findall(r'[#](.*?)[,]', chk)[0]
                            chk_remain = re.findall(r'[=](.*?)[/]', chk)[0]
                            total = chk.split("/")[1]
                        parts = log.split(" ")
                        for part in parts:
                            if '%' in part:
                                rate = part
                            elif 'B/s' in part:
                                speed = part
                            elif ':' in part:
                                remain = part
                            elif '=' in part or '#' in part:
                                pass
                            elif part and pass_time == '-':
                                rsync_size = size_tools.XB_XiB(part)
                    elif log:
                        files = log.split('/')
                        file_name = files[-1]
                try:
                    chk_remain = int(chk_remain)
                    total = int(total)
                except:
                    chk_remain = total = 0
                try:
                    job_info = {'status': status, 'size': size, 'last_time': last_time, 'pass_time': pass_time,
                                'chk_now': chk_now, 'chk_remain': chk_remain, 'total': total, 'rate': rate,
                                'speed': speed, 'remain': remain, 'file_name': file_name, 'next_time': next_time,
                                'now_size': rsync_size}
                except:
                    job_info = {'status': status, 'size': size, 'last_time': last_time, 'pass_time': pass_time,
                                'next_time': next_time}
            else:
                job_info = {'status': status, 'size': size, 'last_time': last_time, 'pass_time': pass_time,
                            'next_time': next_time}
        return {"job": job_info, "pod": info['pod'], "top": info['top']}
