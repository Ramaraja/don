# common.py: Common functions and data structures used by multiple modules.

import paramiko
import sys
import re
import pprint
import subprocess

# Program settings
settings = {
        'debug' : False,
        }

# Helper functions.
def debug (msg):
    if settings['debug']:
        if not sys.stdout == sys.__stdout__:
            tmp = sys.stdout
            sys.stdout = sys.__stdout__
            print('DEBUG: ' + msg)
            sys.stdout = tmp
        else:
            print('DEBUG: ' + msg)

def error (msg):
    if not sys.stdout == sys.__stdout__:
        tmp = sys.stdout
        sys.stdout = sys.__stdout__
        print('ERROR: ' + msg)
        sys.stdout = tmp
    else:
        print('ERROR: ' + msg)

def warning (msg):
    if not sys.stdout == sys.__stdout__:
        tmp = sys.stdout
        sys.stdout = sys.__stdout__
        print('WARNING: ' + msg)
        sys.stdout = tmp
    else:
        print('WARNING: ' + msg)


def status_update (msg):
    if not sys.stdout == sys.__stdout__:
        tmp = sys.stdout
        sys.stdout = sys.__stdout__
        print('STATUS: ' + msg)
        sys.stdout = tmp
    else:
        print('STATUS: ' + msg)

def dump_json (json_info, json_filename):
    import json
    try:
        outfile = open(json_filename, "w")
    except IOError, e:
        print e
        print 'Couldn\'t open <%s>; Redirecting output to stdout' % json_filename
        outfile = sys.stdout

    json.dump(json_info, outfile)
    outfile.flush()
    outfile.close()

def load_json (json_filename):
    import json
    try:
        infile = open(json_filename, "r")
    except IOError, e:
        print e
        print 'Couldn\'t open <%s>; Error!' % json_filename
        return None

    tmp = json.load(infile)
    infile.close()
    return tmp

def connect_to_box (server, username, password,timeout=3) :
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(server, username= username, password= password,timeout=timeout)
    except:
        return None
    return ssh

# this function i will modify to get data from a file instead of giving command directly
def ssh_cmd(ssh, cmd) :
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(cmd)
    error = ssh_stderr.read()
    if len(error):
        print 'ERROR: ' + error
    output = ssh_stdout.read()
    ssh_stdout.flush()
    return output

# TODO (right now assumes subnet mask to be 24 bits long)
def get_subnet (ip):
    subnet = '.'.join(ip.split('.')[:3])
    return subnet

def get_router (namespace, info):
    routers = info.get('routers', None)
    if not routers:
        return 'Unknown'
    for router in routers.keys():
        if routers[router]['id'] in namespace:
            return router

    return 'Unknown'

# TODO (guaranteed way of figuring out whether network is private or public)
def is_network_public (ip, vm, info):
    vm_entry = info['vms'].get(vm)
    entry = vm_entry['interfaces'].get(ip, None)
    if not entry:
        error('Interface: ' + ip + ' does not exist!')
        return False
    if re.search('public', entry['network']):
        return True
    return False

def get_intf_ip (info, interface):
    intf = strip_interface(interface)
    return info['tap_to_ip'].get(intf, 'x.x.x.x')

def ip_to_intf (info, ip):
    for intf, intf_ip in info['tap_to_ip'].iteritems():
        if intf_ip == ip:
            return intf
    return None

def router_to_namespace (info, router):
    router_entry = info['routers'].get(router, None)
    if not router_entry:
        return None
    net_id = router_entry.get('id', None)
    if not net_id:
        return None
    return 'qrouter-' + net_id

def intf_to_namespace (info, intf):
    nms_dict = info['namespaces']
    for nms in nms_dict.keys():
        if nms_dict[nms].has_key('interfaces'):
            if nms_dict[nms]['interfaces'].has_key(intf):
                return nms
    return None

def get_ip_network (info, vm, ip):
    intf_entry = info['vms'][vm]['interfaces'].get(ip, None)
    if not intf_entry:
        return 'unknown'
    return intf_entry.get('network', 'unknown')

def get_vlan_tag (info, interface):
    intf = strip_interface(interface)

    intf = 'qvo' + intf
    br_int = info['bridges']['br-int']
    debug ('Getting vlan tag for ' + intf)
    if br_int['ports'].has_key(intf):
        return br_int['ports'][intf].get('tag', '0')
    return '0'

def strip_interface (intf):
    x = intf
    x = x.replace('tap', '')
    x = x.replace('qbr', '')
    x = x.replace('qvb', '')
    x = x.replace('qvo', '')
    return x

def get_port_ovs_id_tag (info, vm, port_ip):
    for key, ip in info['tap_to_ip'].iteritems():
        if ip == port_ip:
            qvo = 'qvo'+key
            qvo_entry = info['bridges']['br-int']['ports'].get(qvo, None)
            if not qvo_entry:
                return None
            ovs_id = qvo_entry.get('id', None)
            ovs_tag = qvo_entry.get('tag', None)
            return (ovs_id, ovs_tag)
    return None

def execute_cmd (cmd, sudo=False, shell=False, env=None):
    if sudo:
        if shell == False:
            mycmd = ['sudo'] + cmd
        else:
            mycmd = 'sudo ' + cmd
    else:
        mycmd = cmd

    pprint.pprint(mycmd)
    return subprocess.check_output(mycmd,
                shell=shell,
                stderr=subprocess.STDOUT,
                env=env,
                universal_newlines=True).replace('\t', '    ')

