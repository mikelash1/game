# -*- coding: utf-8 -*-
"""
Created on Sat Feb 10 21:10:59 2018

@author: mike
"""

import logging
import random

from GameState import attack_territory

class Player:
    def __init__(self, name, brg_light_color = [255, 255, 255], brg_dark_color = [0, 0, 0]):
        self.name = name
        self.brg_light_color = brg_light_color
        self.brg_dark_color = brg_dark_color
        self.myterritories = []
        self.mycards = []
        
    def add_territory(self, territory):
        self.myterritories.append(territory)
        
    def remove_territory(self, territory):
        self.myterritories.remove(territory)
        
    def takeTurn(self, new_troops):
        cards = self.turn_in_cards()
        self.placeTroops(new_troops)
        #show_board()
        conquered = self.attack()
        self.reinforce()
        
        return conquered, cards
        
    def turn_in_cards(self):
        return []
    
    def placeTroops(self, num_troops):
        
        logging.info('{} receives {} troops'.format(self.name, num_troops))
        for it in range(num_troops):
            myrandterr = list(self.myterritories)
            random.shuffle(myrandterr)
            for t in myrandterr:
                if not t.is_isolated():
                    t.addTroops()
                    break
            
    def attack(self):
        
        conquered = False
        myterr = list(self.myterritories)
        for t in myterr:
            if t.troops < 3:
                continue
            
            for et in t.borders:
                if et.owner == self:
                    continue
                
                while t.troops > 1 and et.troops > 0:
                    attack_territory(t, et)
                    
                #show_board()
                if t.troops > 1:
                    et.newOwner(self)
                    conquered = True
                    self.move_troops(t, et, t.troops-1)
                else:
                    logging.info('{} failed to take {} attacking from {}'.format( \
                          self.name, et.name, t.name))
                    
                    break
                
        return conquered
            
    def move_troops(self, from_territory, to_territory, num_move):
        # Todo check for valid path and ownership
        from_territory.removeTroops(num_move)
        to_territory.addTroops(num_move)
        
    def reinforce(self):
        
        for t in self.myterritories:
            if t.troops < 3:
                continue
            
            for t2 in t.borders:
                if not t2.is_isolated() and t2.owner == self:
                    num_move = t.troops-1
                    logging.info('{} reinforced {} from {} with {} troops'.format( \
                          self.name, t2.name, t.name, num_move))
                    self.move_troops(t, t2, num_move)
                    
                    return