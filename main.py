from utils import control, mirror_control, manager_stat, check


def menu():
    try:
        while 1:
            mode = input("1.新增镜像\n2.镜像管理\n3.Manager状态\n")
            if mode:
                mode = int(mode)
            else:
                break
            if mode == 1:
                name = input("输入mirror名称(不能重复)：")
                mirror_control(name).add()
            elif mode == 2:
                control()
            elif mode == 3:
                manager_stat()
            else:
                return 0
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    if check():
        menu()
