#! /usr/bin/env python3
import requests, argparse, datetime, paramiko, time

def process_argument():
    parser = argparse.ArgumentParser()
    parser.add_argument('-u','--username', type=str, help='登入帳號', required=True)
    parser.add_argument('-p','--password', type=str, help='登入密碼', required=True)
    parser.add_argument('-k','--apikey', type=str, help='中央氣象局授權碼',required=True)
    parser.add_argument('-b','--board', type=str, help='發文看板',required=True)
    parser.add_argument('-c','--host', type=str, help='登入主機', default='ptt2.cc')
    return parser.parse_args()

def CWB_data(dataid, apikey):
    return requests.get(f'https://opendata.cwb.gov.tw/fileapi/v1/opendataapi/{dataid}?Authorization={apikey}&format=JSON').json()['cwbopendata']['dataset']

def datetime2str(t):
    return f'{t.year}年{t.month:02d}月{t.day:02d}日{t.hour:02d}時{t.minute:02d}分'

def tcolor(s):
    t = int(s)
    if t <= 10:
        return "\x15[1;34m"+s+"\x15[m"
    elif t <= 15:
        return "\x15[36m"+s+"\x15[m"
    elif t <= 20:
        return "\x15[1;36m"+s+"\x15[m"
    elif t <= 25:
        return "\x15[1;33m"+s+"\x15[m"
    elif t <= 30:
        return "\x15[34m"+s+"\x15[m"
    elif t <= 35:
        return "\x15[31m"+s+"\x15[m"
    else:
        return "\x15[1;31m"+s+"\x15[m"
def rcolor(s):
    r = int(s)
    if r == 0:
        return s
    elif r <= 20:
        return "\x15[1m"+s+"\x15[m"
    elif r <= 40:
        return "\x15[1;36m"+s+"\x15[m"
    elif r <= 60:
        return "\x15[36m"+s+"\x15[m"
    elif r <= 80:
        return "\x15[1;34m"+s+"\x15[m"
    else:
        return "\x15[34m"+s+"\x15[m"

def generate_post_content(data):
    issue_time = datetime.datetime.strptime(data['datasetInfo']['issueTime'], '%Y-%m-%dT%H:%M:%S%z')
    start_time = datetime.datetime.strptime(data['location'][0]['weatherElement'][0]['time'][0]['startTime'], '%Y-%m-%dT%H:%M:%S%z')
    end_time = datetime.datetime.strptime(data['location'][0]['weatherElement'][0]['time'][0]['endTime'], '%Y-%m-%dT%H:%M:%S%z')

    content = f'''發布時間：{datetime2str(issue_time)}
有效時間：{datetime2str(start_time)}起至{datetime2str(end_time)}

預報分區　　　　　天　　　　氣　　　　　雨率　氣溫(攝氏)

'''
    for pos in data['location']:

        weather_element = {}
        for sub in pos['weatherElement']:
            weather_element[sub['elementName']]=sub['time'][0]

        content += '＊{name}　{descript}{rain}％　　{min_t} - {max_t}\n'.format(
            name = pos['locationName'],
            descript = weather_element['Wx']['parameter']['parameterName'].ljust(15, '　'),
            max_t = tcolor(weather_element['MaxT']['parameter']['parameterName'].rjust(2, ' ')),
            min_t = tcolor(weather_element['MinT']['parameter']['parameterName'].rjust(2, ' ')),
            rain = rcolor(weather_element['PoP']['parameter']['parameterName'].rjust(2, ' '))
        )
    content += '\n＊備註：各縣市預報係以各縣市政府所在地附近為預報參考位置。\n'
    content += '\n---資料來源:中央氣象局---\n---  Coded By oToToT  ---'
    content = content.replace('\n', '\r\n')
    return content
def generate_post_title(data):
    t = datetime.datetime.strptime(data['datasetInfo']['issueTime'], '%Y-%m-%dT%H:%M:%S%z')
    return f'[預報] {t.year}/{t.month:02d}/{t.day:02d} {"早上" if t.hour < 12 else "中午" if t.hour == 12 else "晚上"}'

height, width = 24, 80
def recv_data(session):
    while not session.channel.recv_ready():
        time.sleep(0.01)
    data = ''
    while session.channel.recv_ready():
        data += session.channel.recv(height*width).decode('big5','ignore')
    return data
def send_data(session,s):
    while not session.channel.send_ready():
        time.sleep(0.01)
    session.channel.send(s.encode('big5'))

def login(host, username, password, kickOther=False):
    session = paramiko.SSHClient()
    session.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    session.connect(host, username='bbs', password='')
    session.channel = session.invoke_shell(width = width, height = height)

    frame = recv_data(session)
    send_data(session,username+'\r\n')
    frame = recv_data(session)
    send_data(session,password+'\r\n')
    frame = recv_data(session)
    frame = recv_data(session)

    if '您想刪除其他重複登入的連線嗎' in frame:
        send_data(session,'y\r\n' if kickOther else 'n\r\n')
        frame = recv_data(session)
    if '更新與同步線上使用者及好友名單' in frame:
        frame = recv_data(session)
    if '請按任意鍵繼續' in frame:
        send_data(session,'a')
        frame = recv_data(session)
    if '刪除以上錯誤嘗試的記錄' in frame:
        send_data(session,'y\r\n')
        frame = recv_data(session)
    if '您有一篇文章尚未完成' in frame:
        send_data(session,'q\r\n')
        frame = recv_data(session)
    return session

def post(session, board, title, content):
    send_data(session, 's')
    frame = recv_data(session)
    send_data(session, board+'\r\n')
    frame = recv_data(session)
    if '請按任意鍵繼續' in frame:
        send_data(session, 'a')
        frame = recv_data(session)
    send_data(session, '\x10')
    send_data(session, '\r\n')
    send_data(session, title+'\r\n')
    for c in content:
        send_data(session, c)
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

    username = arg.username
    password = arg.password
    board = arg.board
    host = arg.host

    data = CWB_data('F-C0032-001', arg.apikey)
    content = generate_post_content(data)
    title = generate_post_title(data)

    session = login(host, username, password)
    post(session, board, title, content)

if __name__ == '__main__':
    main()
