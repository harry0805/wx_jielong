import time
import pyautogui
import mouse as original_mouse
import keyboard as original_keyboard
import re
import pyperclip
from PIL import ImageChops
from pynput.mouse import Listener as mouseListener
from pynput.keyboard import Listener as keyboardListener, KeyCode
import os
import json

# Default settings
config = {
    # The program will only send your message after this many people is already in the list
    'only_join_after': 3,
    # The time interval between each new message check
    'ss_interval': 0.3,
    # Time to pause after user has interrupted the program
    'user_input_pause_time': 2,
    # The key for exiting the program
    'exit_key': '`',
    # If True The program will not send the names that are already present in the message
    'no_duplicate_names': True,
    # The timeframe for the program to detect the message area before it times out
    'detection_timeout': 10,
}

# Load settings from jielong_config.json
if os.path.exists('jielong_config.json'):
    with open('jielong_config.json', 'r') as f:
        config.update(json.load(f))


# Get names form file
if not os.path.exists('names.txt'):
    print('names.txt not found. Please create a names.txt file in the same directory with this program.')
    quit()
with open('names.txt', 'r') as f:
    names = f.read().split('\n')
if len(names) == 0:
    print('names.txt is empty. Please add names to names.txt')
    quit()
str_names = ', '.join(names)
print(f'Names Retrieved! This program will add {str_names} to the list.')

exit_program = False
program_inputs = 0
last_input = 0
def on_input(*args, **kwargs):
    # If this program made an input, ignore it
    global program_inputs
    if program_inputs > 0:
        program_inputs -= 1
        return
    global last_input
    last_input = time.time()
def on_key_press(key):
    if key == KeyCode.from_char(config['exit_key']):
        print('Terminated by user.')
        global exit_program
        exit_program = True
        return
    on_input()
mouseListener(on_scroll=on_input, on_click=on_input, on_move=on_input).start()
keyboardListener(on_press=on_key_press).start()

# Change mouse and keyboard library to count mouse inputs
def count_inputs_decorator(func, inputs=1):
    def wrapper(*args, **kwargs):
        global program_inputs
        program_inputs += inputs
        return func(*args, **kwargs)
    return wrapper

mouse = original_mouse
keyboard = original_keyboard
mouse.click = count_inputs_decorator(original_mouse.click, 2)
keyboard.press_and_release = count_inputs_decorator(original_keyboard.press_and_release)
keyboard.press = count_inputs_decorator(original_keyboard.press)


def get_last_input_time_passed():
    return time.time() - last_input

def get_msg_area(timeout=30, interval=0.5):
    timer = time.time()
    while timer + timeout > time.time():
        chat_icons = pyautogui.locateOnScreen('wx.png')
        if chat_icons is None:
            time.sleep(interval)
            continue
        return chat_icons.left + 65, chat_icons.top - 40
    return None

def get_msg_background(msg_area):
    return msg_area[0] - 75, msg_area[1]

def focus_and_go_bottom(msg_area):
    mouse.move(*get_msg_background(msg_area))
    mouse.click()
    time.sleep(0.6)
    mouse.click()
    keyboard.press_and_release('home')
    keyboard.press_and_release('end')

def copy_new_message(msg_area):
    mouse.move(*msg_area)
    mouse.click('right')
    mouse.move(0, -5, absolute=False)
    mouse.click()
    keyboard.press('ctrl')
    keyboard.press_and_release('c')
    keyboard.release('ctrl')
    mouse.move(*get_msg_background(msg_area))
    mouse.click()

def check_message(msg):
    pattern = re.compile(r'(?s)#接龙\n.*1\..+')
    if not pattern.match(msg):
        return False
    return True

def join_message(msg, names):
    # Obtain current number
    msg_list = msg.split('\n')
    current_number = msg_list[-1].split('.')[0]
    if not current_number.isdigit():
        print('Failed to obtain current number')
        return False
    current_number = int(current_number)
    if current_number < config['only_join_after']:
        print('Not enough people in the list')
        return False

    names_to_add = names
    if config['no_duplicate_names']:
        # Get all current names in the message
        current_names = [line.split('. ')[1] for line in msg_list[-1:-current_number + 1:-1]]
        # Remove names that are already in the message
        names_to_add = [name for name in names if name not in current_names]
        if len(names_to_add) == 0:
            print('All the names are already in the message')
            return 'end'
        if len(names_to_add) < len(names):
            print(f'{len(names) - len(names_to_add)} names are already in the message, only {len(names_to_add)} names will be added this time')

    # Add names to message
    for i, name in enumerate(names_to_add):
        msg_list.append(f'{current_number + i + 1}. {name}')
    return '\n'.join(msg_list)

def click_message_box():
    # Find the chat box and click
    chat_box = pyautogui.locateOnScreen('wx.png')
    if chat_box is None:
        print('Failed to find chat box')
        return False
    current_location = mouse.get_position()
    mouse.move(chat_box.left + 10, chat_box.top + 45)
    mouse.click()
    mouse.move(*current_location)
    return True

def paste_and_send():
    keyboard.press_and_release('ctrl + a')
    keyboard.press_and_release('ctrl + v')
    keyboard.press_and_release('enter')

def wait_until_no_inputs():
    last_intput_time_passed = get_last_input_time_passed()
    # Repeatedly sleep for the remaining time because last_input may be updated
    while last_intput_time_passed < config['user_input_pause_time']:
        time.sleep(config['user_input_pause_time'] - last_intput_time_passed)
        last_intput_time_passed = get_last_input_time_passed()

def initialize():
    # Get message area
    msg_area = get_msg_area(config['detection_timeout'], config['detection_interval'])
    if msg_area is None:
        print('Failed to get message area, timeout')
        quit()
    print('Message area found')
    # Wait for user to stop interacting with the computer
    if get_last_input_time_passed() < config['user_input_pause_time']:
        print('Now stop interacting with the computer until this program has finished.')
        wait_until_no_inputs()
    # Focus on message area and move to the bottom of chat
    focus_and_go_bottom(msg_area)
    return msg_area

# Check clipboard already has a jielong message
current_clipboard = pyperclip.paste()
if check_message(current_clipboard):
    current_clipboard = '!' + current_clipboard
    pyperclip.copy(current_clipboard)
    print('Modified current clipboard because it already matches')

# Initialize
print('Detecting message area, please move wechat window to the front...')
msg_area = initialize()

# Detect new message
print('Starting detection for new messages...')
ss_region = (msg_area[0]-8, msg_area[1]-10, 150, 20)
previous_ss = pyautogui.screenshot(region=ss_region)
last_input = 0
while True:
    if exit_program:
        quit()
    # Detect if user has inputted in a time period
    last_intput_time_passed = get_last_input_time_passed()
    if last_intput_time_passed < config['user_input_pause_time']:
        print('User interrupted, program paused... ')
        wait_until_no_inputs()
        print('Program resumed, re-detecting message area...')
        msg_area = initialize()
        previous_ss = pyautogui.screenshot(region=ss_region)
        continue
    current_ss = pyautogui.screenshot(region=ss_region)
    difference = ImageChops.difference(previous_ss, current_ss).getbbox()
    if difference is not None:
        # New message detected
        print('New message detected!')
        copy_new_message(msg_area)
        # Wait for clipboard to update
        time.sleep(0.1)
        if check_message(msg := pyperclip.paste()):
            new_msg = join_message(msg, names)
            # No new names to add
            if new_msg == 'end':
                quit()
            if new_msg is not False:
                # Add names and Send message
                pyperclip.copy(new_msg)
                if not click_message_box():
                    print('Failed to find message box somehow...')
                    continue
                paste_and_send()
                print('Message sent!')
                quit()
        else:
            print('Message does not match, continue detecting...')

    previous_ss = current_ss
    time.sleep(config['ss_interval'])