# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import os
import cv2
import numpy as np
import matplotlib as plt
import random
from collections import OrderedDict

DEFAULT_BOARD_FILE = 'Risk_game_map.png'

global colors
colors = {}

global countries
countries = {}

global players
players = OrderedDict()

global continents
continents = {}

def load_colors():
    
    global colors
    for c in ['blue', 'green', 'red', 'yellow', 'orange', 'purple']:
        norm = list(plt.colors.to_rgb('xkcd:dark {}'.format(c)))
        light = list(plt.colors.to_rgb('xkcd:light {}'.format(c)))
        
        brgnorm = [int(i * 255) for i in reversed(norm)]
        brglight = [int(i * 255) for i in reversed(light)]
        colors[c] = [brgnorm, brglight]
    
class Country:
    def __init__(self, name, continent, borders):
        self.name = name
        self.continent = continent
        self.borders = borders
        self.owner = ''
        self.troops = 0
        
        image_name = 'Pictures/{}.png'.format(name)
        self.image = cv2.imread(image_name, cv2.IMREAD_GRAYSCALE)
        self.outline = cv2.Canny(self.image,100,200)
        M = cv2.moments(self.image)
        self.cX = int(M["m10"] / M["m00"])
        self.cY = int(M["m01"] / M["m00"])
        
    def newOwner(self, owner):
        global players
        if self.owner and self.owner != owner:
            print('{} captured {} from {}'.format(owner, self.name, self.owner))
            players[self.owner].removeCountry(self.name)
        
        self.owner = owner
        players[self.owner].addCountry(self.name)
        self.troops = 0
        
    def addTroops(self, troops=1):
        self.troops += troops
        
    def removeTroops(self, troops=1):
        self.troops -= troops
        
class Player:
    def __init__(self, color):
        self.color = color
        self.mycountries = []
        
    def addCountry(self, country_name):
        self.mycountries.append(country_name)
        
    def removeCountry(self, country_name):
        self.mycountries.remove(country_name)
        
    def takeTurn(self):
        self.placeTroops(new_troops(set(self.mycountries)))
        #show_board()
        self.attack()
        
    def placeTroops(self, num_troops):
        for it in range(num_troops):
            random.shuffle(self.mycountries)
            countries[self.mycountries[0]].addTroops()
            
    def attack(self):
        global countries
        random.shuffle(self.mycountries)
        for c in [countries[c] for c in self.mycountries]:
            if c.troops < 3:
                continue
            
            for ec in c.borders:
                if countries[ec].owner == self.color:
                    continue
                
                while c.troops > 1 and countries[ec].troops > 0:
                    attack_country(c, countries[ec])
                    
                if c.troops > 1:
                    countries[ec].newOwner(self.color)
                    self.move_troops(c, countries[ec], c.troops-1)
                    
                return
            
    def move_troops(self, from_country, to_country, num_move):
        # Todo check for valid path and ownership
        from_country.removeTroops(num_move)
        to_country.addTroops(num_move)
        
def roll_die():
    return random.randint(1,6)

def rolls(num_rolls):
    
    return sorted([roll_die() for i in range(num_rolls)], reverse=True)
        
def attack_country(attacking_country, defending_country, attacking_troops=3):
    
    attack_available = attacking_country.troops - 1
    if attack_available < attacking_troops:
        attacking_troops = attack_available
        
    defending_troops = 2 if defending_country.troops > 1 else 1
    
    attack_rolls = rolls(attacking_troops)
    defend_rolls = rolls(defending_troops)
    
    i = 0
    while i < min(attacking_troops, defending_troops):
        if attack_rolls[i] > defend_rolls[i]:
            defending_country.removeTroops()
        else:
            attacking_country.removeTroops()
            
        i += 1
        
        
def new_troops(my_countries):
    
    global continents
    
    # Country Count Troops
    troops = int(len(my_countries) / 3)
    if troops < 3:
        troops = 3
        
    # Continent Bonus
    for n, cont in continents.items():
        if cont <= my_countries:
            troops += int(n[-1])
            
    return troops
    
def load_countries(country_file):
    
    global countries
    global continents
    
    lines = []
    with open(country_file, 'r') as fid:
        lines = fid.readlines()
        
    for l in lines:
        parts = l.strip().split()
        countries[parts[0]] = Country(parts[0], parts[1], parts[2:])
        
        continent = continents.get(parts[1], set())
        continent.add(parts[0])
        continents[parts[1]] = continent

def initial_players(num_players=2):
    
    global players
    global colors
    global countries
    
    color_list = list(colors.keys())
    
    for i in range(num_players):
        players[color_list[i]] = Player(color_list[i])
        
    start_armies = 40 - 5 * (num_players - 2)
    country_list = list(countries.keys())
    random.shuffle(country_list)

    for i in range(start_armies):
        for pn, p in players.items():
            if country_list:
                c = country_list.pop()
                countries[c].newOwner(pn)
                countries[c].addTroops()
            else:
                random.shuffle(p.mycountries)
                countries[p.mycountries[0]].addTroops()
            
            #show_board()
                
def show_country_background(base_image, country):

    global colors
    
    if not country.owner:
        return
        
    c = country.owner
    
    # Fill in the background
    base_image[np.where(country.image!=[0])] = colors[c][1]
        
    # FIll in the edges
    base_image[np.where(country.outline!=[0])] = colors[c][0]
            
def show_country_troops(base_image, country):
    
    global colors
    
    if not country.owner:
        return
        
    c = country.owner
    
    cX = country.cX
    cY = country.cY
    
    # setup text
    font = cv2.FONT_HERSHEY_SIMPLEX
    text = str(country.troops)
    border = 10
    
    # get boundary of this text
    textsize = cv2.getTextSize(text, font, 1, 2)[0]
    
    # get coords based on boundary
    lowerL = int(cX - (textsize[0] + border) / 2)
    lowerR = int(cY + (textsize[1] + border) / 2)
    upperL = int(cX + (textsize[0] + border) / 2)
    upperR = int(cY - (textsize[1] + border) / 2)
    lowerLT = int(cX - textsize[0] / 2)
    lowerRT = int(cY + textsize[1] / 2)    
    cv2.rectangle(base_image, (lowerL, lowerR), (upperL, upperR), colors[c][0], -1)
    
    # add text centered on image
    cv2.putText(base_image, text, (lowerLT, lowerRT), font, 1, colors[c][1], 2)
    
def show_board(wait=0):
    
    global countries
    base_image = cv2.imread(DEFAULT_BOARD_FILE)
    
    for cn, c in countries.items():
        show_country_background(base_image, c)
        
    for cn, c in countries.items():
        show_country_troops(base_image, c)
        
    cv2.imshow('image', base_image)
    cv2.waitKey(wait)
        
def main():
    
    global players
    
    random.seed(1)
    load_colors()
    load_countries('Countries.txt')
    initial_players(3)
    
    show_board()
    
    # Whoever picked last, goes first
    player_list = list(players.keys())
    player_list.reverse()
    
    while len(players) > 1:
        
        ip = 0
        while ip < len(players):
            p = players[player_list[ip]]
            if not p.mycountries:
                del players[player_list[ip]]
                continue
            
            p.takeTurn()
            show_board()
            ip += 1
            
        #break
        
    
    cv2.destroyAllWindows()

if __name__ == '__main__':
    
    try:
        main()
    except:
        cv2.destroyAllWindows()
        raise