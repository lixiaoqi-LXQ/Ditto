import json
import os

def dump_output(fname, out, append=False):
    if not os.path.exists('./results'):
        os.mkdir('./results')
    with open(f'results/{fname}.txt', 'a' if append else 'w') as f:
        f.write(out)

def save_res(fname, dict):
    # save file to the results directory
    if not os.path.exists('./results'):
        os.mkdir('./results')
    with open(f'results/{fname}.json', 'w') as f:
        json.dump(dict, f)


def load_res(fname):
    if not os.path.exists(f'./results/{fname}'):
        return None
    with open(f'results/{fname}', 'r') as f:
        return json.load(f)


def save_time(figName, duration):
    if not os.path.exists('./results/timer.json'):
        res = {figName: duration}
    else:
        res = load_res('timer.json')
        res[figName] = duration
    save_res('timer', res)
