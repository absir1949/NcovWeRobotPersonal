import itchat
from itchat.content import *

@itchat.msg_register([TEXT, MAP, CARD, NOTE, SHARING])
def text_reply(msg):
    msg.user.send('%s: %s' % (msg.type, msg.text))

def start_server():
    itchat.auto_login(True)
    itchat.send('Hello, login success', toUserName='hfx0119')
    itchat.run(True)

if __name__ == '__main__':
    start_server()

