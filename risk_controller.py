import logging
import sys
import matplotlib as plt
import random

from risk_model import risk_model, GameState, MAX_PLAYERS
from risk_view import risk_view, RECHECK_TIME
from Player import HumanPlayer, RandomComputerPlayer, ColorInfo

class risk_controller():
    def __init__(self, map_name, num_players = MAX_PLAYERS, human_setup = False):
        
        self.init_logging()
        self.map_name = map_name
        self.num_players = num_players
        self.human_setup = human_setup
        
        self.model = risk_model(self)
        self.view = risk_view(self, self.model)
        
    def init_logging(self):
        
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
    
    def random_init(self):
        self.model.random_initialization()
        
    def get_model_data(self):
        return self.model.get_model_data()
    
    def handle_array(self, player_array, input_validation_array, return_array):
    
        for gs in GameState:
            if player_array[gs.value]:
                if hasattr(self, gs.name):
                    if getattr(self, gs.name)(return_array):
                        return True
                elif not self.model.players:
                    logging.debug('Need to add {} function in controller'.format(gs.name))
                
        return self.model.players[0].handle_array(player_array, input_validation_array, return_array)
    
    def SelectMap(self, return_array):
        
        if self.human_setup:
            return False
        
        self.model.set_map(self.map_name)
        return_array[GameState.SelectMap.value] = 1
        return True
    
    def AddPlayer(self, return_array):
        
        if self.human_setup:
            return False
        
        if len(self.model.players) == self.num_players and self.model.map_name:
            return_array[GameState.StartGame.value] = 1
            return True
        
        # Only add Human Players for now
        current_players = [p.name for p in self.model.players]
        pl = [ \
              ('blue', RandomComputerPlayer) \
              #,('blue', HumanPlayer) \
              ,('green', RandomComputerPlayer) \
              ,('red', RandomComputerPlayer) \
              ,('yellow', HumanPlayer) \
              ,('orange', HumanPlayer) \
              ,('purple', HumanPlayer) \
              ]
        for c, t in pl:
            if c not in current_players:
                logging.debug('Adding player {} to game'.format(c))
                self.model.add_player(player = t(c, ColorInfo(c)))
                return_array[GameState.AddPlayer.value] = 1
                return True
    
    def StartGame(self, return_array):
        
        if self.human_setup:
            return False
        
        if len(self.model.players) != self.num_players or not self.model.map_name:
            return False
            
        return_array[GameState.StartGame.value] = 1
        return True
    
    def RandomTerritories(self, return_array):
        # Until we implement choosing territories,
        # if random is available, we select it
        return_array[GameState.RandomTerritories.value] = 1
        return True
    
    #def finish_game(self):
        
        
    
    def process_array(self):
        
        #logging.debug('Calling process_array')
        player_array, input_validation_array, return_array = self.model.get_model_data()
        
        if player_array[GameState.GameOver.value]:
            #self.finish_game()
            return
        
        recheck = RECHECK_TIME
        if self.handle_array(player_array, input_validation_array, return_array):
            self.model.handle_return_array(return_array)
            
            #If the controller is handling the action, no need to wait
            recheck = 0
        else:
            self.view.handle_array(player_array, input_validation_array, return_array)
            
        self.view.root.after(recheck, self.process_array)  # reschedule event
    
    def run(self):
        
        self.view.root.after(0, self.process_array)
        random.seed(1)
        self.view.run()
