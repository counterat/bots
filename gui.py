import pyautogui
import time
import pyautogui
import time
from main import get_members_of_chat,get_chats, get_chats_2


time.sleep(3)

x,y = (pyautogui.position())
print(x,y)
def subscr_to_chats(chats_links):
    for chat_link in chats_links:
        print(chat_link)
        chat_link = chat_link.replace('@', '')
        pyautogui.doubleClick(154,65)
        pyautogui.press('backspace')
        pyautogui.typewrite(chat_link)
        pyautogui.moveTo(367,161, duration=1)
        pyautogui.click()
        time.sleep(1)
        pyautogui.moveTo(939,1000, duration=1)
        pyautogui.click()

def get_inline_user_info():
    with pyautogui.hold('alt'):
        pyautogui.press(['tab'])
        pyautogui.press(['tab'])


    members = get_members_of_chat(-1001778892228)
    for member in members:
        pyautogui.click(825, 1001)
        pyautogui.typewrite(f'@usinfobot {member}')
        pyautogui.moveTo(883, 888, duration=1.5)
        pyautogui.click()
        pyautogui.click()
        pyautogui.click()
        pyautogui.moveTo(1545, 1005)
        pyautogui.dragTo(700,1005)

def paste_the_chat_links_to_the_bot(chats=[]):
    for chat in chats:
        pyautogui.moveTo(856, 998)
        pyautogui.click()
        with pyautogui.hold('ctrl'):
            pyautogui.press('a')
        pyautogui.press('backspace')
        pyautogui.typewrite(f'@usinfobot @{chat.split("https://t.me/")[1]}')
        pyautogui.moveTo(943,798, duration =2.5, tween=pyautogui.easeOutQuad)
        pyautogui.click()
        time.sleep(3)
        #pyautogui.click(1838,881)
#paste_the_chat_links_to_the_bot()