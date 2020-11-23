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
my_region = config.region
watched_users = config.userlist
known_games = []

def list_players_from_game(g):
    fin = []
    for p in g['participants']:
        user = watcher.summoner.by_name(my_region, p['summonerName'])
        # Lane metric is a bit strange
        # p['lane'] = watcher.match.matchlist_by_account(my_region, user['accountId'])['matches'][0]['lane']
        league = watcher.league.by_summoner(my_region, p['summonerId'])
        p['Ranked Solo 5x5'] = "N/A"
        p['Ranked Flex SR'] = "N/A"
        p['Flex Win Ratio'] = "N/A"
        p['Solo Win Ratio'] = "N/A"

        if not league:
            fin.append(p)
            continue

        for i in league:
            if 'RANKED_SOLO_5x5' in i.values():
                p['Ranked Solo 5x5'] = i['tier'] + " " + i['rank']
                p['Solo Win Ratio'] = str(round(int(i['wins']) / float(i['losses']), 2))
            if 'RANKED_FLEX_SR' in i.values():
                p['Ranked Flex SR'] = i['tier'] + " " + i['rank']
                p['Flex Win Ratio'] = str(round(int(i['wins']) / float(i['losses']), 2))
        fin.append(p)
    return fin

def get_win_chance(p):
    team1_win_ratio_average = 0
    team2_win_ratio_average = 0

    for i in p[:half]:
        if i['Solo Win Ratio'] == 'N/A':
            team1_win_ratio_average = team1_win_ratio_average + .75
            continue
        team1_win_ratio_average = team1_win_ratio_average + float(i['Solo Win Ratio'])
    team1_win_ratio_average = team1_win_ratio_average / 5

    for i in p[half:]:
        if i['Solo Win Ratio'] == 'N/A':
            team2_win_ratio_average = team2_win_ratio_average + .75
            continue
        team2_win_ratio_average = team2_win_ratio_average + float(i['Solo Win Ratio'])
    team2_win_ratio_average = team2_win_ratio_average / 5
    return 0 if team1_win_ratio_average > team2_win_ratio_average else 1

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
                half = len(players)//2
                winner = get_win_chance(players)
                df = pd.DataFrame(players)
                df.drop(['teamId', 'spell1Id', 'spell2Id', 'championId', 'profileIconId', 'bot', 'summonerId', 'gameCustomizationObjects', 'perks'], axis=1, inplace=True)
                team1 = tabulate.tabulate(df[:5], headers='keys', tablefmt='fancy_grid', showindex=False)
                team2 = tabulate.tabulate(df[5:], headers='keys', tablefmt='fancy_grid', showindex=False)
                webhook = DiscordWebhook(url=config.webhook_url, content="I found a game!")
                response = webhook.execute()
                webhook = DiscordWebhook(url=config.webhook_url, content="Team 1:\n" + "```" + team1 + "```\n\n")
                response = webhook.execute()
                webhook = DiscordWebhook(url=config.webhook_url, content="Team 2:\n" + "```" + team2 + "```\n\n")
                response = webhook.execute()
                webhook = DiscordWebhook(url=config.webhook_url, content="Based on ranks/win ratios, I think team 1 will win!" if winner == 0 else "Based on ranks/win ratios, I think team 2 will win!")
                response = webhook.execute()
                print(team1)
                print(team2)
            else:
                print("Game is known, skipping...")
                continue
        except Exception as e:
            if '404' not in str(e):
                print(e)

    print("Sleeping for 30 seconds")
    time.sleep(30)
