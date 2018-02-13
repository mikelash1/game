# -*- coding: utf-8 -*-
"""
Created on Sat Feb 10 21:10:59 2018

@author: mike
"""

import logging
import random
import itertools

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
        card_troops, cards = self.turn_in_cards()
        self.placeTroops(new_troops + card_troops)
        #show_board()
        conquered, defeated_cards = self.attack()
        self.reinforce()
        
        return conquered, cards + defeated_cards
        
    def turn_in_cards(self, bonus = True):
        
        new_troops = 0
        cards = []
        if len(self.mycards) > 2:
            for c in itertools.combinations(self.mycards, 3):
                card_set = set([int(card.value[-1]) for card in c])
                if len(card_set) != 2:
                    new_troops = max(card_set)
                    if len(card_set) == 3:
                        new_troops = 10
                       
                    logging.info(' {} troops from cards'.format(new_troops))
                    for card in c:
                        if card.territory and card.territory.owner == self and bonus:
                            logging.info(' 2 bonus troops from card on {}'.format(card.territory.name))
                            card.territory.addTroops(2)
                            bonus = False
                            
                        cards.append(card)
                        self.mycards.remove(card)
                    
                    break
            
        return new_troops, cards
    
    def placeTroops(self, num_troops):
        
        logging.info('{} receives {} troops to place'.format(self.name, num_troops))
        for it in range(num_troops):
            myrandterr = list(self.myterritories)
            random.shuffle(myrandterr)
            for t in myrandterr:
                if not t.is_isolated():
                    t.addTroops()
                    break
            
    def attack(self):
        
        conquered = False
        defeated_cards = []
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
                    last_owner = et.owner
                    et.newOwner(self)
                    conquered = True
                    self.move_troops(t, et, t.troops-1)
                    
                    if not last_owner.myterritories:
                        logging.info('{} received {} cards for defeating {}' \
                             .format(self.name, len(last_owner.mycards), last_owner.name))
                        
                        self.mycards += et.owner.mycards
                        last_owner.mycards = []
                        while len(self.mycards) > 5:
                            card_troops, cards = self.turn_in_cards(False)
                            self.placeTroops(card_troops)
                            defeated_cards += cards
                else:
                    logging.info('{} failed to take {} attacking from {}'.format( \
                          self.name, et.name, t.name))
                    
                    break
                
        return conquered, defeated_cards
            
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