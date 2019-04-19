import http.client
import json
import csv
from collections import defaultdict
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


#### Sport Radar API calls produced a persisten 'JSONEncode' error when a for loop was used, or more than one year was requested, both within a single script.

# for a in range(2008, 2019):
#     year = str(a)
#     conn = http.client.HTTPSConnection("api.sportradar.us")
#
#     conn.request("GET", 'http://api.sportradar.us/nfl/official/trial/v5/en/games/{}/REG/schedule.json?api_key=pcme8fe9qe7ucbhtrtqveexa'.format(year))
#
#     res = conn.getresponse()
#     data = res.read()
#     clean = data.decode("utf-8")
#
#
#     json_resp = json.loads(clean)
#     nfl_api_dict[year] = json_resp
#
# #
# def get_api_games(a):
#     year = str(a)
#     conn = http.client.HTTPSConnection("api.sportradar.us")
#
#     conn.request("GET", 'http://api.sportradar.us/nfl/official/trial/v5/en/games/{}/REG/schedule.json?api_key=pcme8fe9qe7ucbhtrtqveexa'.format(year))
#
#     res = conn.getresponse()
#     data = res.read()
#     clean = data.decode("utf-8").replace('\0', '')
#
#     return json.loads(clean)
####

# Retrieve a CSV file that contains NFL team names and their corresponding team abbreviation. Found on from Github.
abbrevs_csv_name = 'nfl_teams.csv'
names_to_abbrevs = {}
abbrevs_to_names = {}
with open(abbrevs_csv_name, 'r') as abbrevs_data:
    reader = csv.DictReader(abbrevs_data)
    for a in reader:
        names_to_abbrevs[a['Name'].split()[-1]] = a['Abbreviation']
        abbrevs_to_names[a['Abbreviation']] = a['Name'].split()[-1]

# Reading the 'spreadspoke_scores.csv' file, containing game results and game odds, into a Python list named 'spread_data'.
nfl_csv_name = 'spreadspoke_scores.csv'
spread_data = []
with open(nfl_csv_name, 'r') as csv_data:
    reader = csv.DictReader(csv_data)
    for a in reader:
        spread_data.append(a)

# Opening and reading the 'sportradar.json' file, due to the persistent API issue, into a Python object named 'sr_games_dict'.
# The 'sportradar.json' file contains the weather conditions for each NFL game from the seasons 2014-2018.
with open('sportradar.json') as api_data:
    sr_games_dict = json.load(api_data)

# Filtering out games in sr_games_dict that did not contain a game weather report, and adding games with a weather report to a dictionary with unique keys for each game.
game_data = {}
for a in sr_games_dict:
    for b in sr_games_dict[a]['weeks']:
        for c in b['games']:
            if 'weather' in c.keys():
                game_id = c['home']['name'].split()[-1] + ' ' + c['away']['name'].split()[-1] + ' ' + c['scheduled'].split('T')[0]
                game_data[game_id] = {}
                game_data[game_id]['condition'] = str(c['weather']).split('Temp')[0] # Regular expression was too complicated to apply here even though ideal, the split() function works just as well.


# Filtering out games later than 2014, playoff games, games that haven't finished yet, games missing a predetermined team favorite, and games that did not have corresponding game data from the API/JSON.
for a in spread_data:
    date = a['schedule_date'].split('/')
    if int(date[2]) >= 2014 and a['schedule_playoff'] != 'TRUE' and a['score_home'] != '' and a['score_away'] != '':
        if a['team_favorite_id'] in names_to_abbrevs.values():
            winner = ''
            loser = ''
            if int(a['score_home']) > int(a['score_away']):
                winner = names_to_abbrevs[a['team_home'].split()[-1]]
                loser = names_to_abbrevs[a['team_away'].split()[-1]]
            else:
                winner = names_to_abbrevs[a['team_away'].split()[-1]]
                loser = names_to_abbrevs[a['team_home'].split()[-1]]
            format_date = date[2] + '-' + date[0] + '-' + date[1]
            game_id = a['team_home'].split()[-1] + ' ' + a['team_away'].split()[-1] + ' ' + format_date
            if game_id in game_data:
                game_data[game_id]['favored'] = a['team_favorite_id']
                game_data[game_id]['winner'] = winner
                game_data[game_id]['loser'] = loser

# Find all unique weather conditions.
conditions = [a['condition'] for a in game_data.values()]
unique_conditions = set(conditions)

# *** My own categorization of weather types to determine team performance in each. ***
# All other types are considered 'fair'.

# The 'moderate' category contains game conditipns with cloud cover, haziness/fogginess, severe cold/heat/wind, and a possibility of precipitation.
moderate_types = ['Cloudy and humid ', 'Overcast ', 'Sunny, highs to upper 80\'s ', 'Cloudy and Windy ', 'Cloudy, chance of rain increasing up to 75% during game. ',
 'Cloudy ', 'CLOUDY ', 'cloudy ', 'Coudy ', 'Cloundy ' 'Foggy ', '10% Chance of rain ', 'Mostly Cloudy ', 'Cloudy, 50% change of rain ', 'Cold ',
 '30% Chance of Rain ', 'Cloudy, Humid, Chance of Rain ', 'Mostly Coudy ', 'Sunny, Windy ', 'Cloudly ', 'Cloudy skies ', 'Cloudy, chance of rain ', 'Mostly Cloudy, Chilly ',
 'Cloudy and cold ', 'Hazy ', 'Cloudy, fog started developing in 2nd quarter ', 'Mostly cloudy ', 'Rain Chance 40% ', 'Cloudy, 80% chance of rain ']

# The 'poor' category contains game conditions with mostly precipitation, and some other less than ideal conditions.
poor_types = ['Cloudy, light snow accumulating 1-3\" ', 'Flurries ', 'Cloudy, flurries ', 'Occasional rain ending in the 10PM hour ',
'Cloudy with periods of rain, thunder possible. Winds shifting to WNW, 10-20 mph. ', 'Rain ', 'Showers ', 'Snow Showers, 3 to 5 inches expected. ',
'Cloudy, Rain ', 'Scattered Showers ', 'Rain likely, temps in low 40\s. ', 'Heavy lake effect snow ', 'Rainy and cool ', 'Cloudy with rain ',
'Cloudy and rainy ', 'Snow showers ', 'Light Showers ', 'Light Rain ', 'Rain showers ', 'Rainy ', 'Snow ', 'Cloudy with light snow. ']

# The 'covered' category contains game conditions with a covered, controlled playing environment, like a closed dome.
# "Weather" is not a factor here, but it is considered a game condition
covered_types = ['', 'N/A (Indoors) ', 'N/A Indoor ', 'Indoors ', 'Indoor ', 'N/A ', 'Controlled ', 'Climate Control ', 'Controlled Climate ', 'Controlled  Climate ']

# The 'fair' category contains game conditions with ideal weather, like sun, clear skies.

# Setting up dictionary to accumulate team wins, losses, and favor in weather types.
condition_results = defaultdict(dict)
condition_results['moderate_results'] = defaultdict(list)
condition_results['poor_results'] = defaultdict(list)
condition_results['covered_results'] = defaultdict(list)
condition_results['fair_results'] = defaultdict(list)

#Accumulating all winning, losing, and favored teams from each game, and organizing them based on game condition.
for a in game_data:
    if 'winner' in game_data[a] and 'favored' in game_data[a] and 'loser' in game_data[a]: # Filter out games that did not have corresponding IDs, due to discrepencies in the 2 original data sources.
        if game_data[a]['condition'] in moderate_types:
            condition_results['moderate_results']['winners'].append(game_data[a]['winner'])
            condition_results['moderate_results']['losers'].append(game_data[a]['loser'])
            condition_results['moderate_results']['favored_to_win'].append(game_data[a]['favored'])
        if game_data[a]['condition'] in poor_types:
            condition_results['poor_results']['winners'].append(game_data[a]['winner'])
            condition_results['poor_results']['losers'].append(game_data[a]['loser'])
            condition_results['poor_results']['favored_to_win'].append(game_data[a]['favored'])
        if game_data[a]['condition'] in covered_types:
            condition_results['covered_results']['winners'].append(game_data[a]['winner'])
            condition_results['covered_results']['losers'].append(game_data[a]['loser'])
            condition_results['covered_results']['favored_to_win'].append(game_data[a]['favored'])
        else:
            condition_results['fair_results']['winners'].append(game_data[a]['winner'])
            condition_results['fair_results']['losers'].append(game_data[a]['loser'])
            condition_results['fair_results']['favored_to_win'].append(game_data[a]['favored'])

# Accumulating dictionaries to calculate all total team counts for each weather condition.
moderate_team_stats = {'winners': defaultdict(dict), 'losers': defaultdict(dict), 'favored_to_win': defaultdict(dict), 'games_played': defaultdict(dict)}
poor_team_stats = {'winners': defaultdict(dict), 'losers': defaultdict(dict), 'favored_to_win': defaultdict(dict), 'games_played': defaultdict(dict)}
covered_team_stats = {'winners': defaultdict(dict), 'losers': defaultdict(dict), 'favored_to_win': defaultdict(dict), 'games_played': defaultdict(dict)}
fair_team_stats = {'winners': defaultdict(dict), 'losers': defaultdict(dict), 'favored_to_win': defaultdict(dict), 'games_played': defaultdict(dict)}

# Accumulate team abbreviations prior to condition wins accumulation to make mapping 'games_played' to teams easier.
for a in abbrevs_to_names:
    moderate_team_stats['games_played'][a] = 0
    poor_team_stats['games_played'][a] = 0
    covered_team_stats['games_played'][a] = 0
    fair_team_stats['games_played'][a] = 0

# Accumulating dictionaries to calculate all total team counts for each weater condition. Count number of occurences team abbreviaton occurs within each condition and result count for wins, losses, and favoreds.
for a in condition_results['moderate_results']:
    if a == 'winners':
        for b in condition_results['moderate_results'][a]:
            moderate_team_stats[a][b] = condition_results['moderate_results'][a].count(b)
            moderate_team_stats['games_played'][b] += 1
    if a == 'losers':
        for b in condition_results['moderate_results'][a]:
            moderate_team_stats[a][b] = condition_results['moderate_results'][a].count(b)
            moderate_team_stats['games_played'][b] += 1
    else:
        for b in condition_results['moderate_results'][a]:
            moderate_team_stats[a][b] = condition_results['moderate_results'][a].count(b)


for a in condition_results['poor_results']:
    if a == 'winners':
        for b in condition_results['poor_results'][a]:
            poor_team_stats[a][b] = condition_results['poor_results'][a].count(b)
            poor_team_stats['games_played'][b] += 1
    if a == 'losers':
        for b in condition_results['poor_results'][a]:
            poor_team_stats[a][b] = condition_results['poor_results'][a].count(b)
            poor_team_stats['games_played'][b] += 1
    else:
        for b in condition_results['poor_results'][a]:
            poor_team_stats[a][b] = condition_results['poor_results'][a].count(b)


for a in condition_results['covered_results']:
    if a == 'winners':
        for b in condition_results['covered_results'][a]:
            covered_team_stats[a][b] = condition_results['covered_results'][a].count(b)
            covered_team_stats['games_played'][b] += 1
    if a == 'losers':
        for b in condition_results['covered_results'][a]:
            covered_team_stats[a][b] = condition_results['covered_results'][a].count(b)
            covered_team_stats['games_played'][b] += 1
    else:
        for b in condition_results['covered_results'][a]:
            covered_team_stats[a][b] = condition_results['covered_results'][a].count(b)


for a in condition_results['fair_results']:
    if a == 'winners':
        for b in condition_results['fair_results'][a]:
            fair_team_stats[a][b] = condition_results['fair_results'][a].count(b)
            fair_team_stats['games_played'][b] += 1
    if a == 'losers':
        for b in condition_results['fair_results'][a]:
            fair_team_stats[a][b] = condition_results['fair_results'][a].count(b)
            fair_team_stats['games_played'][b] += 1
    else:
        for b in condition_results['fair_results'][a]:
            fair_team_stats[a][b] = condition_results['fair_results'][a].count(b)


# Prepping visualization data, creating win, loss, and favored percentages in each condition.

moderate_team_percs = defaultdict(dict)
poor_team_percs = defaultdict(dict)
covered_team_percs = defaultdict(dict)
fair_team_percs = defaultdict(dict)

# Filter out teams that have no wins, losses, or favoreds, in stats dictionaries.
for a in abbrevs_to_names:
    moderate_team_percs[a]['win_perc'] = 0
    poor_team_percs[a]['win_perc'] = 0
    covered_team_percs[a]['win_perc'] = 0
    fair_team_percs[a]['win_perc'] = 0
    moderate_team_percs[a]['loss_perc'] = 0
    poor_team_percs[a]['loss_perc'] = 0
    covered_team_percs[a]['loss_perc'] = 0
    fair_team_percs[a]['loss_perc'] = 0
    moderate_team_percs[a]['favored_perc'] = 0
    poor_team_percs[a]['favored_perc'] = 0
    covered_team_percs[a]['favored_perc'] = 0
    fair_team_percs[a]['favored_perc'] = 0


# Prepping visualization data, creating win, loss, and favored percentages in each condition.
for a in moderate_team_stats:
    for b in moderate_team_stats[a]:
        if a == 'winners':
            moderate_team_percs[b]['win_perc'] = (moderate_team_stats[a][b] / moderate_team_stats['games_played'][b]) * 100
        if a == 'losers':
            moderate_team_percs[b]['loss_perc'] = (moderate_team_stats[a][b] / moderate_team_stats['games_played'][b]) * 100
        if a == 'favored_to_win':
            moderate_team_percs[b]['favored_perc'] = (moderate_team_stats[a][b] / moderate_team_stats['games_played'][b]) * 100

for a in poor_team_stats:
    for b in poor_team_stats[a]:
        if a == 'winners':
            poor_team_percs[b]['win_perc'] = (poor_team_stats[a][b] / poor_team_stats['games_played'][b]) * 100
        if a == 'losers':
            poor_team_percs[b]['loss_perc'] = (poor_team_stats[a][b] / poor_team_stats['games_played'][b]) * 100
        if a == 'favored_to_win':
            poor_team_percs[b]['favored_perc'] = (poor_team_stats[a][b] / poor_team_stats['games_played'][b]) * 100

for a in covered_team_stats:
    for b in covered_team_stats[a]:
        if a == 'winners':
            covered_team_percs[b]['win_perc'] = (covered_team_stats[a][b] / covered_team_stats['games_played'][b]) * 100
        if a == 'losers':
            covered_team_percs[b]['loss_perc'] = (covered_team_stats[a][b] / covered_team_stats['games_played'][b]) * 100
        if a == 'favored_to_win':
            covered_team_percs[b]['favored_perc'] = (covered_team_stats[a][b] / covered_team_stats['games_played'][b]) * 100

for a in fair_team_stats:
    for b in fair_team_stats[a]:
        if a == 'winners':
            fair_team_percs[b]['win_perc'] = (fair_team_stats[a][b] / fair_team_stats['games_played'][b]) * 100
        if a == 'losers':
            fair_team_percs[b]['loss_perc'] = (fair_team_stats[a][b] / fair_team_stats['games_played'][b]) * 100
        if a == 'favored_to_win':
            fair_team_percs[b]['favored_perc'] = (fair_team_stats[a][b] / fair_team_stats['games_played'][b]) * 100

# Calculate top 5 Winningest and Losingest Teams for each weather condition.
top_5_winningest_teams_moderate = sorted(moderate_team_percs.items(), key = lambda x: x[1]['win_perc'], reverse = True)[:5]
top_5_losingest_teams_moderate = sorted(moderate_team_percs.items(), key = lambda x: x[1]['loss_perc'], reverse = True)[:5]
#
top_5_winningest_teams_poor = sorted(poor_team_percs.items(), key = lambda x: x[1]['win_perc'], reverse = True)[:5]
top_5_losingest_teams_poor = sorted(poor_team_percs.items(), key = lambda x: x[1]['loss_perc'], reverse = True)[:5]
#
top_5_winningest_teams_covered = sorted(covered_team_percs.items(), key = lambda x: x[1]['win_perc'], reverse = True)[:5]
top_5_losingest_teams_covered = sorted(covered_team_percs.items(), key = lambda x: x[1]['loss_perc'], reverse = True)[:5]
#
top_5_winningest_teams_fair = sorted(fair_team_percs.items(), key = lambda x: x[1]['win_perc'], reverse = True)[:5]
top_5_losingest_teams_fair = sorted(fair_team_percs.items(), key = lambda x: x[1]['loss_perc'], reverse = True)[:5]

# Creates all visualization
def create_bar_vis(top_5, title, loss_or_win_perc):

    
    N = 5
    ind = np.arange(N)
    width = -0.3

    percentages = []
    team_names= []
    favored_to_win_perc = []
    for a in top_5:
        percentages.append(a[1]['{}_perc'.format(loss_or_win_perc.lower())])
        favored_to_win_perc.append(a[1]['favored_perc'])
        team_names.append(abbrevs_to_names[a[0]])

    per_block = ax.bar(ind, percentages, width, align = 'edge', color='r')

    fav_block = ax.bar(ind + .3, favored_to_win_perc, width, align = 'edge', color='b')

    ax.set_title(title)
    ax.set_ylabel('Percentage')
    ax.set_xlabel('Team Name')
    ax.set_xticks(ind)
    ax.set_xticklabels(team_names)

    ax.legend((per_block[0], fav_block[0]), ('Game {} %'.format(loss_or_win_perc), 'Favored To Win %'))

    def label_bars(block):
        for a in block:
            h = a.get_height()
            ax.text(a.get_x() + a.get_width()/2, h*1.01, str(h)[:4] + '%', fontsize = 7, ha = 'center') #S-Overflow
    label_bars(per_block)
    label_bars(fav_block)

    plt.show()

# Calls all visualization
create_bar_vis(top_5_winningest_teams_fair, 'Top 5 Winningest Teams in \'Fair\' Conditions (2014-2018)', 'Win')
create_bar_vis(top_5_losingest_teams_fair, 'Top 5 Losingest Teams in \'Fair\' Conditions (2014-2018)', 'Loss')
create_bar_vis(top_5_winningest_teams_moderate, 'Top 5 Winningest Teams in \'Moderate\' Conditions (2014-2018)', 'Win')
create_bar_vis(top_5_losingest_teams_moderate, 'Top 5 Losingest Teams in \'Moderate\' Conditions (2014-2018)', 'Loss')
create_bar_vis(top_5_winningest_teams_poor, 'Top 5 Winningest Teams in \'Poor\' Conditions (2014-2018)', 'Win')
create_bar_vis(top_5_losingest_teams_poor, 'Top 5 Losingest Teams in \'Poor\' Conditions (2014-2018)', 'Loss')
create_bar_vis(top_5_winningest_teams_covered, 'Top 5 Winningest Teams in \'Covered\' Conditions (2014-2018)', 'Win')
create_bar_vis(top_5_losingest_teams_covered, 'Top 5 Losingest Teams in \'Covered\' Conditions (2014-2018)', 'Loss')
