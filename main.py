# -*- coding: utf-8 -*-

from risk_controller import risk_controller
from Player import HumanPlayer, RandomComputerPlayer, BasicComputerPlayer, ColorInfo
#from NNPlayer import NNPlayer

import random
import timeit
import cProfile

import pstats

MIN_RAND = 1
MAX_RAND = 2
MIN_PLAYER = 2
MAX_PLAYER = 6

OUTFILE = 'tmp.txt'
FORCE_GUI = False

LIMIT = []

def main():
    with open(OUTFILE, 'w') as fid:
        pass
    
    pl = [ 
      #('blue', NNPlayer),
      #('blue', HumanPlayer),
      ('blue', BasicComputerPlayer),
      ('green', BasicComputerPlayer),
      ('red', RandomComputerPlayer),
      #('yellow', HumanPlayer),
      #('orange', HumanPlayer),
      #('purple', HumanPlayer),
      ('yellow', RandomComputerPlayer),
      ('orange', RandomComputerPlayer),
      ('purple', RandomComputerPlayer),
      ]
    
    pl = [t(c, ColorInfo(c)) for c, t in pl]
    
    for r in range(MIN_RAND, MAX_RAND+1):
        for p in range(MIN_PLAYER, MAX_PLAYER+1):
            
            if LIMIT and (r, p) not in LIMIT:
                continue
            
            print(f'Random seed: {r}, Players: {p}')
            random.seed(r)
            try:
                start = timeit.default_timer()
                winner = risk_controller(map_name='World', player_list=pl[:p], force_gui=FORCE_GUI).run()
                stop = timeit.default_timer()
                str_out = f'Random seed: {r}, Players: {p}, Winner: {winner} Time: {stop-start:.2f}\n'
                with open(OUTFILE, 'a') as fid:
                    fid.write(str_out)
                print(str_out)
            except:
                print(f'Random seed: {r}, Players: {p}')
                raise
            
            if FORCE_GUI:
                return

if __name__ == "__main__":
    #cProfile.run('main()', 'restats')
    #p = pstats.Stats('restats')
    #p.sort_stats('time').print_stats(10)
    main()