import re
import jieba
from src.util.constant import ALL_AREA_KEY, AREA_TAIL
from src.util.log import LogSupport

ls = LogSupport()
def check_whether_register(text):
    return re.match('^订阅.+', text) != None

def user_subscribe(conn, user, area, jieba):
    """
    接收用户订阅
    :param conn: redis 连接
    :param user: 用户名
    :param area: 发送订阅的文字，如订阅湖北省
    :return:
    """
    all_area = set(conn.smembers(ALL_AREA_KEY))
    # 去掉订阅两字
    area = area.replace("订阅", '')
    area_list = jieba.cut(area)
    succ_subscribe = []
    failed_subscribe = []
    tails = ['省', '市', '区', '县','州','自治区', '自治州', '']

    for ar in area_list:
        ar = re.subn(AREA_TAIL, '', ar)[0]
        flag = False
        for tail in tails:
            if ar + tail in all_area:
                # 使该地区的键值唯一，以腾讯新闻中的名称为准，比如湖北省和湖北都使用湖北，而涪陵区和涪陵都使用涪陵区
                conn.rpush(ar + tail, user)
                succ_subscribe.append(ar + tail)
                flag =True
                break
        if not flag:
            failed_subscribe.append(ar)

    return succ_subscribe, failed_subscribe