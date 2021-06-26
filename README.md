# AutoWeatherPtt

Post daily weather information on pttbbs or any other bbs.

# Install

Install requirement from requirements.txt
```
$ pip install -r requirements.txt
```

Run weather.py with Python(>=3.7) and load config from command line
```
./weather.py exec [-h] -u USERNAME -p PASSWORD -k APIKEY -b BOARD [-c HOST] [-o ORIGIN]
```

Run weather.py with Python(>=3.7) and load config from config.json
```
./weather.py config [-h] filepath
```

## Argument Information

Argument Name | Alias  | Description
--------------|--------|-------------------------
--username    | -u     | username of bbs to login
--password    | -p     | password of bbs to login
--apikey      | -k     | apikey of cwb opendata
--board       | -b     | board to post
--host        | -c     | websocket endpoint
--origin      | -o     | original website url

## Config Spec

A JSON file as below is required

```json
{
    "username": "oToToT",
    "password": "******",
    "board": "Weather",
    "apikey": "CWB-********-****-****-****-************",
    "host": "wss://ws.ptt2.cc/bbs",
    "origin": "https://term.ptt2.cc"
}
```
