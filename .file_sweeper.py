import os
import psutil
import time
from dashcam import space_check

def file_sweeper(path=None, max_space=None):
    os.chdir(path)
    while not space_check(max_space):
        f = sorted(os.listdir(path))
        print('Removing: ' + f[0])
        os.remove(f[0])

if __name__ == '__main__':
    pwd = os.getcwd()

    file_sweeper(path=os.path.join(pwd,'vids'), max_space=13)
