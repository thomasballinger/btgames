#!/usr/bin/env python
"""Script for running Freesurfer on an amazon EC2 instance

Requires amazon access key and amazon secret key - currently script
looks for these in the environment.

Warning: if you already have a security group called "remoteFreesurfer",
this script will enable access to port 22 tcp!  This isn't dangerous on
the machines we boot up, since only keypair access is allowed via ssh,
but could be very dangerous if you have other instances in this security group.
"""
import os
import time
from glob import glob

import boto.ec2

def get_security_group(conn):
    sec_group_name = 'allOpen'
    security_groups = conn.get_all_security_groups()
    #print security_groups
    try:
        fs_security_group = [sg for sg in security_groups if sg.name == sec_group_name][0]
        print sec_group_name, 'security group already exists'
    except IndexError:
        fs_security_group = conn.create_security_group(sec_group_name, 'Everything Open Security Group')
        print 'new security group created'
    try:
        fs_security_group.authorize(ip_protocol='tcp', from_port=1, to_port=65535, cidr_ip='0.0.0.0/0')
        fs_security_group.authorize(ip_protocol='udp', from_port=1, to_port=65535, cidr_ip='0.0.0.0/0')
        print 'new security rule created, allowing all tcp and udp access'
    except boto.ec2.connection.EC2ResponseError:
        print 'security rules already exist, allowing all tcp and udp access'
    return fs_security_group

def get_key_pair_name_and_pem_file(conn, pem_filename=None):
    """Tries to find existing key pairs, otherwise creates new"""

    def new_key(keys):
        new_key_pair_name, counter = 'BTbenchmark', 0
        while new_key_pair_name in [k.name for k in keys]:
            counter += 1
            new_key_pair_name = 'BTbenchmark'+str(counter)
        key = conn.create_key_pair(new_key_pair_name)
        print 'new key pair created:', new_key_pair_name
        key.save('.')
        print 'new key pair pem saved to current directory', os.path.abspath('.')
        return new_key_pair_name, os.path.join(os.path.abspath('.'), name+'.pem')

    keys = conn.get_all_key_pairs()
    if pem_filename:
        if not os.path.exists(pem_filename):
            raise EnvironmentError("pem file does not exist")
        pems = [pem_filename]
    else:
        pems = glob(os.path.expanduser('~/*.pem'))
        pems.extend(glob('./*.pem'))
    for pem in pems:
        name = os.path.basename(pem)[:-4]
        match = [k for k in keys if k.name == name]
        if match:
            return name, os.path.abspath(pem)
    else:
        return new_key(keys)

def get_ec2_connection():
    """Returns connection object"""
    access_key = os.environ['AMAZON_ACCESS_KEY']
    secret_key = os.environ['AMAZON_SECRET_KEY']
    conn = boto.ec2.connection.EC2Connection(access_key, secret_key)
    return conn

def get_ami(conn):
    ami_id = 'ami-a73264ce' #ubuntu1204
    ami = conn.get_image(ami_id)
    return ami

def _start_instance():
    """Returns how to access started instance. Blocks until instance is ready."""
    conn = get_ec2_connection()
    key, pem = get_key_pair_name_and_pem_file(conn)
    secgrp = get_security_group(conn)
    image = get_ami(conn)

    reservation = image.run(key_name=key,
            security_groups=[secgrp],
            instance_type='m1.small')

    instance = reservation.instances[0]
    instance.add_tag('BTbenchmark')
    return instance, pem

def start_instance():
    instance, pem = _start_instance()
    while True:
        time.sleep(1)
        print instance.update()
        if instance.state == 'running':
            time.sleep(45) # seems to take this long before an apt-get update will work correctly
            break
    return 'ubuntu@' + instance.public_dns_name, pem

def start_instances(n):
    """Start several instances without waiting for each one separately"""
    if n > 10:
        print 'really?'
        raise SystemExit()
    instances = [_start_instance() for _ in range(n)]
    while not all([inst.state == 'running' or inst.update() == 'running'
                   for inst, key in instances]): pass
    instances, keys = zip(*instances)
    time.sleep(45)
    assert all(key == keys[0] for key in keys), 'instances have different keys?'
    return ['ubuntu@' + inst.public_dns_name for inst in instances], keys[0]

def test():
    host, pem = start_instance()
    print 'Instance now running! Accessible at'
    print host
    print 'using pem'
    print pem
    print 'you need to log on as ubuntu'

def test_start_instances():
    print start_instances(2)

if __name__ == '__main__':
    conn = get_ec2_connection()
    print 'authentication credentials ok!'
    test_start_instances()
    #test()
