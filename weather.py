#! /usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import json
from datetime import datetime
from getpass import getpass
import requests
from SimplePTTClient import PTTClient

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
    from_args.add_argument('-c', '--host', type=str, help='登入主機', default='wss://ws.ptt2.cc/bbs')
    from_args.add_argument('-o', '--origin', type=str, help='登入來源', default='https://term.ptt2.cc')
    return parser.parse_args()


def CWB_data(dataid, apikey):
    return requests.get(
        f'https://opendata.cwa.gov.tw/fileapi/v1/opendataapi/{dataid}\
        ?Authorization={apikey}&format=JSON'
    ).json()['cwaopendata']['dataset']


def datetime2str(dt):
    return f'{dt.year}年{dt.month:02d}月{dt.day:02d}日{dt.hour:02d}時{dt.minute:02d}分'


def tcolor(s):
    tem = int(s)
    if tem <= 10:
        return f"\x15[1;34m{s}\x15[m"
    if tem <= 15:
        return f"\x15[36m{s}\x15[m"
    if tem <= 20:
        return f"\x15[1;36m{s}\x15[m"
    if tem <= 25:
        return f"\x15[1;33m{s}\x15[m"
    if tem <= 30:
        return f"\x15[1;35m{s}\x15[m"
    if tem <= 35:
        return f"\x15[31m{s}\x15[m"
    return f"\x15[1;31m{s}\x15[m"


def rcolor(s):
    rain = int(s)
    if rain == 0:
        return s
    if rain <= 20:
        return f"\x15[1m{s}\x15[m"
    if rain <= 40:
        return f"\x15[1;36m{s}\x15[m"
    if rain <= 60:
        return f"\x15[36m{s}\x15[m"
    if rain <= 80:
        return f"\x15[1;34m{s}\x15[m"
    return f"\x15[34m{s}\x15[m"


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
    content += '''
＊備註：各縣市預報係以各縣市政府所在地附近為預報參考位置。

---資料來源:中央氣象局---
---  Coded By oToToT  ---'''
    content = content.replace('\n', '\r\n')
    return content


def generate_post_title(data):
    tstamp = datetime.strptime(data['datasetInfo']['issueTime'],
                               '%Y-%m-%dT%H:%M:%S%z')
    stage = ''
    if tstamp.hour < 12:
        stage = '早上'
    elif tstamp.hour == 12:
        stage = '中午'
    else:
        stage = '晚上'
    return f'[預報] {tstamp.year}/{tstamp.month:02d}/{tstamp.day:02d} {stage}'


def main():
    arg = process_argument()

    if arg.cmd == 'config':
        config = json.load(arg.config_file)
        arg.config_file.close()
        username = config.get('username', None)
        password = config.get('password', None)
        board = config.get('board', None)
        apikey = config.get('apikey', None)
        host = config.get('host', 'wss://ws.ptt2.cc/bbs')
        origin = config.get('origin', 'https://term.ptt2.cc')
    elif arg.cmd == 'exec':
        username = arg.username
        password = arg.password
        board = arg.board
        apikey = arg.apikey
        host = arg.host
        origin = arg.origin

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

    client = PTTClient(host, origin)
    if not client.login(username, password):
        print("Login Failed!")
        return
    client.post(board, title, content)


if __name__ == '__main__':
    main()
