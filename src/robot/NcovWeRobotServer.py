import json
import time
import itchat
import os
import sys

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
BASE_PATH = os.path.split(rootPath)[0]
sys.path.append(BASE_PATH)
from itchat.content import *
from src.robot.NcovWeRobotFunc import *
from src.util.constant import INFO_TAIL, SHOULD_UPDATE, UPDATE_CITY, UPDATE_NCOV_INFO, SHORT_TIME_SPLIT, INFO_TAIL_ALL, \
    UPDATE_NCOV_INFO_ALL, SEND_SPLIT
from src.util.redis_config import connect_redis
import jieba
import threading
from src.spider.SpiderServer import start_tx_spider

@itchat.msg_register([TEXT, MAP, CARD, NOTE, SHARING])
def text_reply(msg):
    if msg['FromUserName'] == itchat.originInstance.storageClass.userName and msg['ToUserName'] != 'filehelper':
        return
    if check_whether_register(msg.text):
        succ, failed = user_subscribe(conn, msg.user.UserName, msg.text, jieba)
        succ_text = ''
        if len(succ) > 0:
            succ_text = '成功订阅{}的疫情信息!'.format(",".join(succ))
        failed_text = ''
        if len(failed) > 0:
            failed_text = '订阅{}失败，该地区名称不正确或暂无疫情信息。'.format("，".join(failed))
        # msg.user.send('%s: %s' % (succ_text, failed_text))
        ls.logging.info('用户%s: %s %s' % (msg.user.UserName, succ_text, failed_text))
        itchat.send('%s %s' % (succ_text, failed_text), toUserName=msg.user.UserName)
        if len(succ) > 0:
            time.sleep(SEND_SPLIT)
            itchat.send(get_ncvo_info_with_city(conn, succ), toUserName=msg.user.UserName)
            area = succ[0]
            if area != '全国' and area != '中国':
                time.sleep(SEND_SPLIT)
                itchat.send(INFO_TAIL.format(area, area), toUserName=msg.user.UserName)
            else:
                time.sleep(SEND_SPLIT)
                itchat.send(INFO_TAIL_ALL, toUserName=msg.user.UserName)
    elif check_whether_unregist(msg.text):
        succ, failed = user_unsubscribe_multi(conn, msg.user.UserName, msg.text, jieba)
        succ_text = ''
        if len(succ) > 0:
            succ_text = '成功取消{}的疫情信息订阅'.format("，".join(succ))
        failed_text = ''
        if len(failed) > 0:
            failed_text = '取消{}的疫情信息订阅失败，您好像没有订阅该地区信息或者地区名称错误'.format("，".join(failed))
        ls.logging.info('用户%s: %s %s' % (msg.user.UserName, succ_text, failed_text))
        itchat.send('%s %s' % (succ_text, failed_text), toUserName=msg.user.UserName)


def init_jieba():
    all_area = set(conn.smembers(ALL_AREA_KEY))
    if len(all_area) == 0:
        ls.logging.error("尚无地区信息")

    for words in all_area:
        jieba.add_word(words)
    return jieba


def do_ncov_update(conn, itchat, debug=True):
    ls.logging.info("thread do ncov update info start success-----")
    try:
        while True:
            should_update = conn.get(SHOULD_UPDATE)
            if should_update == '1':
                update_city = conn.get(UPDATE_CITY)
                conn.set(SHOULD_UPDATE, 0)
                if not update_city:
                    ls.logging.warning("-No update city info")
                    continue
                update_city = json.loads(update_city)
                for city in update_city:
                    if city['city'] == '全国' or city['city'] == '中国':
                        push_info = UPDATE_NCOV_INFO_ALL.format(city['city'], city['n_confirm'], city['n_suspect'],
                                                                city['confirm'], city['suspect'], city['dead'],
                                                                city['heal'])
                    else:
                        push_info = UPDATE_NCOV_INFO.format(city['city'], city['n_confirm'], city['confirm'],
                                                            city['dead'], city['heal'])
                    subscribe_user = conn.smembers(city['city'])

                    ls.logging.info("begin to send info...")
                    for user in subscribe_user:
                        try:
                            ls.logging.info("info:{},user: {}".format(push_info[:20], user))
                            itchat.send(push_info, toUserName=user)
                            # 发送太快容易出事
                            time.sleep(SEND_SPLIT)
                        except BaseException as e:
                            ls.logging.error("send failed，{}".format(user))
                            ls.logging.exception(e)
            if debug:
                break
            # 暂停几分钟
            time.sleep(SHORT_TIME_SPLIT)
    except BaseException as e:
        ls.logging.error("Error in check ncov update-----")
        ls.logging.exception(e)


def start_server():
    # 在不同的终端上，需要调整CMDQR的值
    itchat.auto_login(True, enableCmdQR=2)
    ls.logging.info("begin to start tx spider")
    p1 = threading.Thread(target=start_tx_spider)
    p1.start()
    ls.logging.info("begin to start ncov update")
    p2 = threading.Thread(target=do_ncov_update, args=[conn, itchat, False])
    p2.start()
    itchat.send('Hello, 自动机器人又上线啦', toUserName='filehelper')
    itchat.run(True)

conn = connect_redis()
jieba = init_jieba()

if __name__ == '__main__':
    start_server()
