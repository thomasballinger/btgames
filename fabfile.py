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

import awsinstances

def install_tracker():
    """Installs opentracker"""
    sudo('apt-get update')
    sudo('apt-get -y install cvs make git build-essential lib32z-dev')
    run('cvs -d :pserver:cvs@cvs.fefe.de:/cvs -z9 co libowfat')
    with cd("libowfat"):
        run('make')
    run('git clone git://erdgeist.org/opentracker')
    with cd("opentracker"):
        run('make')
    port = 6969
    user, host = env.host_string.split('@')
    inst = awsinstances.get_instance(public_dns_name=host)
    announce = 'http://%s:%d/announce' % (inst.public_dns_name, port)
    _save_announce_url(announce)

def start_tracker():
    """Starts a tracker running - only run on trackers"""
    run('screen -d -m "opentracker/opentracker"', pty=False)

def _hostname(instance):
    return 'ubuntu@%s' % instance.public_dns_name

def all_instances(name=None):
    """Use all instances for following commands"""
    if name is not None:
        hosts = [awsinstances.get_instance(name)]
    else:
        hosts = awsinstances.get_instances()
    env.key_filename = awsinstances.find_key_file(hosts[0].key_name)
    env.hosts = [_hostname(x) for x in hosts]

def instance(name):
    """instance:name - use this instance for following commands"""
    all_instances(name=name)

def list():
    """List current instances: their names and hoststrings"""
    if not env.hosts:
        print 'no instances currently in use, listing all instances:'
        instances = awsinstances.get_instances()
    else:
        instances = [awsinstances.get_instance(public_dns_name=env.host_string.split('@')[1])]
    for inst in instances:
        print inst.tags.get('Name', '(no name)'), _hostname(inst)

def wait_until_ready():
    """Wait until all specified instances are ready"""
    while True:
        print 'outer loop'
        with settings(warn_only=True, connection_attempts=1000, timeout=.1):
            print 'inner loop'
            result = run('ping -c 1 -W 1 google.com')
            if result.return_code == 0:
                break

def install_deluge():
    """Install the Deluge bittorrent client"""
    sudo('apt-get update')
    sudo('apt-get install -y deluge-console deluged buildtorrent')

ANNOUNCE_URL_FILE = 'saved_announce_url.txt'

def _get_saved_announce_url():
    with open(ANNOUNCE_URL_FILE) as f:
        return f.read()

def _save_announce_url(announce):
    with open(ANNOUNCE_URL_FILE, 'w') as f:
        f.write(announce)

def seed_file(datafilename, tracker=None):
    """seed_file:bigFile.txt[,tracker] - Uploads file, creates a torrent file for it, and seeds it.  If tracker name not provided, use saved announce url"""

    if tracker is None:
        announce = _get_saved_announce_url()
    else:
        inst = awsinstances.get_instance(tracker)
        port = 6969
        announce = 'http://%s:%d/announce' % (inst.public_dns_name, port)
    put(datafilename, os.path.basename(datafilename))
    run('buildtorrent -a %s "%s" test.torrent' % (announce, os.path.basename(datafilename)))

    run('deluged; sleep 1; deluge-console add test.torrent')
    # For some reasons doing these separately doesn't work will
    # This seems to work for now...

    get('test.torrent', 'test.torrent')

def new_instance(name):
    """new_instance:nameOfInstance - Boot up a new instance, use it for following commands"""
    access, pem = awsinstances.new_instance(name)
    print 'set up instance, access with:'
    print 'ssh %s -i %s' % (access, pem)
    env.host_string = access
    env.key_filename = pem

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
    """install:yourModule - Uses custom install function from yourModule.py on current instance"""
    user = _get_userscript(who)
    user.install()
    print 'Should be installed on', env.host_string
    print 'To look around, try'
    print 'ssh %s -i %s' % (env.host_string, env.key_filename)

def install_scenario_1(who, filename):
    """takes a data filename and a user - One peer, one tracker"""
    user = _get_userscript(who)
    (tracker, peer, yours), pem = [awsinstances.new_instance(name) for name in ['tracker', 'peer', 'client']]
    with settings(key_filename=pem):
        with settings(host_string=tracker):
            install_tracker()
            start_tracker()
        with settings(host_string=peer):
            install_deluge()
            seed_file(filename)
        with settings(host_string=yours):
            user.install()
            print 'to run scenario, try "fab run_scenario_1:<username> -H %s -i %s"' % (env.host_string, env.key_filename)
    list()

def run_scenario_1(who, torrentfile):
    """Whose code to test, which torrent files - One peer, one tracker"""
    user = _get_userscript(who)
    user.torrentfile(torrentfile)
    t0 = time.time()
    user.download()
    t = time.time() - t0
    print 'command took %2f seconds' % t
