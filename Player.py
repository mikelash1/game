# -*- coding: utf-8 -*-
"""
Created on Sat Feb 10 21:10:59 2018

@author: mike
"""

import logging
import matplotlib as plt
from risk_model import GameState
import numpy as np
import random

class ColorInfo():
    def __init__(self, xkcd_color):
        self.light, self.lighthex = self.from_xkcd_color('light ' + xkcd_color)
        self.normal, self.normalhex = self.from_xkcd_color(xkcd_color)
        self.dark, self.darkhex = self.from_xkcd_color('dark ' + xkcd_color)
    
    @staticmethod
    def from_xkcd_color(xkcd_color):
        
        eight_bit = [int(i * 255) for i in list(plt.colors.to_rgb('xkcd:{}'.format(xkcd_color)))]
        hex = '#%02x%02x%02x' % tuple(eight_bit)
        
        return eight_bit, hex
        
class Player:
    def __init__(self, name, color = ColorInfo('grey'), model = None):
        self.name = name
        if type(color) == type(str):
            self.color = ColorInfo(color)
        else:
            self.color = color
          
        self.model = model   
        self._terr_start = len(GameState)
        self._conquer_index = -1
        
    @property
    def model(self):
        return self._model
        
    @model.setter
    def model(self, model):
        self._model = model
        if self._model:
            self._conquer_index = self._model.player_array_conquerd_index
            
    @property
    def terr_start(self):
        return self._terr_start
        
    def handle_array(self, player_array, input_validation_array, return_array):
        
        input_valid_choice_array = input_validation_array[:self._terr_start]
        player_choice_array = player_array[:self._terr_start]
        valid_choices = [GameState[gs] for gs in list(np.where((input_valid_choice_array > 0) & (player_choice_array > 0))[0])]
        
        # If we havent taken over a territory, at least try
        if not player_array[GameState.EndTurn] or not player_array[GameState.SelectAttackingTerritory] \
            or player_array[self._conquer_index]:
            random.shuffle(valid_choices)
        
        for gs in valid_choices:
            if hasattr(self, gs.name):
                if getattr(self, gs.name)(player_array, input_validation_array, return_array):
                    return True
            #else:
            #    logging.debug(gs.name)
                    
        return False
    
        
class HumanPlayer(Player):
    
    #TODO: Take this out
    def StartTurn(self, player_array, input_validation_array, return_array):
        logging.debug('{} StartTurn'.format(self.__class__.__name__))
        return_array[GameState.StartTurn] = 1
        return True

class RandomComputerPlayer(Player):
        
    def StartTurn(self, player_array, input_validation_array, return_array):
        logging.debug('{} StartTurn'.format(self.__class__.__name__))
        return_array[GameState.StartTurn] = 1
        return True
    
    def TurnInCards(self, player_array, input_validation_array, return_array):
        logging.debug('{} TurnInCards'.format(self.__class__.__name__))
        return_array[GameState.TurnInCards] = 1
        return True
    
    def SelectCard(self, player_array, input_validation_array, return_array):
        
        input_valid_terr = input_validation_array[self.terr_start:]
        return_array_terr = return_array[self.terr_start:]
        valid_indicies = np.where(input_valid_terr == 1)[0]
        choice_index = random.choice(list(valid_indicies))
        #if choice_index > return_array_terr.size - 3:
        #    return False
        
        return_array[GameState.SelectCard] = 1
        return_array_terr[choice_index] = 1
        return True
    
    def StartTroopPlacement(self, player_array, input_validation_array, return_array):
        logging.debug('{} StartTroopPlacement'.format(self.__class__.__name__))
        return_array[GameState.StartTroopPlacement] = 1
        return True
    
    def PlaceTroops(self, player_array, input_validation_array, return_array):
        
        input_valid_terr = input_validation_array[self.terr_start:]
        return_array_terr = return_array[self.terr_start:]
        valid_indicies = np.where(input_valid_terr == 1)[0]
        return_array[GameState.PlaceTroops] = 1
        #print(input_valid_terr, return_array_terr)
        selected_index = random.choice(list(valid_indicies))
        return_array_terr[selected_index] = 1 - random.random()
        #print(selected_index)
        return True
    
    def SelectAttackingTerritory(self, player_array, input_validation_array, return_array):
        
        input_valid_terr = input_validation_array[self.terr_start:]
        return_array_terr = return_array[self.terr_start:]
        valid_indicies = np.where(input_valid_terr == 1)[0]
        
        return_array[GameState.SelectAttackingTerritory] = 1
        return_array_terr[random.choice(list(valid_indicies))] = 1
        return True
        
    def SelectDefendingTerritory(self, player_array, input_validation_array, return_array):
        
        input_valid_terr = input_validation_array[self.terr_start:]
        return_array_terr = return_array[self.terr_start:]
        valid_indicies = np.where(input_valid_terr >= 1)[0]
        return_array[GameState.SelectDefendingTerritory] = 1
        return_array_terr[random.choice(list(valid_indicies))] = (1 - random.random())
        return True
    
    def TakeOverReinforcement(self, player_array, input_validation_array, return_array):
        
        return_array[GameState.TakeOverReinforcement] = 1 - random.random()
        return True
    
    def EndTurn(self, player_array, input_validation_array, return_array):
        
        return_array[GameState.EndTurn] = 1
        return True

    def SkipReinforcement(self, player_array, input_validation_array, return_array):
        
        return_array[GameState.SkipReinforcement] = 1
        return True

    def SelectReiforceSource(self, player_array, input_validation_array, return_array):
        
        input_valid_terr = input_validation_array[self.terr_start:]
        return_array_terr = return_array[self.terr_start:]
        valid_indicies = np.where(input_valid_terr == 1)[0]
        return_array[GameState.SelectReiforceSource] = 1
        return_array_terr[random.choice(list(valid_indicies))] = 1
        return True
    
    def SelectReiforceDestination(self, player_array, input_validation_array, return_array):
        
        input_valid_terr = input_validation_array[self.terr_start:]
        return_array_terr = return_array[self.terr_start:]
        valid_indicies = np.where(input_valid_terr == 1)[0]
        return_array[GameState.SelectReiforceDestination] = 1
        return_array_terr[random.choice(list(valid_indicies))] = 1 - random.random()
        return True
    
    
class BasicComputerPlayer(RandomComputerPlayer):
    
    def PlaceTroops(self, player_array, input_validation_array, return_array):
        
        input_valid_terr = input_validation_array[self.terr_start:]
        return_array_terr = return_array[self.terr_start:]
        valid_indicies = list(np.where(input_valid_terr == 1)[0])
        #print(valid_indicies)
        return_array[GameState.PlaceTroops] = 1
        self.prune_troop_relocation(valid_indicies)
        selected_index = random.choice(valid_indicies)
        return_array_terr[selected_index] = 1 - random.random()
        #print(selected_index)
        return True
    
    def SelectReiforceDestination(self, player_array, input_validation_array, return_array):
        
        input_valid_terr = input_validation_array[self.terr_start:]
        return_array_terr = return_array[self.terr_start:]
        valid_indicies = list(np.where(input_valid_terr == 1)[0])
        return_array[GameState.SelectReiforceDestination] = 1
        self.prune_troop_relocation(valid_indicies)
        selected_index = random.choice(valid_indicies)
        return_array_terr[selected_index] = 1 - random.random()
        return True
    
    def prune_troop_relocation(self, valid_indicies):
        
        i = 0
        while i < len(valid_indicies):
            dist = self._model.get_border_dist(valid_indicies[i])
            #print(i, dist)
            if len(dist) == 1 and list(dist.keys())[0] == 0:
                #print(i, valid_indicies, len(valid_indicies))
                del valid_indicies[i]
            else:
                i += 1