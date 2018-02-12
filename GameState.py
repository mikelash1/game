# -*- coding: utf-8 -*-
"""
Created on Fri Feb  9 15:04:00 2018

@author: LashMi
"""

import cv2
import numpy as np
import logging
import random

def roll_die():
    return random.randint(1,6)

def rolls(num_rolls):
    
    return sorted([roll_die() for i in range(num_rolls)], reverse=True)
        
def attack_territory(attacking_territory, defending_territory, attacking_troops=3):
    
    attack_available = attacking_territory.troops - 1
    if attack_available < attacking_troops:
        attacking_troops = attack_available
        
    defending_troops = 2 if defending_territory.troops > 1 else 1
    
    attack_rolls = rolls(attacking_troops)
    defend_rolls = rolls(defending_troops)
    
    i = 0
    while i < min(attacking_troops, defending_troops):
        if attack_rolls[i] > defend_rolls[i]:
            defending_territory.removeTroops()
        else:
            attacking_territory.removeTroops()
            
        i += 1

class Territory:
    def __init__(self, name, continent, borders, board):
        self.name = name
        self.continent = continent
        self.borders = borders
        self.owner = None
        self.troops = 0
        
        image_name = 'World/{}.png'.format(name)
        self.image = cv2.imread(image_name, cv2.IMREAD_GRAYSCALE)
        self.outline = cv2.Canny(self.image,100,200)
        M = cv2.moments(self.image)
        self.cX = int(M["m10"] / M["m00"])
        self.cY = int(M["m01"] / M["m00"])
        
    def newOwner(self, owner):
        
        if self.owner and self.owner.name != owner.name:
            logging.info('{} captured {} from {}'.format(owner.name, self.name, self.owner.name))
            self.owner.remove_territory(self)
        
        self.owner = owner
        self.owner.add_territory(self)
        self.troops = 0
        
    def addTroops(self, troops=1):
        self.troops += troops
        
    def removeTroops(self, troops=1):
        self.troops -= troops
        
    def is_isolated(self):
        
        for t in self.borders:
            if self.owner != t.owner:
                return False
            
        return True

class GameState:
    def __init__(self, board, players):
        self.board = board
        self.board_base_image = '{0}/{0}.png'.format(board)
        self.players = players
        self.territories = {}
        self.continents = {}
        
        self.load_territories()
        
    def load_territories(self):
        
        lines = []
        with open('{}/Territories.txt'.format(self.board), 'r') as fid:
            lines = fid.readlines()
            
        for l in lines:
            parts = l.strip().split()
            new_terr = Territory(parts[0], parts[1], parts[2:-1], self.board)
            self.territories[parts[0]] = new_terr
            
            continent = self.continents.get(parts[1], set())
            continent.add(new_terr)
            self.continents[parts[1]] = continent
            
        for n, t in self.territories.items():
            t.borders = [self.territories[t2] for t2 in t.borders]
    
    def show_board(self, wait=0):
    
        base_image = cv2.imread(self.board_base_image)
        tl = list(self.territories.values())
        
        for t in tl:
            self.show_territory_background(base_image, t)
            
        for t in tl:
            self.show_territory_troops(base_image, t)
            
        cv2.imshow(self.board, base_image)
        cv2.waitKey(wait)
        
    def show_territory_background(self, base_image, territory):
        
        if not territory.owner:
            return
            
        cl = territory.owner.brg_light_color
        cd = territory.owner.brg_dark_color
        
        # Fill in the background
        base_image[np.where(territory.image!=[0])] = cl
            
        # FIll in the edges
        base_image[np.where(territory.outline!=[0])] = cd
                
    def show_territory_troops(self, base_image, territory):
        
        if not territory.owner:
            return
        
        cl = territory.owner.brg_light_color
        cd = territory.owner.brg_dark_color
        
        cX = territory.cX
        cY = territory.cY
        
        # setup text
        font = cv2.FONT_HERSHEY_SIMPLEX
        text = str(territory.troops)
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
        cv2.rectangle(base_image, (lowerL, lowerR), (upperL, upperR), cd, -1)
        
        # add text centered on image
        cv2.putText(base_image, text, (lowerLT, lowerRT), font, 1, cl, 2)
        
    def new_troops(self, my_territories):
        
        # territory Count Troops
        troops = int(len(my_territories) / 3)
        if troops < 3:
            troops = 3
            
        logging.debug(' {} territory troops'.format(troops))
        # Continent Bonus
        for n, cont in self.continents.items():
            if cont <= set(my_territories):
                cont_troops = int(n[-1])
                logging.debug(' {} troops for {}'.format(cont_troops, n[:-1]))
                troops += cont_troops
                
        return troops
    
    def random_initialization(self):
            
        start_armies = 40 - 5 * (len(self.players) - 2)
        territory_list = list(self.territories.keys())
        random.shuffle(territory_list)
    
        for i in range(start_armies):
            for p in self.players:
                if territory_list:
                    c = territory_list.pop()
                    self.territories[c].newOwner(p)
                    self.territories[c].addTroops()
                else:
                    random.sample(p.myterritories, 1)[0].addTroops()
    
    def play_game(self, show = False):
        
        random.shuffle(self.players)
        
        self.random_initialization()
        
        if show:
            self.show_board()
        
        # Whoever picked last, goes first
        self.players.reverse()
        
        round = 0
        ip = 0
        max_rounds = 99
        while len(self.players) > 1 and round < max_rounds:
            
            if ip >= len(self.players):
                ip = 0
                
            p = self.players[ip]
            if not p.myterritories:
                logging.info('{} is out of the game!!!'.format(p.name))
                del self.players[ip]
                continue
            
            p.takeTurn(self.new_troops(p.myterritories))
            if show:
                self.show_board(500)
            #show_board()
            ip += 1
            #round += 1
            #break
            
        logging.info('{} wins!!!'.format(self.players[0].name))
            
        cv2.destroyAllWindows()