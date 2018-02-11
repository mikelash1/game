# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import GameState

import cv2

import random
from collections import OrderedDict


global colors
colors = {}

global countries
countries = {}

global players
players = OrderedDict()
    

        
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
        self.reinforce()
        
    def placeTroops(self, num_troops):
        global countries
        log('{} receives {} troops'.format(self.color, num_troops))
        for it in range(num_troops):
            random.shuffle(self.mycountries)
            for c in [countries[c] for c in self.mycountries]:
                if not is_isolated(c):
                    c.addTroops()
                    break
            
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
                    
                #show_board()
                if c.troops > 1:
                    countries[ec].newOwner(self.color)
                    self.move_troops(c, countries[ec], c.troops-1)
                else:
                    log('{} failed to take {} attacking from {}'.format( \
                          self.color, countries[ec].name, c.name))
                    
                    break
        return
            
    def move_troops(self, from_country, to_country, num_move):
        # Todo check for valid path and ownership
        from_country.removeTroops(num_move)
        to_country.addTroops(num_move)
        
    def reinforce(self):
        global countries
        for c in [countries[c] for c in self.mycountries]:
            if c.troops < 3:
                continue
            
            for c2 in [countries[c2] for c2 in c.borders]:
                if not is_isolated(c2) and c2.owner == self.color:
                    num_move = c.troops-1
                    log('{} reinforced {} from {} with {} troops'.format( \
                          self.color, c2.name, c.name, num_move))
                    self.move_troops(c, c2, num_move)
                    
                    return
def log(str_in):
    print(str_in)
                
def is_isolated(country):
    
    global countries
    for c in [countries[c] for c in country.borders]:
        if country.owner != c.owner:
            return False
        
    return True
    
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
                
def play_game(board, players):
    
    global players
    global colors
    global countries
    
    game_state = GameState.GameState('World')
    
    random.seed(1)
    colors = game_state.colors
    countries = game_state.countries
    
    game_state.show_board()
    
    # Whoever picked last, goes first
    player_list = list(players.keys())
    player_list.reverse()
    
    round = 0
    max_rounds = 99
    while len(player_list) > 1 and round < max_rounds:
        
        ip = 0
        while ip < len(player_list):
            p = players[player_list[ip]]
            if not p.mycountries:
                log('{} is out of the game!!!'.format(player_list[ip]))
                del player_list[ip]
                continue
            
            p.takeTurn()
            game_state.show_board(1000)
            #show_board()
            ip += 1
            
        round += 1
        #break
        
    cv2.destroyAllWindows()

def main():
    
    initial_players(2)
    play_game('World', 2)

if __name__ == '__main__':
    
    try:
        main()
    except:
        cv2.destroyAllWindows()
        raise