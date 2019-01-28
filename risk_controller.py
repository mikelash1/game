
import logging
import sys
import random

from risk_model import risk_model, GameState, MAX_PLAYERS
from risk_view import risk_view, RECHECK_TIME

class risk_controller():
    def __init__(self, map_name, player_list = [], human_setup = False, force_gui = False):
        
        self.init_logging()
        self.map_name = map_name
        self.player_list = player_list[:MAX_PLAYERS]
        self.human_setup = human_setup
        self._force_gui = force_gui
        self._using_gui = False
        self._finished = False
        
        self.model = risk_model(map_name, player_list)
        self.view = None
        for p in self.player_list:
                logging.debug('Adding player {} to game'.format(p.name))
                p.model = self.model
        
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
        return self.model.model_data
    
    def handle_array(self, player_array, input_validation_array, return_array):
    
        for gs in GameState:
            #print(gs, player_array[gs], input_validation_array[gs])
            if player_array[gs] and input_validation_array[gs]:
                #print(gs.name)
                if hasattr(self, gs.name):
                    if getattr(self, gs.name)(player_array, input_validation_array, return_array):
                        return True
                elif not self.model.players:
                    logging.debug('Need to add {} function in controller'.format(gs.name))
                
        return self.model.players[0].handle_array(player_array, input_validation_array, return_array)
    
    def SelectMap(self, _, __, return_array):
        
        if self.human_setup:
            return False
        
        self.model.set_map(self.map_name)
        return_array[GameState.SelectMap] = 1
        return True
    
    def AddPlayer(self, _, __, return_array):
        
        if self.human_setup:
            return False
        
        if len(self.model.players) == len(self.player_list) and self.model.map_name:
            return_array[GameState.StartGame] = 1
            return True

        for p in self.player_list:
            if p not in self.model.players:
                logging.debug('Adding player {} to game'.format(p.name))
                p.set_model(self.model)
                self.model.add_player(player = p)
                return_array[GameState.AddPlayer] = 1
                return True
    
    def StartGame(self, player_array, _, return_array):
        
        if self.human_setup:
            return False
        
        if len(self.model.players) != len(self.player_list) or not self.model.map_name:
            return False
            
        return_array[GameState.StartGame] = 1
        
        return True
    
    def RandomTerritories(self, _, __, return_array):
        # Until we implement choosing territories,
        # if random is available, we select it
        return_array[GameState.RandomTerritories] = 1
        return True
    
    def finish_game(self):
        
        if self._using_gui:
            self.view.quit()
        self._finished = True
    
    def process_array(self):
        
        #logging.debug('Calling process_array')
        player_array, input_validation_array, return_array = self.model.model_data
        
        if player_array[GameState.GameOver]:
            self.finish_game()
            return 
        
        recheck = RECHECK_TIME
        if self.handle_array(player_array, input_validation_array, return_array):
            #print('risk_controller - process_array',return_array)
            self.model.handle_return_array(return_array)
            
            #If the controller is handling the action, no need to wait
            if self._force_gui and player_array[GameState.StartTurn]:
                self.init_view()
                self.view.handle_array(player_array, input_validation_array, return_array, handle_data=False)
            else:
                recheck = 0
        else:
            #raise Exception(player_array)
            self.init_view()
            self.view.handle_array(player_array, input_validation_array, return_array)
            
        if self._using_gui:
            self.view.root.after(recheck, self.process_array)  # reschedule event
    
    def init_view(self):
        
        if not self._using_gui:
            self._using_gui = True
            self.view = risk_view(self, self.model)
            self.view.root.after(0, self.process_array)
            self.view.run() 
    
    def run(self):
        
        while not self._finished:
            self.process_array()
            
        return self.model.players[0].name
