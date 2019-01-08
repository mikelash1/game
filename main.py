# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
'''
from GameState import GameState
import Player

import cv2
import random
import matplotlib as plt
import logging
import sys

from tkinter import ttk
from PIL import Image, ImageTk

def main():
    
    root_ttk = ttk()
    
    random.seed(1)
    
    rootlog = logging.getLogger()
    rootlog.setLevel(logging.DEBUG)
    
    while rootlog.handlers:
        rootlog.handlers.pop()
        
    formatter = logging.Formatter("%(message)s")
    # Setup console logging
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    rootlog.addHandler(ch)
    
    num_players = 6
    players = []
    for c in ['blue', 'green', 'red', 'yellow', 'orange', 'purple'][:num_players]:
        dark = list(plt.colors.to_rgb('xkcd:dark {}'.format(c)))
        light = list(plt.colors.to_rgb('xkcd:light {}'.format(c)))
        
        brgdark = [int(i * 255) for i in reversed(dark)]
        brglight = [int(i * 255) for i in reversed(light)]
        players.append(Player.HumanPlayer(c, brglight, brgdark))
    
    gs = GameState('World', players)
    gs.play_game(500)

if __name__ == '__main__':
    
    try:
        main()
    except:
        raise
    finally:
        cv2.destroyAllWindows()
        
       
       ''' 
# -*- coding: utf-8 -*-
  
"""
Created on Feb 18 10:30:38 2014
 
@author: Sukhbinder Singh
 
A basic python example of Model–view–controller (MVC), a software design pattern for implementing user interfaces for scientific application.
 
Mainly written as a quick start framework to quickly implement tkinter based GUI for prototypes for my personal and 
 
 
"""

''' 
import tkinter as tk
import time

def display():
    #time.sleep(.5)
    print("var_str:", var_int.get())

root = tk.Tk()

var_int = tk.IntVar()
var_int.set(0)

var_str = tk.StringVar()
var_str.set("Troops")

#root.bind('<Button-1>', display) # run display() on every (left button) click

#tk.Checkbutton(root, textvariable=var_int, variable=var_str, onvalue=4, offvalue=-5).pack()
tk.Label(root, textvariable=var_str).pack()
tk.Spinbox(root, textvariable=var_int, from_=0, to=10, width=10, command=display).pack()


root.mainloop()



'''
from risk_controller import risk_controller

if __name__ == '__main__':
    
    risk_controller('World', 4).run()
