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
from numpy.matlib import rand

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
    def __init__(self, name, color = ColorInfo('grey')):
        self.name = name
        self.color = color
        self.terr_start = len(GameState)
        
    def handle_array(self, player_array, input_validation_array, return_array):
        
        valid_choice_array = player_array[:len(GameState)]
        valid_choices = list(np.where(valid_choice_array > 0)[0])
        random.shuffle(valid_choices)
        
        for c in valid_choices:
            gs = [gs for gs in GameState if gs.value == c][0]
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
        return_array[GameState.StartTurn.value] = 1
        return True
    
    
        
    # TODO: replace this with drop down in view
    def TakeOverReinforcement(self, player_array, input_validation_array, return_array):
        
        return_array[GameState.TakeOverReinforcement.value] = .99
        return True

class RandomComputerPlayer(Player):
        
    def StartTurn(self, player_array, input_validation_array, return_array):
        logging.debug('{} StartTurn'.format(self.__class__.__name__))
        return_array[GameState.StartTurn.value] = 1
        return True
    
    def TurnInCards(self, player_array, input_validation_array, return_array):
        logging.debug('{} TurnInCards'.format(self.__class__.__name__))
        return_array[GameState.TurnInCards.value] = 1
        return True
    
    def SelectCard(self, player_array, input_validation_array, return_array):
        
        input_valid_terr = input_validation_array[self.terr_start:]
        return_array_terr = return_array[self.terr_start:]
        valid_indicies = np.where(input_valid_terr == 1)[0]
        choice_index = random.choice(list(valid_indicies))
        #if choice_index > return_array_terr.size - 3:
        #    return False
        
        return_array[GameState.SelectCard.value] = 1
        return_array_terr[choice_index] = 1
        return True
    
    def StartTroopPlacement(self, player_array, input_validation_array, return_array):
        logging.debug('{} StartTroopPlacement'.format(self.__class__.__name__))
        return_array[GameState.StartTroopPlacement.value] = 1
        return True
    
    def PlaceTroops(self, player_array, input_validation_array, return_array):
        
        input_valid_terr = input_validation_array[self.terr_start:]
        return_array_terr = return_array[self.terr_start:]
        valid_indicies = np.where(input_valid_terr == 1)[0]
        return_array[GameState.PlaceTroops.value] = 1
        return_array_terr[random.choice(list(valid_indicies))] = random.random()
        return True
    
    def SelectAttackingTerritory(self, player_array, input_validation_array, return_array):
        
        input_valid_terr = input_validation_array[self.terr_start:]
        return_array_terr = return_array[self.terr_start:]
        valid_indicies = np.where(input_valid_terr == 1)[0]
        
        return_array[GameState.SelectAttackingTerritory.value] = 1
        return_array_terr[random.choice(list(valid_indicies))] = 1
        return True
        
    def SelectDefendingTerritory(self, player_array, input_validation_array, return_array):
        
        input_valid_terr = input_validation_array[self.terr_start:]
        return_array_terr = return_array[self.terr_start:]
        valid_indicies = np.where(input_valid_terr == 1)[0]
        return_array[GameState.SelectDefendingTerritory.value] = 1
        return_array_terr[random.choice(list(valid_indicies))] = random.random()
        return True
    
    def TakeOverReinforcement(self, player_array, input_validation_array, return_array):
        
        return_array[GameState.TakeOverReinforcement.value] = random.random()
        
        if not return_array[GameState.TakeOverReinforcement.value]:
            import sys
            return_array[GameState.TakeOverReinforcement.value] = sys.float_info.epsilon
            
        return True
    
    def EndTurn(self, player_array, input_validation_array, return_array):
        
        return_array[GameState.EndTurn.value] = 1
        return True

    def SkipReinforcement(self, player_array, input_validation_array, return_array):
        
        return_array[GameState.SkipReinforcement.value] = 1
        return True

    def SelectReiforceSource(self, player_array, input_validation_array, return_array):
        
        input_valid_terr = input_validation_array[self.terr_start:]
        return_array_terr = return_array[self.terr_start:]
        valid_indicies = np.where(input_valid_terr == 1)[0]
        return_array[GameState.SelectReiforceSource.value] = 1
        
        return_array_terr[random.choice(list(valid_indicies))] = random.random()
        return True
    
    def SelectReiforceDestination(self, player_array, input_validation_array, return_array):
        
        input_valid_terr = input_validation_array[self.terr_start:]
        return_array_terr = return_array[self.terr_start:]
        valid_indicies = np.where(input_valid_terr == 1)[0]
        return_array[GameState.SelectReiforceDestination.value] = 1
        return_array_terr[random.choice(list(valid_indicies))] = 1
        return True
    
    
class BasicComputerPlayer(RandomComputerPlayer):
    
    def SelectAttackingTerritory(self, player_array, input_validation_array, return_array):
        
        input_valid_terr = input_validation_array[self.terr_start:]
        return_array_terr = return_array[self.terr_start:]
        valid_indicies = np.where(input_valid_terr == 1)[0]
        return_array[GameState.SelectAttackingTerritory.value] = 1
        return_array_terr[random.choice(list(valid_indicies))] = 1
        return True 
    