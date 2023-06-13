from datetime import datetime
import json
import shutil
import subprocess
from typing import List, Union

def _internal_get_units() -> List[str]:
    results        = []
    systemctl_path = shutil.which('systemctl')    
    help_options   = [systemctl_path, 'list-units','--type=help']
    output         = subprocess.check_output(help_options).decode('utf-8').split('\n')
    for line in output:
        line = line.strip()
        if 'Available' in line or line == '':
            continue
        results.append(line.strip())
    return results

""" Provide back a list of unit types and available options to toggle with systemctl. """
def _internal_get_unit_state_options() -> Union[dict,None]:
    results          = []
    systemctl_path   = shutil.which('systemctl')
    command          = [systemctl_path,"list-units","--type=service", "--state=help", "--no-legend"]
    # Step 1: Get back a list of available unit types.
    unit_types       = _internal_get_units()
    # Step 2: Get back the list of available options. Parse into a dictionary for each type.
    template         = {}
    template['unit'] = None
    for unit in unit_types:
        template[unit] = None
    available_options= None
    try:
        unit_type = None
        unit_state= None
        available_options = subprocess.check_output(command).decode('utf-8')
        for line in available_options.split('\n'):
            if 'substates' in line or 'Available unit' in line:
                unit_type = line.split(' ')[1]
            elif line == "" or line == "\n":
                continue
            else:
                if template[unit_type] is None:
                    template[unit_type] = []
                template[unit_type].append(line.strip())
        return template
    except subprocess.CalledProcessError:
        print("Ran into an issue")
    
""" Internal function. Attempt to query systemctl. Return list of valid types if incorrect type is passed in."""
def _internal_systemctl_get_units(unit_type: str) -> List[str]:
    results = []
    # Get the path to systemctl if in a non-standard location.
    systemctl_path = shutil.which('systemctl')
    try:
        command = [systemctl_path,'list-units',f'--type={unit_type}', '--no-legend','--all']
        output  = subprocess.check_output(command).decode('utf-8').split('\n')
        for line in output:
            # Remove non-alphanumeric characters.
            for character in line:
                if not character.isalpha():
                    line.replace(character,'')
            line = line.split()
            template = {
                'name'        : line[0],
                'loaded'      : line[1].lower() == 'loaded',
                'active'      : line[2].lower() == 'active',
                'state'       : line[3],
                'description' : " ".join(line[4:])
            }
            results.append(template)
    except subprocess.CalledProcessError:
        results = _internal_get_units()
    finally:
        return results
""" Internal function. Get the available properties that can be queried or set by systemd. Return None if unit is not found."""
def _internal_get_properties(unit_name) -> Union[dict, None]:
    systemctl_path = shutil.which('systemctl')
    MAGIC_NUM_FOR_INF = 18446744073709551615
    command = [systemctl_path,'show',unit_name]
    try:
        output = subprocess.check_output(command).decode('utf-8').split('\n')
        template = {}
        for line in output:
            key = line.split('=')[0]
            if key == 'LoadError':
                return None
            if key == '':
                continue
            val = "".join(line.split('=')[1:])
            if str.isdigit(val):
                val = int(val)
                if val == MAGIC_NUM_FOR_INF:
                    val = "infinity"
            template[key] = val
        return template
    except subprocess.CalledProcessError:
        return None
""" 
    Internal function. Call journalctl to get the logs of the specified unit. 
    Defaults to logs since 1 hour ago and last 50 logs.
    Return None if unit not found or no logs were found.
"""
def _internal_journalctl_get_messages(unit_name: str, since="1 hour ago", limit=10) -> List[dict]:
    if since == None:
        since = "1 hour ago"
    if limit == None or limit <= 0:
        limit = 10
    journalctl_path = shutil.which('journalctl')
    command = [journalctl_path,f'--unit={unit_name}','--output=json',f"--since={since}", '--reverse']
    try:
        output   = subprocess.check_output(command).decode('utf-8')
        messages = []
        for message in output.split('\n'):
            template = {}
            if message == '':
                continue
            msg = json.loads(message)
            if '__REALTIME_TIMESTAMP' in msg.keys() and 'MESSAGE' in msg.keys():
                # Convert the timestamp in microseconds to seconds.
                timestamp = int(msg.get('__REALTIME_TIMESTAMP')) // 1000000
                template['timestamp'] = datetime.fromtimestamp(timestamp)
                template['message']   = msg.get('MESSAGE')
            if len(template.keys()) > 0:
                messages.append(template)
        return messages[:limit]
    except subprocess.CalledProcessError:
        return None
    
if __name__ == '__main__':
    options = _internal_get_unit_state_options()
    print(options)