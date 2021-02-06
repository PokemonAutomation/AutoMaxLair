import os

# We need to import log files from the parent directory.
from os.path import dirname, abspath
base_dir = dirname(dirname(abspath(__file__)))
log_path = os.path.join(base_dir, 'logs')
file_list = os.listdir(log_path)

# Modify this list with whatever bosses you want to look at.
bosses = ['articuno', 'zapdos', 'moltres', 'mewtwo', 'raikou', 'entei',
    'suicune', 'lugia', 'ho-oh', 'latias', 'latios', 'kyogre', 'groudon',
    'rayquaza', 'uxie', 'mesprit', 'azelf', 'dialga', 'palkia', 'heatran',
    'giratina', 'cresselia', 'tornadus', 'thundurus', 'reshiram', 'zekrom',
    'landorus', 'kyurem', 'xerneas', 'yveltal', 'zygarde', 'koko', 'lele',
    'bulu', 'fini', 'solgaleo', 'lunala', 'necrozma', 'nihilego', 'xurkitree',
    'buzzwole', 'pheromosa', 'celesteela', 'kartana', 'guzzlord', 'stakataka',
    'blacephalon'
]
global_losses = 0
global_wins = 0

for boss in bosses:
    total_losses = 0
    total_wins = 0

    # Iterate over all relevant log files because a new file is created every
    # time the program is restarted.
    for fn in file_list:
        # Note that early versions capitalize the boss name whereas others do
        # not. Therefore convert all the text to lower case.
        if boss.lower() in fn.lower() and ('.txt' in fn or '.log' in fn):
            with open(os.path.join(log_path, fn), newline='\n', encoding='utf-8') as log_file:
                num_losses = 0
                num_wins = 0
                try:
                    for row in log_file.readlines():
                        # The following lines are logged once at the end of a run.
                        if 'You lose' in row:
                            num_losses += 1
                        if 'Congratulations' in row:
                            num_wins += 1
                except Exception as e:
                    print(f'Error processing {fn}:')
                    print(e)
                total_losses += num_losses
                total_wins += num_wins

    total_runs = total_losses + total_wins
    win_percentage = 0 if total_runs == 0 else total_wins / total_runs * 100

    print(f'Summary for {boss}')
    print(f'Total losses: {total_losses}')
    print(f'Total wins: {total_wins}')
    print(f'Total runs: {total_runs}')
    print(f'Win percentage: {win_percentage:.0f} %\n')

    global_wins += total_wins
    global_losses += total_losses


global_runs = global_losses + global_wins
global_win_percentage = 0 if global_runs == 0 else global_wins / global_runs * 100

print('Global Summary')
print(f'Global losses: {global_losses}')
print(f'Global wins: {global_wins}')
print(f'Global runs: {global_runs}')
print(f'Global Win percentage: {global_win_percentage:.0f} %\n')
