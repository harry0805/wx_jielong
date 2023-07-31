import time
import pyautogui
import mouse
import keyboard
import re
import pyperclip

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
    # Add names to message
    for i, name in enumerate(names):
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

names = ['Harry', 'Yao', 'Swan', 'Tina']

# Check clipboard already has message
current_clipboard = pyperclip.paste()
if check_message(current_clipboard):
    current_clipboard = '!' + current_clipboard
    pyperclip.copy(current_clipboard)
    print('Modified current clipboard because it already matches')
# Wait for message to be copied
print('Starting detection...')
while True:
    msg = pyperclip.paste()
    if check_message(msg):
        break
    time.sleep(0.1)
# Add names and Send message
msg = pyperclip.paste()
new_msg = join_message(msg, names)
pyperclip.copy(new_msg)
if not click_message_box():
    quit()
paste_and_send()
print('Message sent!')