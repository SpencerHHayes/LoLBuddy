# LoLBuddy
A Discord webhook integration to give you helpful stats/links when you are loading into a game.

## Requirements
You must specify the following in config.py:
- `api_key` set to your Riot API Developer key.
- `userlist` set to a list of summoner names you would like the bot to watch.
- `webhook_url` set to your discord webhook url.
- `region` set to the LoL region the summoners in question are based.

## Running
Example:
`python -u main.py > log` to log output. 
