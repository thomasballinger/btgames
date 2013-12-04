#!/usr/bin/env python
"""Commands for testing bittorrent clients on Amazon"""

from fabric.api import run, sudo, local, cd, env
from fabric.operations import put, get, prompt
from fabric.contrib.files import exists, append
from fabric.context_managers import settings
from fabric.api import env
import os
import time

import start_instance

def installTracker():
    """Installs opentracker"""
    sudo('apt-get update')
    sudo('apt-get -y install cvs make git build-essential lib32z-dev')
    run('cvs -d :pserver:cvs@cvs.fefe.de:/cvs -z9 co libowfat')
    with cd("libowfat"):
        run('make')
    run('git clone git://erdgeist.org/opentracker')
    with cd("opentracker"):
        run('make')

def startTracker():
    run('screen -d -m "opentracker/opentracker"', pty=False)

def getAnnounceUrl():
    user, host = env.host_string.split('@')
    announce = 'http://%s:6969/announce' % (host,)
    print 'announce url:', announce
    return announce

def installDeluge():
    sudo('apt-get update')
    sudo('apt-get install -y deluge-console deluged buildtorrent')

def seedFile(datafilename, announce):
    """Uploads file, creates a torrent file for it, and seeds it"""

    put(datafilename, os.path.basename(datafilename))
    run('buildtorrent -a %s %s test.torrent' % (announce, os.path.basename(datafilename)))
    run('deluged')
    time.sleep(10)
    run('deluge-console add test.torrent')
    get('test.torrent', 'test.torrent')

def newInstance():
    access, pem = start_instance.start_instance()
    print 'set up instance, access with:'
    print 'ssh %s -i %s' % (access, pem)


def newClient(filename, announce):
    access, pem = start_instance.start_instance()
    with settings(host_string=access, key_filename=pem):
        with settings(connection_attempts=10, timeout=10):
            print 'waiting for instance to boot up...'
            run('uname') # waiting for instance to boot up
        installDeluge()
        seedFile(filename)

def installYours():
    sudo('apt-get update')
    sudo('apt-get install -y python-pip python-dev build-essential git')
    run('git clone https://github.com/thomasballinger/bittorrent.git')
    with cd('bittorrent'):
        sudo('pip install -r requirements.txt')

def runYours(torrentfile):
    put('test.torrent', 'test.torrent')
    t0 = time.time()
    with cd('bittorrent'):
        run('time python main.py ../test.torrent')
    t = time.time() - t0
    print 'slow time is %2f seconds' % t

def scenario_one_peer_one_tracker(filename):
    (tracker, peer, yours), pem = start_instance.start_instances(3)
    with settings(key_filename=pem):
        with settings(host_string=tracker):
            installTracker()
            startTracker()
            announce = getAnnounceUrl()
        with settings(host_string=peer):
            installDeluge()
            seedFile(filename, announce)
        with settings(host_string=yours):
            print 'your server is:', env.host_string
            installYours()
            runYours('test.torrent')

