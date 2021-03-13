import os
import sys
import re

# We need to import log files from the parent directory.
from os.path import dirname, abspath, join
base_dir = dirname(dirname(abspath(__file__)))
log_path = os.path.join(base_dir, 'logs')
file_list = os.listdir(log_path)

# Modify this list with whatever bosses you want to look at.
bosses = ['articuno', 'zapdos', 'moltres', 'mewtwo', 'raikou', 'entei',
          'suicune', 'lugia', 'ho-oh', 'latias', 'latios', 'kyogre', 'groudon',
          'rayquaza', 'uxie', 'mesprit', 'azelf', 'dialga', 'palkia', 'heatran',
          'giratina-altered', 'cresselia', 'tornadus', 'thundurus', 'reshiram', 'zekrom',
          'landorus', 'kyurem', 'xerneas', 'yveltal', 'zygarde-50', 'tapu-koko', 'tapu-lele',
          'tapu-bulu', 'tapu-fini', 'solgaleo', 'lunala', 'necrozma', 'nihilego', 'xurkitree',
          'buzzwole', 'pheromosa', 'celesteela', 'kartana', 'guzzlord', 'stakataka',
          'blacephalon'
          ]
global_losses = 0
global_wins = 0
global_shinies = 0
global_legends = 0

for boss in bosses:
    total_losses = 0
    total_wins = 0
    total_shinies = 0
    shiny_names = []
    total_legends = 0

    # Iterate over all relevant log files because a new file is created every
    # time the program is restarted.
    for fn in file_list:
        # Note that early versions capitalize the boss name whereas others do
        # not. Therefore convert all the text to lower case.
         if boss.lower() in fn.lower() and ('.txt' in fn or '.log' in fn):
            with open(os.path.join(log_path, fn), newline='\n', encoding='utf-8') as log_file:
                num_losses = 0
                num_wins = 0
                num_shinies = 0
                legend_caught = 0
                for row in log_file.readlines():
                    # The following lines are logged once at the end of a run.
                    if 'You lose' in row:
                        num_losses += 1
                    if 'Congratulations' in row:
                        num_wins += 1
                    if 'Shiny found' in row:
                        num_shinies += 1
                    if 'will be kept' in row:
                        shiny_names.append(row.split(' will be kept')[0].split('Shiny ')[1])
                    if (f'{boss} will be kept') in row:
                        legend_caught += 1
                        
                total_losses += num_losses
                total_wins += num_wins
                total_shinies += num_shinies
                total_legends += legend_caught

    total_runs = total_losses + total_wins
    win_percentage = 0 if total_runs == 0 else total_wins / total_runs * 100

    print(f'\nSummary for {boss}')
    print(f'Total loses: {total_losses}')
    print(f'Total wins: {total_wins}')
    print(f'Total runs: {total_runs}')
    print(f'Win percentage: {win_percentage:.0f} %')
    print(f'Legend odds: {total_legends} in {total_wins}')
    print(f'Total shinies found: {total_shinies}')
    for shiny_name in shiny_names:
        print(f'{shiny_name}')
        
    global_wins += total_wins
    global_losses += total_losses
    global_shinies += total_shinies
    global_legends += total_legends

global_runs = global_losses + global_wins
global_win_percentage = 0 if global_runs == 0 else global_wins / global_runs * 100
global_legend_odds = 0 if global_legends == 0 else global_wins / global_legends

print(f'\nGlobal Summary')
print(f'Global loses: {global_losses}')
print(f'Global wins: {global_wins}')
print(f'Global runs: {global_runs}')
print(f'Global Win percentage: {global_win_percentage:.0f} %')
print(f'Global legends: {global_legends}')
print(f'Global legend odds: 1 in {global_legend_odds:.0f}')
print(f'Global shinies found: {global_shinies} \n')
