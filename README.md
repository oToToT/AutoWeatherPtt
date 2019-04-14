# AutoWeatherPtt

Post daily weather information on pttbbs or any other bbs.

# Install

Install requirement from requirements.txt

    $ pip install -r requirements.txt

Run weather.py with Python(>=3.7)

    ./weather.py [-h] -u USERNAME -p PASSWORD -k APIKEY -b BOARD [-c HOST]

## Argument Information

Argument Name | Alias  | Description
--------------|--------|-------------------------
--username    | -u     | username of bbs to login
--password    | -p     | password of bbs to login
--apikey      | -k     | apikey of cwb opendata
--board       | -b     | board to post
--host        | -c     | bbs address
