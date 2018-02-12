# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

from GameState import GameState
import Player

import cv2
import random
import matplotlib as plt
import logging

def main():
    
    random.seed(1)
    
    root = logging.getLogger()
    while root.handlers:
        root.handlers.pop()
        
    formatter = logging.Formatter("%(message)s")
    # Setup console logging
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    root.addHandler(ch)
    
    num_players = 4
    players = []
    for c in ['blue', 'green', 'red', 'yellow', 'orange', 'purple'][:num_players]:
        dark = list(plt.colors.to_rgb('xkcd:dark {}'.format(c)))
        light = list(plt.colors.to_rgb('xkcd:light {}'.format(c)))
        
        brgdark = [int(i * 255) for i in reversed(dark)]
        brglight = [int(i * 255) for i in reversed(light)]
        players.append(Player.Player(c, brglight, brgdark))
    
    gs = GameState('World', players)
    gs.play_game()

if __name__ == '__main__':
    
    try:
        main()
    except:
        raise
    finally:
        cv2.destroyAllWindows()