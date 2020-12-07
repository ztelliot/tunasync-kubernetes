import delegator
import platform
from requests import get
import wget
import tarfile
import os
import sys

path = os.getcwd()


class build(object):
    def __init__(self):
        with open("config.json") as f:
            self.config = eval(f.read())

    def getPlat(self):
        plat = platform.machine()
        if plat.lower() in ['amd64', 'x86_64']:
            arch = 'amd64'
        elif plat.lower() == "aarch64":
            arch = 'arm64'
        else:
            arch = 'amd64'
        return arch

    def getBin(self):
        try:
            try:
                tag = get("https://api.github.com/repos/tuna/tunasync/releases/latest").json()['tag_name']
            except ConnectionError:
                tag = \
                    get(
                        "https://cold-breeze-c026.h-wkfx4vqhcj-xsv.workers.dev/repos/tuna/tunasync/releases/latest").json()[
                        'tag_name']
                # 备用地址 https://github-api-indol.vercel.app/repos/tuna/tunasync/releases/latest
            try:
                for line in delegator.run("chmod +x tunasync && ./tunasync -v").out.split('\n'):
                    if tag.split('v')[1] in line:
                        print("Already Downloaded...\nPass...")
                        return 1
            except:
                pass
            plat = self.getPlat()
            dl_url = 'https://github.com/tuna/tunasync/releases/download/{}/tunasync-linux-{}-bin.tar.gz'.format(tag,
                                                                                                                 plat)
            print("Download URL:" + dl_url)
            try:
                filename = wget.download(dl_url, 'tunasync-linux-bin.tar.gz')
                print("Download success")
            except:
                dl_url = str(dl_url).replace('github.com', 'g.ioiox.com/https://github.com')
                # 备用地址 github-omega.vercel.app/https://github.com
                print("Try " + dl_url)
                filename = wget.download(dl_url, 'tunasync-linux-bin.tar.gz')
                print("Download success")
            try:
                archive = tarfile.open(filename)
                archive.extractall()
                archive.close()
                print("Unzip success")
                try:
                    os.remove(filename)
                except:
                    pass
                delegator.run("chmod +x tunasync tunasynctl")
                return 1
            except:
                print("Unzip failed")
                try:
                    os.remove(filename)
                except:
                    pass
                return -1
        except:
            print("Get bin error")
            return -1

    def Manager(self):
        self.getBin()
        print(delegator.run('cp -f ../manager/manager.conf conf/ && cp -f ../manager/manager.dockerfile ../conf/Dockerfile && docker build conf -t manager:latest && rm -f conf/Dockerfile').out)
        return 0

    def Worker(self, image, concurrent, interval, mirrors, name):
        self.getBin()
        with open('../worker/worker.dockerfile') as f:
            with open('../conf/Dockerfile', 'w') as wf:
                wf.write(f.read().format(image=image))
        with open('../worker/worker.conf') as f:
            with open('conf/worker.conf', 'w') as wf:
                wf.write(f.read().format(concurrent=concurrent, interval=interval, name=name, mirrors=mirrors,
                                         ip=self.config['clusterIP'], port=self.config['port']))
        print(delegator.run('docker build conf -t worker:{} && rm -f conf/Dockerfile'.format(name)).out)
        return 0


if __name__ == "__main__":
    options = sys.argv
    if 'manager' in options:
        build().Manager()
    elif 'worker' in options:
        print("Please USE main.py to build worker image")
    else:
        print("Error")
