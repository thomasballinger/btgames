from fabric.api import run, sudo, local, cd, env
from fabric.operations import put, get, prompt
from fabric.contrib.files import exists, append
from fabric.context_managers import settings
from fabric.api import env
import time
import os

def install():
    sudo('apt-get update')
    sudo('apt-get install -y python-pip python-dev build-essential git')
    run('git clone https://github.com/thomasballinger/bittorrent.git')
    with cd('bittorrent'):
        sudo('pip install -r requirements.txt')

def torrentfile(torrentfile):
    put(os.path.basename(torrentfile), 'test.torrent')

def download(torrentfile):
    with cd('bittorrent'):
        run('time python main.py ../test.torrent')
