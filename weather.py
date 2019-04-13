#! /usr/bin/env python3
import requests, argparse, datetime, string

def process_argument():
    parser = argparse.ArgumentParser()
    parser.add_argument('-u','--username', type=str, help='登入帳號', required=True)
    parser.add_argument('-p','--password', type=str, help='登入密碼', required=True)
    parser.add_argument('-k','--apikey', type=str, help='中央氣象局授權碼',required=True)
    parser.add_argument('-b','--board', type=str, help='發文看板',required=True)
    parser.add_argument('-c','--host', type=str, help='登入主機', default='ptt2.cc')
    return parser.parse_args()

def CWB_data(dataid, apikey):
    return requests.get('https://opendata.cwb.gov.tw/fileapi/v1/opendataapi/%s?Authorization=%s&format=JSON'%(dataid, apikey)).json()['cwbopendata']['dataset']

def fullStr(s):
    fullTable = "０１２３４５６７８９"
    return ''.join([fullTable[int(dig)] for dig in str(s)])

def fillw(s, width, pend, prefix=True):
    ret = str(s)
    if len(ret) < width:
        ret = pend*(width-len(ret)) + ret if prefix else ret + pend*(width-len(ret))
    return ret

def datetime2str(time):
    ret = string.Template('$year年$month月$day日$hour時$minute分')
    arg = {
        'year': time.year,
        'month': fillw(time.month,2,'0'),
        'day': fillw(time.day,2,'0'),
        'hour': fillw(time.hour,2,'0'),
        'minute': fillw(time.minute,2,'0')
    }
    return ret.substitute(arg)

def generate_post(data):
    issue_time = datetime.datetime.strptime(data['datasetInfo']['issueTime'], '%Y-%m-%dT%H:%M:%S%z')
    start_time = datetime.datetime.strptime(data['location'][0]['weatherElement'][0]['time'][0]['startTime'], '%Y-%m-%dT%H:%M:%S%z')
    end_time = datetime.datetime.strptime(data['location'][0]['weatherElement'][0]['time'][0]['endTime'], '%Y-%m-%dT%H:%M:%S%z')

    content = string.Template('''
發布時間：$issue_time_str
有效時間：$start_time_str起至$end_time_str

預報分區　　　　　天　　　　氣　　　　　雨率　氣溫(攝氏)

''')
    argument = {
        'issue_time_str': datetime2str(issue_time),
        'start_time_str': datetime2str(start_time),
        'end_time_str': datetime2str(end_time)
    }
    content = content.safe_substitute(argument)
    for pos in data['location']:
        weather_element = {}
        for sub in pos['weatherElement']:
            weather_element[sub['elementName']]=sub['time'][0]
        content += string.Template('＊$name　$descript${rain}％　　$min_t - $max_t\n').safe_substitute(
            name = pos['locationName'],
            descript = fillw(weather_element['Wx']['parameter']['parameterName'], 15, '　', False),
            max_t = fillw(weather_element['MaxT']['parameter']['parameterName'], 2, '0'),
            min_t = fillw(weather_element['MinT']['parameter']['parameterName'], 2, '0'),
            rain = fillw(weather_element['PoP']['parameter']['parameterName'], 2, '0')
        )
    content += '\n＊備註：各縣市預報係以各縣市政府所在地附近為預報參考位置。\n'
    content += '\n---資料來源:中央氣象局---\n---  Coded By oToToT  ---'
    return content

def main():
    arg = process_argument()

    username = arg.username
    password = arg.password
    board = arg.board
    host = arg.host

    data = CWB_data('F-C0032-001', arg.apikey)
    content = generate_post(data)
    print(content)

if __name__ == '__main__':
    main()
