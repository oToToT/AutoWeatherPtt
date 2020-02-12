#! /usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import time
import json
from datetime import datetime
from getpass import getpass
import paramiko
import requests


TERM_HEIGHT = 24
TERM_WIDTH = 80
TERM_ENCODING = 'big5'


def process_argument():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='cmd', metavar='cmd', required=True)

    from_config = subparsers.add_parser('config', help='使用設定檔匯入設定')
    from_config.add_argument('config_file', type=argparse.FileType('r'), help='設定檔位置')

    from_args = subparsers.add_parser('exec', help='從命令列輸入設定')
    from_args.add_argument('-u', '--username', type=str, help='登入帳號', default=None)
    from_args.add_argument('-p', '--password', type=str, help='登入密碼', default=None)
    from_args.add_argument('-k', '--apikey', type=str, help='中央氣象局授權碼', default=None)
    from_args.add_argument('-b', '--board', type=str, help='發文看板', default=None)
    from_args.add_argument('-c', '--host', type=str, help='登入主機', default='ptt2.cc')
    return parser.parse_args()


def CWB_data(dataid, apikey):
    return requests.get(
        f'https://opendata.cwb.gov.tw/fileapi/v1/opendataapi/{dataid}\
        ?Authorization={apikey}&format=JSON'
    ).json()['cwbopendata']['dataset']


def datetime2str(dt):
    return f'{dt.year}年{dt.month:02d}月{dt.day:02d}日{dt.hour:02d}時{dt.minute:02d}分'


def tcolor(s):
    tem = int(s)
    if tem <= 10:
        return "\x15[1;34m"+s+"\x15[m"
    if tem <= 15:
        return "\x15[36m"+s+"\x15[m"
    if tem <= 20:
        return "\x15[1;36m"+s+"\x15[m"
    if tem <= 25:
        return "\x15[1;33m"+s+"\x15[m"
    if tem <= 30:
        return "\x15[1;35m"+s+"\x15[m"
    if tem <= 35:
        return "\x15[31m"+s+"\x15[m"
    return "\x15[1;31m"+s+"\x15[m"


def rcolor(s):
    rain = int(s)
    if rain == 0:
        return s
    if rain <= 20:
        return "\x15[1m"+s+"\x15[m"
    if rain <= 40:
        return "\x15[1;36m"+s+"\x15[m"
    if rain <= 60:
        return "\x15[36m"+s+"\x15[m"
    if rain <= 80:
        return "\x15[1;34m"+s+"\x15[m"
    return "\x15[34m"+s+"\x15[m"


def generate_post_content(data):
    issue_time = datetime.strptime(
        data['datasetInfo']['issueTime'],
        '%Y-%m-%dT%H:%M:%S%z'
    )
    start_time = datetime.strptime(
        data['location'][0]['weatherElement'][0]['time'][0]['startTime'],
        '%Y-%m-%dT%H:%M:%S%z'
    )
    end_time = datetime.strptime(
        data['location'][0]['weatherElement'][0]['time'][0]['endTime'],
        '%Y-%m-%dT%H:%M:%S%z'
    )

    content = f'''發布時間：{datetime2str(issue_time)}
有效時間：{datetime2str(start_time)}起至{datetime2str(end_time)}

預報分區　　　　　天　　　　氣　　　　　雨率　氣溫(攝氏)

'''
    for pos in data['location']:

        weather_element = {}
        for sub in pos['weatherElement']:
            weather_element[sub['elementName']] = sub['time'][0]

        content += '＊{name}　{descript}{rain}％　　{min_t} - {max_t}\n'.format(
            name=pos['locationName'],
            descript=weather_element['Wx']['parameter']['parameterName'].ljust(15, '　'),
            max_t=tcolor(weather_element['MaxT']['parameter']['parameterName'].rjust(2, ' ')),
            min_t=tcolor(weather_element['MinT']['parameter']['parameterName'].rjust(2, ' ')),
            rain=rcolor(weather_element['PoP']['parameter']['parameterName'].rjust(3, ' '))
        )
    content += '\n＊備註：各縣市預報係以各縣市政府所在地附近為預報參考位置。\n'
    content += '\n---資料來源:中央氣象局---\n---  Coded By oToToT  ---'
    content = content.replace('\n', '\r\n')
    return content


def generate_post_title(data):
    ts = datetime.strptime(data['datasetInfo']['issueTime'], '%Y-%m-%dT%H:%M:%S%z')
    stage = ''
    if ts.hour < 12:
        stage = '早上'
    elif ts.hour == 12:
        stage = '中午'
    else:
        stage = '晚上'
    return f'[預報] {ts.year}/{ts.month:02d}/{ts.day:02d} {stage}'


def recv_data(session):
    while not session.channel.recv_ready():
        time.sleep(0.01)
    data = ''
    while session.channel.recv_ready():
        data += session.channel.recv(TERM_HEIGHT * TERM_WIDTH).decode(TERM_ENCODING, 'ignore')
    return data


def send_data(session, s):
    while not session.channel.send_ready():
        time.sleep(0.01)
    session.channel.send(s.encode(TERM_ENCODING))


def login(host, username, password, kickOther=False):
    session = paramiko.SSHClient()
    session.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    session.connect(host, username='bbs', password='')
    session.channel = session.invoke_shell(height=TERM_HEIGHT, width=TERM_WIDTH)

    frame = recv_data(session)
    send_data(session, username+'\r\n')
    frame = recv_data(session)
    send_data(session, password+'\r\n')
    frame = recv_data(session)
    frame = recv_data(session)

    if '您想刪除其他重複登入的連線嗎' in frame:
        send_data(session, 'y\r\n' if kickOther else 'n\r\n')
        frame = recv_data(session)
    if '更新與同步線上使用者及好友名單' in frame:
        frame = recv_data(session)
    if '請按任意鍵繼續' in frame:
        send_data(session, 'a')
        frame = recv_data(session)
    if '刪除以上錯誤嘗試的記錄' in frame:
        send_data(session, 'y\r\n')
        frame = recv_data(session)
    if '您有一篇文章尚未完成' in frame:
        send_data(session, 'q\r\n')
        frame = recv_data(session)
    if '您保存信件數目' in frame and '超出上限' in frame:
        send_data(session, 'a')
        frame = recv_data(session)
        send_data(session, 'q')
        frame = recv_data(session)
    return session


def post(session, board, title, content):
    send_data(session, 's')
    frame = recv_data(session)
    send_data(session, board+'\r\n')
    frame = recv_data(session)
    if '動畫播放中' in frame:
        send_data(session, 'q')
        frame = recv_data(session)
    if '請按任意鍵繼續' in frame:
        send_data(session, 'q')
        frame = recv_data(session)
    send_data(session, '\x10')
    send_data(session, '\r\n')
    send_data(session, title+'\r\n')
    for char in content:
        send_data(session, char)
    frame = recv_data(session)
    send_data(session, '\x18')
    frame = recv_data(session)
    send_data(session, 's\r\n')
    frame = recv_data(session)
    if '請按任意鍵繼續' in frame:
        send_data(session, 'a')
        frame = recv_data(session)
    # ugly way
    time.sleep(1)


def main():
    arg = process_argument()

    if arg.cmd == 'config':
        config = json.load(arg.config_file)
        arg.config_file.close()
        username = config.get('username', None)
        password = config.get('password', None)
        board = config.get('board', None)
        apikey = config.get('apikey', None)
        host = config.get('host', 'ptt2.cc')
    elif arg.cmd == 'exec':
        username = arg.username
        password = arg.password
        board = arg.board
        apikey = arg.apikey
        host = arg.host

    if not username:
        username = input('登入帳號: ')
    if not password:
        password = getpass('登入密碼: ')
    if not board:
        board = input('發文看板: ')
    if not apikey:
        apikey = getpass('中央氣象局授權碼: ')

    data = CWB_data('F-C0032-001', apikey)
    content = generate_post_content(data)
    title = generate_post_title(data)

    session = login(host, username, password)
    post(session, board, title, content)


if __name__ == '__main__':
    main()
