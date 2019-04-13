# AutoWeatherPtt

Post daily weather information on ptt or any other bbs.

## HOWTO

Download python3 an use pip to install requests.

Apply an Authorization key of http://opendata.cwb.gov.tw/ and edit the authKey variable in weather.py

edit user, password and board variables in weather.py

Also you can edit host variable if needed

After doing all these preparation, you can just run it or use crontab and the --check=false paramter to post it timely

p.s if you don't want it bottom your post you can add --buttom=false paramter

