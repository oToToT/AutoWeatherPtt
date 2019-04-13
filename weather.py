#! /usr/bin/env python3
import requests, argparse, datetime

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

def fullStr(s):
    fullTable = "０１２３４５６７８９"
    return ''.join([fullTable[int(dig)] for dig in str(s)])

def datetime2str(t):
    return f'{t.year}年{t.month:02d}月{t.day:02d}日{t.hour:02d}時{t.minute:02d}分'

def generate_post_content(data):
    issue_time = datetime.datetime.strptime(data['datasetInfo']['issueTime'], '%Y-%m-%dT%H:%M:%S%z')
    start_time = datetime.datetime.strptime(data['location'][0]['weatherElement'][0]['time'][0]['startTime'], '%Y-%m-%dT%H:%M:%S%z')
    end_time = datetime.datetime.strptime(data['location'][0]['weatherElement'][0]['time'][0]['endTime'], '%Y-%m-%dT%H:%M:%S%z')

    content = f'''
發布時間：{datetime2str(issue_time)}
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
            max_t = weather_element['MaxT']['parameter']['parameterName'].rjust(2, '0'),
            min_t = weather_element['MinT']['parameter']['parameterName'].rjust(2, '0'),
            rain = weather_element['PoP']['parameter']['parameterName'].rjust(2, '0')
        )
    content += '\n＊備註：各縣市預報係以各縣市政府所在地附近為預報參考位置。\n'
    content += '\n---資料來源:中央氣象局---\n---  Coded By oToToT  ---'
    return content
def generate_post_title(data):
    t = datetime.datetime.strptime(data['datasetInfo']['issueTime'], '%Y-%m-%dT%H:%M:%S%z')
    return f'[預報] {t.year}/{t.month}/{t.day} {"早上" if t.hour < 12 else "中午" if t.hour == 12 else "晚上"}'

def main():
    arg = process_argument()

    username = arg.username
    password = arg.password
    board = arg.board
    host = arg.host

    data = CWB_data('F-C0032-001', arg.apikey)
    content = generate_post_content(data)
    title = generate_post_title(data)

#    session = login(host, username, board)
#    post(session, board, title, content)
#    logout(session)

if __name__ == '__main__':
    main()
