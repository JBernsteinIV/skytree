#!/usr/bin/python3
import ipaddress
import json
import re
import subprocess
import sys

""" UTILITIES SECTION """

def run_cmd(cmd, flags):
    command = [cmd, *flags]
    stdout  = subprocess.check_output(command)
    return stdout.decode('utf-8')

def format_to_list(devices=[], output=[]):
    template = {}
    for element in output.split('\n'):
    # If an empty line has been hit, we move on to the next device.
        if len(element) == 0 or element == '\n':
            if len(template) != 0:
                devices.append(template)
                # Reset for the next lspci device.
                template = {}
        else:
            key   = element.split(':')[0]
            # Split ONLY on the first colon ":", then merge all other output in the line together.
            # Use the '*' character to unpack the list into a string object.
            value = str(*[ el.replace('\t',"") for el in element.split(':',maxsplit=1)[1:] ])
            # Add the string objects to the template dictionary. 
            template[key] = value
    return devices

""" Take the indent level of the output string and use it to define a dictionary. """
"""
    TODO:
        * Try removing quiet flag from dmidecode.
        * Count the number of "Handles" that appear.
        * Use the number of handles to determine the data type for each section(object or list).
"""
def indent_to_dict(output, section):
    template     = {}
    for line in output.split('\\n'):
        left_val   = line.split(':')[0].strip()
        right_val  = str( [ re.sub('\n\t',':', val) for val in line.split(':')[1:] ] )
        if not template.get(section) or section == 'Memory Device':
            template[section] = []
        temp = {}
        lval = None
        rval = None
        for element in line.split('\n'):
            indent_level = element.count('\t')
            element = element.replace('\t','')
            if element:
                if ':' in element:
                    lval, rval = element.split(':')[0], element.split(':', maxsplit=1)[1]
                    temp[lval] = rval.strip()
                    # This is the last key in dmidecode -t 17's output for each object by DMI handle.
                    # Use this as the basis for when to append the temp dict object into the list.
                    if lval.strip() == 'Configured Clock Speed':
                        template[section].append(temp)
                        temp = {}
                else:
                    if not temp.get(lval):
                        temp[lval] = []
                    if type(temp[lval]) is list:
                        temp[lval].append(element)
        if section != 'Memory Device':
            template[section] = temp

    if len(template) > 0:
        return template

""" FUNCTIONS SECTION """

def parse_lspci():
    cmd   = "/usr/bin/lspci"
    flags = ["-k", "-mm", "-v"]
    output= run_cmd(cmd=cmd, flags=flags)
    # Store the scanned devices into a list.
    lspci_devices = format_to_list(output=output)
    return lspci_devices

def parse_dmidecode():
    dmi = {}
    # Dmidecode offers on most platforms between 0 and 42 DMI objects by 'type'.
    for entry in range(0, 43):
        cmd = '/usr/sbin/dmidecode'
        flags = ['--type',str(entry), '--quiet']
        result = run_cmd(cmd=cmd, flags=flags)
        # Name of the DMI type based off of its enumeration.
        section = result.split('\n',maxsplit=1)[0].strip()
        # Grab the rest of the output without the section header.
        output  = result.replace(section,'')
        if section != "":
            dmi.update(indent_to_dict(output=output, section=section))
    return dmi

def smartctl_attributes(device):
    template = {}
    attributes = []
    command  = '/usr/sbin/smartctl'
    flags    = ['--attributes', '/dev/%s' % device]
    output   = run_cmd(cmd=command, flags=flags)
    # Skip the beginning lines until the header section is found.
    ctr      = 0
    for line in output.splitlines():
        # [ID, Attribute Name, Flag, Value, Worst, Thresh, Type, Updated, When, Raw]
        if ctr > 6:
            line = line.split()
            if line:
                template['id']         = int(line[0])
                template['attribute']  = line[1]
                template['normalized'] = int(line[3])
                template['previous']   = int(line[4])
                template['current']    = int(line[9])
                template['threshold']  = int(line[5])
                template['type']       = line[6]
                template['updated']    = line[7]
                attributes.append(template)
        ctr += 1
        template               = {}
    return attributes

def smartctl_information(device):
    template = {}
    command  = '/usr/sbin/smartctl'
    flags    = ['--info', '/dev/%s' % device]
    output   = run_cmd(cmd=command, flags=flags)
    for line in output.splitlines():
        # [ID, Attribute Name, Flag, Value, Worst, Thresh, Type, Updated, When, Raw]
        if ":" in line:
            key = line.split(':')[0]
            value = line.split(':')[1]
            template[key] = value.strip()
    return template

def get_partitions(device):
    command = '/bin/lsblk'
    flags   = ['/dev/%s' % device, '--json']
    output  = json.loads(run_cmd(cmd=command, flags=flags))
    return output['blockdevices'][0]['children']

def parse_smartctl():
    devices         = []
    scanned_devices = None
    try:
        block_devices   = subprocess.check_output(['/bin/ls','/sys/block']).decode('utf-8')
        scanned_devices = [device for device in block_devices.splitlines() if 'loop' not in device and device != 'sr0']
        for device in scanned_devices:
            template = {
                'device'      : device,
                'partitions'  : get_partitions(device=device),
                'information' : smartctl_information(device=device),
                'attributes'  : smartctl_attributes(device=device),
            }
            devices.append(template)
        template = {}
    except subprocess.CalledProcessError() as e:
        print(str(e))
    finally:
        return devices

""" Grab the list of possible query options provided by this version of nvidia-smi. Note that the possible queries may change over time. """
def parse_nvidia_queries():
    filter_list = ['Default', 'Prohibited', 'Exclusive_Process']
    command = '/usr/bin/nvidia-smi'
    flags   = ['--help-query-gpu']
    queries = []
    output  = run_cmd(cmd=command, flags=flags)
    for line in output.splitlines():
        if 'List of valid properties' in line:
            continue
        if line.startswith('"') and 'means' not in line:
            query = line.strip().split(" ")[0].replace('"','')
            queries.append(query)
    return queries

def get_nvidia_count():
    command = '/usr/bin/nvidia-smi'
    flags   = ['--list-gpus']
    output  = run_cmd(cmd=command, flags=flags)
    return len(output.splitlines())

def parse_nvidia():
    queries  = parse_nvidia_queries()
    gpu_count= get_nvidia_count()
    gpu_ctr  = 0
    gpus     = []
    while gpu_ctr < gpu_count:
        command  = '/usr/bin/nvidia-smi'
        flags    = ['--format=csv,noheader','--id=%i' % gpu_ctr,'--query-gpu=%s' % (','.join(queries))]
        output   = run_cmd(cmd=command, flags=flags)
        template = {}
        ctr      = 0
        for element in output.split(','):
            key   = queries[ctr]
            value = element.strip()
            ctr += 1
            if value != "[Not Supported]":
                template[key] = value
        gpus.append(template)
        gpu_ctr += 1
    return gpus

def get_nics():
    template = {}
    devices  = []
    command  = '/sbin/ifconfig'
    flags    = ['-s']
    output   = run_cmd(cmd=command, flags=flags)
    for element in output.splitlines():
        if 'Iface' in element or element.startswith('lo'):
            continue
        else:
            template['name']     = element.split()[0]
            template['mtu']      = int(element.split()[1])
            template['received'] = {
                'succeeded' : int(element.split()[2]),
                'failed'    : int(element.split()[3]),
                'dropped'   : int(element.split()[4]),
                'overruns'  : int(element.split()[5])
            }
            template['sent'] = {
                'succeeded' : int(element.split()[6]),
                'failed'    : int(element.split()[7]),
                'dropped'   : int(element.split()[8]),
                'overruns'  : int(element.split()[9])
            }
        devices.append(template)
        template = {}
    return devices

def get_nic_info(device):
    command = '/sbin/ethtool'
    flags   = ['-i', device['name']]
    output  = run_cmd(cmd=command, flags=flags)
    for line in output.splitlines():
        key = line.split(":")[0]
        if len(line.split(":")) > 1:
            value = line.split(":")[1].strip()
            if value:
                device[key] = value
    return device

def get_ip_address(device):
    netmask_lookup_table = {
         1: '0.0.0.0',          2: '128.0.0.0',        3: '192.0.0.0',        4: '224.0.0.0',
         5: '240.0.0.0',        6: '252.0.0.0',        7: '254.0.0.0',        8: '255.0.0.0',
         9: '255.128.0.0',     10: '255.192.0.0',     11: '255.224.0.0',     12: '255.240.0.0',
        13: '255.248.0.0',     14: '255.252.0.0',     15: '255.254.0.0',     16: '255.255.0.0',
        17: '255.255.128.0',   18: '255.255.192.0',   19: '255.255.224.0',   20: '255.255.240.0',
        21: '255.255.248.0',   22: '255.255.252.0',   23: '255.255.254.0',   24: '255.255.255.0',
        25: '255.255.255.128', 26: '255.255.255.192', 27: '255.255.255.224', 28: '255.255.255.240',
        29: '255.255.255.248', 30: '255.255.255.252', 31: '255.255.255.254', 32: '255.255.255.255'
    }
    command = '/sbin/ip'
    flags   = ['address', 'show', device['name']]
    output  = run_cmd(cmd=command, flags=flags)
    for line in output.splitlines():
        if "%s:" % device['name'] in line:
            device['state'] = line.split(' ')[8]
        elif 'inet' in line:
            if not device.get('addresses'):
                device['addresses'] = []
                addr, netmask = line.strip().split(' ')[1].split('/')
                template = {'address' : addr, 'netmask': netmask_lookup_table[int(netmask)]}
                device['addresses'].append(template)
    return device

def get_network():
    devices  = get_nics()

    for device in devices:
        device.update(get_nic_info(device))
        device.update(get_ip_address(device))

    for device in devices:
        command = '/sbin/ethtool'
        flags   = ['-P', device['name']]
        output  = run_cmd(cmd=command, flags=flags)
        for line in output.splitlines():
            if 'Permanent address' in line:
                mac_address = line.split(":",maxsplit=1)[1].strip()
                if mac_address != "00:00:00:00:00:00":
                    device['mac'] = mac_address
    return devices

""" Currently only provided Debian-based support. """
def get_installed_packages(pkg_mgr='apt'):
    command = '/usr/bin/apt'
    flags   = ['--installed', 'list']
    output  = run_cmd(cmd=command, flags=flags)
    pkgs    = []
    for line in output.splitlines():
        temp = {}
        pkg  = line.split(' ')
        if len(pkg) > 1:
            temp['name']    = pkg[0].split('/')[0]
            temp['version'] = pkg[1]
            pkgs.append(temp)
    return pkgs

""" MAIN FUNCTION """

if __name__ == '__main__':

    HARDWARE = {
        'dmi'      : parse_dmidecode(),
        'lspci'    : parse_lspci(),
        'storage'  : parse_smartctl(),
        'gpu'      : parse_nvidia(),
        'network'  : get_network(),
        #'packages' : get_installed_packages()
    }

    print(json.dumps(HARDWARE))
