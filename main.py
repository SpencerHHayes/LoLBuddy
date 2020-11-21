from riotwatcher import LolWatcher, ApiError
import pandas as pd
import tabulate
import time
import config
import sys
from discord_webhook import DiscordWebhook

# global variables
api_key = config.api_key
watcher = LolWatcher(api_key)
my_region = 'na1'
watched_users = config.userlist
known_games = []

def list_players_from_game(g):
    fin = []
    for p in g['participants']:
        user = watcher.summoner.by_name(my_region, p['summonerName'])
        # Lane metric is a bit strange
        # p['lane'] = watcher.match.matchlist_by_account(my_region, user['accountId'])['matches'][0]['lane']
        league = watcher.league.by_summoner(my_region, p['summonerId'])
        if not league:
            p['Ranked Solo 5x5'] = "N/A"
            p['Ranked Flex SR'] = "N/A"
            p['Flex Win Ratio'] = "N/A"
            p['Solo Win Ratio'] = "N/A"
            fin.append(p)
            continue
        for i in league:
            if 'RANKED_SOLO_5x5' in i.values():
                p['Ranked Solo 5x5'] = i['tier'] + " " + i['rank']
                p['Solo Win Ratio'] = str(round(int(i['wins']) / int(i['losses']), 2))
            else:
                p['Ranked Solo 5x5'] = "N/A"
                p['Solo Win Ratio'] = "N/A"
            if 'RANKED_FLEX_SR' in i.values():
                p['Ranked Flex SR'] = i['tier'] + " " + i['rank']
                p['Flex Win Ratio'] = str(round(int(i['wins']) / int(i['losses']), 2))
            else:
                p['Ranked Flex SR'] = "N/A"
                p['Flex Win Ratio'] = "N/A"
        fin.append(p)
    return fin

while True:

    for p in watched_users:
        print(p)
        try:
            user = watcher.summoner.by_name(my_region, p)
            game = watcher.spectator.by_summoner(my_region, user['id'])
            # If we're here, the user is in a game
            if game['gameId'] not in known_games:
                known_games.append(game["gameId"])
                players = list_players_from_game(game)
                df = pd.DataFrame(players)
                df.drop(['teamId', 'spell1Id', 'spell2Id', 'championId', 'profileIconId', 'bot', 'summonerId', 'gameCustomizationObjects', 'perks'], axis=1, inplace=True)
                table = tabulate.tabulate(df, headers='keys', tablefmt='psql', showindex=False)
                webhook = DiscordWebhook(url=config.webhook_url, content="```" + table + "```")
                response = webhook.execute()
                print(table)
            else:
                print("Game is known, skipping...")
                continue
        except Exception as e:
            if '404' not in str(e):
                print(e)
            continue
    print("Sleeping for 30 seconds")
    time.sleep(30)
