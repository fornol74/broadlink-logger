import sys
import csv
import time
from base64 import b64encode
try:
    import broadlink
except ImportError:
    print(
        "Error: requirement failed!\n"
        "This script require python-broadlink library: "
        "https://github.com/mjg59/python-broadlink\n"
        "you can install it with: \n"
        "pip3 install --user -e "
        "'git+https://github.com/mjg59/python-broadlink.git#egg=broadlink'"
    )
    sys.exit()

"""
Script for recording of the IR codes to CSV file
"""

FIELD_NAMES = ('Button Name', 'Button Code')

MAIN_MENU = {
    '0': 'Quit',
    '1': 'Create new appliance',
}

APPLIANCE_MENU = {
    '0': 'Quit',
    '1': 'Learn new button',
    '2': 'Return to main menu',
}

def terminate():
    print("\nBye.")
    sys.exit()

def show_menu(items, title=""):
    choice = None

    if title:
        print(f'\n*** {title} ***\n')

    print('What would you like to do:')
    print('--------------------------')
    for item in items:
        print(f'| {item}: {items[item]}')
    print('--------------------------\n')

    while choice not in items.keys():
        if choice:
            print(
                f'Invalid answer "{choice}"\nExpected: {list(items.keys())}'
            )
        choice = input('#: ')
    return choice

def request_appliance_name():
    appliance_name = None
    while not appliance_name:
        if appliance_name is not None and not appliance_name:
            print(f'Invalid appliance name: "{appliance_name}"')
        appliance_name = input('Enter appliance name: ')
    return appliance_name

def process_new_appliance(appliance_name, device):
    max_tries = 20  # wiat logged command for 20 seconds
    file_name = appliance_name.replace(' ', '_').lower()
    with open(f'{file_name}.csv', 'w+', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=FIELD_NAMES)
        writer.writeheader()

        while True:
            choice = show_menu(
                APPLIANCE_MENU, title=f"Appliance: {appliance_name}"
            )

            if choice in ("0", "q"):
                terminate()
            if choice == "2":
                break

            if choice == "1":
                current_try = 1
                prev_code = None
                device.enter_learning()
                print('Press target button...')
                
                while current_try <= max_tries:
                    code = None
                    code = device.check_data()
                    if code and code != prev_code:
                        print('Found new code!')
                        button = input('Enter Button Name: ')
                        writer.writerow(
                            {
                                'Button Name': str(button.title()),
                                'Button Code': b64encode(code).decode()
                            }
                        )
                        print('Code successfully stored\n')
                        prev_code = code
                        break
                    current_try += 1
                    time.sleep(1)
                print('Sorry, can not find any codes, try again\n')

if __name__ == '__main__':

    if len(sys.argv) == 1 or (
        len(sys.argv) == 2 and sys.argv[1] in ("-h", "--help")
    ):
        print(f'\nUsage: {sys.argv[0]} <device_ip_address> <timeout>')
        print(f'  <device_ip_address> is required')
        print(f'  <timeout> is optional argument (5 seconds by default)')
        print(f'Usage example: {sys.argv[0]} 192.168.0.42')
        sys.exit()
    
    host = sys.argv[1]
    timeout = sys.argv[2] if len(sys.argv) > 2 else 5

    print('Scanning network for available devices...')
    devices = broadlink.discover(timeout=int(timeout))  

    if not devices:
        print('No devices found in network, aborting')
        print('* hint: try to ping your device before start this script')
        sys.exit()
    else:
        print(f'Found {len(devices)} device(s)')

    device = None
    for dev in devices:
        if dev.host[0] == host:
            print(f'Connecting to: {host}...')
            device = dev
            device.auth()
            print('connected.')
    
    if not device:
        print(f'Device with address {host} was not found, aborting')
        sys.exit()

    try:
        while True:
            choice = show_menu(MAIN_MENU)
            if choice in ("0", "q"):
                break;

            if choice == "1":
                appliance_name = request_appliance_name()
                process_new_appliance(appliance_name, device)

    except KeyboardInterrupt:
        pass
    terminate()
