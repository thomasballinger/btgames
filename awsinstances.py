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
import sys
import time
from glob import glob

import boto.ec2

GROUPNAME = 'BTBenchmark'

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
        return new_key_pair_name, os.path.join(os.path.abspath('.'), new_key_pair_name+'.pem')

    keys = conn.get_all_key_pairs()

    for key in keys:
        fn = find_key_file(key.name)
        if fn:
            return key.name, fn
    else:
        return new_key(keys)

def find_key_file(name):
    if name[-4:] == '.pem':
        name = name[:-4]

    pems = glob(os.path.expanduser('~/*.pem'))
    pems.extend(glob('./*.pem'))
    pems.extend(glob(os.path.expanduser('./.ssh/*.pem')))
    for pem in pems:
        if name == os.path.basename(pem)[:-4]:
            return os.path.abspath(pem)

def get_ec2_connection(cached=[]):
    """Returns connection object"""
    if cached == []:
        access_key = os.environ['AMAZON_ACCESS_KEY']
        secret_key = os.environ['AMAZON_SECRET_KEY']
        conn = boto.ec2.connection.EC2Connection(access_key, secret_key)
        cached.append(conn)
    return cached[0]

def get_ami(conn):
    ami_id = 'ami-a73264ce' #ubuntu1204
    ami = conn.get_image(ami_id)
    return ami

def new_instance(label, wait=True):
    """Returns how to access started instance."""
    conn = get_ec2_connection()
    key, pem = get_key_pair_name_and_pem_file(conn)
    secgrp = get_security_group(conn)
    image = get_ami(conn)

    print 'keyname:', key
    reservation = image.run(key_name=key,
            security_groups=[secgrp],
            instance_type='m1.small')

    instance = reservation.instances[0]
    instance.add_tag('Name', label)
    instance.add_tag('Group', GROUPNAME)
    while wait:
        time.sleep(1)
        sys.stderr.write('.')
        sys.stderr.flush()
        instance.update()
        if instance.public_dns_name:
            return 'ubuntu@%s' % instance.public_dns_name, pem

def terminate_instance(*args, **kwargs):
    conn = get_ec2_connection()
    inst = get_instance(*args, **kwargs)
    conn.terminate_instances(instance_ids=[inst.id])

def get_instances():
    conn = get_ec2_connection()
    return [inst for inst in conn.get_only_instances() if inst.tags.get('Group') == GROUPNAME]

def get_instances_with_name(name):
    conn = get_ec2_connection()
    return [inst for inst in conn.get_only_instances() if inst.tags.get('Group') == GROUPNAME and inst.tags.get('Name') == name]

def get_instance(name=None, public_dns_name=None):
    if name and public_dns_name:
        raise ValueError("specify just one")
    conn = get_ec2_connection()
    if public_dns_name:
        instances = [inst for inst in conn.get_only_instances() if inst.public_dns_name == public_dns_name]
    elif name:
        instances = [inst for inst in conn.get_only_instances() if inst.tags.get('Name') == name and inst.state not in ['shutting-down', 'terminated']]
    else:
        raise ValueError('specify a name or hostname!')
    if len(instances) < 1:
        raise ValueError("Can't find instance from '%s'" % name or public_dns_name)
    elif len(instances) > 1:
        raise ValueError("Found two instances with name '%s'" % name or public_dns_name)
    return instances[0]

if __name__ == '__main__':
    #conn = get_ec2_connection()
    print 'authentication credentials ok!'
    #test_start_instances()
    #test()
    print get_instances()
    print get_instance('tom')
