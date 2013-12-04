#!/usr/bin/env python
"""Commands for testing bittorrent clients on Amazon"""

from fabric.api import run, sudo, local, cd, env
from fabric.operations import put, get, prompt
from fabric.contrib.files import exists, append
from fabric.context_managers import settings
from fabric.api import env
import os
import sys
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

def _getAnnounceUrl():
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

    run('deluged; sleep 1; deluge-console add test.torrent')
    # For some reasons doing these separately doesn't work will
    # This seems to work for now...

    get('test.torrent', 'test.torrent')

def newInstance():
    access, pem = start_instance.start_instance()
    print 'set up instance, access with:'
    print 'ssh %s -i %s' % (access, pem)
    env.host_string = access
    env.key_filename = pem

def installScenario1(who, filename):
    """takes a data filename and a user - One peer, one tracker"""
    user = _get_userscript(who)
    (tracker, peer, yours), pem = start_instance.start_instances(3)
    with settings(key_filename=pem):
        with settings(host_string=tracker):
            installTracker()
            startTracker()
            announce = _getAnnounceUrl()
        with settings(host_string=peer):
            installDeluge()
            seedFile(filename, announce)
        with settings(host_string=yours):
            user.install()
            print 'to run scenario, try "fab run_scenario_1:<username> -H %s -i %s"' % (env.host_string, env.key_filename)

def runScenario1(who, torrentfile):
    """Whose code to test, which torrent files - One peer, one tracker"""
    user = _get_userscript(who)
    user.torrentfile(torrentfile)
    t0 = time.time()
    user.download(torrentfile)
    t = time.time() - t0
    print 'command took %2f seconds' % t

def _get_userscript(who):
    if who[-3:] == '.py':
        who = who[:-3]
    if '.' not in sys.path:
        sys.path.append('.')
    try:
        user_functions = __import__(who)
    except ImportError:
        print os.getcwd()
        raise ValueError("can't find script for user %s" % who)
    if not (hasattr(user_functions, 'install') and
            hasattr(user_functions, 'torrentfile') and
            hasattr(user_functions, 'download')):
        raise ValueError("User file must have 'install', 'torrentfile', and 'download' functions")
    return user_functions

def install(who):
    user = _get_userscript(who)
    user.install()
    print 'Should be installed on', env.host_string
    print 'To look around, try'
    print 'ssh %s -i %s' % (env.host_string, env.key_filename)
