
import numpy as np
import math

import random
import logging
from collections import defaultdict
import enum
from itertools import combinations
from math import ceil

MAX_PLAYERS = 6
MAX_CARDS = 5
UNINIT = -1
TURNED_IN = -2

EXTRA_FIELDS = MAX_PLAYERS + 1
EXTRA_ENUM_OFFSET = MAX_PLAYERS + 1
BLITZ_VALUE = 4

class Territory:
    def __init__(self, name, borders, card_value):
        self._name = name
        self._borders = borders
        self._card_value = card_value
        
    @property
    def name(self):
        return self._name
    
    @property
    def borders(self):
        return self._borders
    
    @borders.setter
    def borders(self, borders):
        self._borders = borders
    
    @property
    def card_value(self):
        return self._card_value
class _Enum(int):
    
    def __new__(cls, name, value, *args, **kwargs):
        return  super(_Enum, cls).__new__(cls, value) 
    
    def __init__(self, name, value):
        self._name = name
        
    @property
    def name(self):
        return self._name
   
class GameStateMeta(type):
    
    def __iter__(self):
        return self.clsiter()
    
    def __len__(self):
        return self.clslength()
   
    def __getitem__(self, key):
        return self.clsgetitem(key)
   
class GameState(metaclass=GameStateMeta):
        
    _values_list = [
        'StartGame',
        'RandomTerritories',
        'StartTurn',
        'TurnInCards',
        'SelectCard',
        'UpdateAlliances',
        'UpdateAnAlliance',
        'StartTroopPlacement',
        'PlaceTroops',
        'SelectTroopPlacement',
        'SelectAttackingTerritory',
        'AttackingTroopCount',
        'SelectDefendingTerritory',
        'TakeOverReinforcement',
        'EndTurn',
        'SkipReinforcement',
        'SelectReiforceSource',
        'SelectReiforceDestination',
        'GameOver',
    ]
    
    #self._value_dict = {}
    for i, v in enumerate(_values_list):
        vars()[v] = _Enum(v, i)
        
    #def __getattr__(self, attr):
    #    return self._value_dict[attr]
    
    @classmethod
    def clslength(cls):
        return len(cls._values_list)
   
    @classmethod
    def clsiter(cls):
        for v in cls._values_list:
            yield vars(cls)[v]
   
    @classmethod
    def clsgetitem(cls, key):
        return vars(cls)[cls._values_list[key]]
   
class risk_model():
 
    def __init__(self, map_name, player_list = []):
        
        # Set the map name and load the 
        self._map_name = map_name
        self._players = player_list
        logging.debug('Setting map to {} in model'.format(self._map_name))
        
        self._territories = []
        self._continents = defaultdict(set)
        self._info_text_observers = []
        self._post_card_territory_troops = 0
        self._alliance_map = defaultdict(dict)
        
        with open('{}/Territories.txt'.format(self._map_name), 'r') as fid:
            for l in fid.readlines():
                parts = l.strip().split()
                new_terr = Territory(parts[0], parts[2:-1], parts[-1])
                self._continents[parts[1]].add(len(self._territories))
                self._territories.append(new_terr)
            
        for t in self._territories:
            t.borders = [i for t2 in t.borders for i, t3 in enumerate(self._territories) if t2 == t3.name]
            
        # Need to size _model_array, 0..N for number of game states
        # then, 1..M for onwer, troop count, card holder, plus 2 for 2 extra wild cards
        # then, MAX_PLAYERS * (MAX_PLAYERS - 1) for alliance associations
        # then final slot for current player has captured at least one territory this turn
        
        self._territory_owner_start = len(GameState)
        game_state_array = np.zeros(self._territory_owner_start)
        territory_size = len(self._territories) * 2
        card_size = len(self._territories) + 2
        territory_array = np.zeros(territory_size + card_size)
        territory_array.fill(UNINIT)
        alliance_size = MAX_PLAYERS * (MAX_PLAYERS - 1)
        alliance_array = np.zeros(alliance_size + 1)
        
        self._model_array = np.concatenate((game_state_array, territory_array, alliance_array), axis = 0)

        self._model_array_gs_view = self._model_array[:self._territory_owner_start]
        
        self._territory_troop_start      = self._territory_owner_start + len(self._territories)
        self._territory_card_start       = self._territory_troop_start + len(self._territories)
        self._alliance_start             = self._territory_card_start + card_size
        self._territory_conquered_index  = self._alliance_start + alliance_size
        
        self._player_array_card_index     = self._alliance_start + (MAX_PLAYERS - 1)
        self._player_array_index          = self._player_array_card_index + MAX_PLAYERS
        self._player_array_conquerd_index = self._player_array_index - 1
        
        self._territory_owner_array_view = self._model_array[self._territory_owner_start:self._territory_troop_start:1]
        self._territory_troop_array_view = self._model_array[self._territory_troop_start:self._territory_card_start:1]
        self._territory_card_array_view  = self._model_array[self._territory_card_start:self._alliance_start:1]
        self._alliance_array_view        = self._model_array[self._alliance_start:self._territory_conquered_index:1]
        
        # Input validation array, this tells the player what territory / card / alliance selections are valid
        # Need slots for all cards + each other player (MAX_PLAYERS - 1)
        self._input_validation_card_array = np.zeros(card_size + MAX_PLAYERS - 1)
        
        self._return_array = np.concatenate((game_state_array, self._input_validation_card_array), axis = 0)
        self._return_array_gs_view  = self._return_array[:self._territory_owner_start]
        self._return_array_card_view = self._return_array[self._territory_owner_start:]
        
        self._model_array[GameState.StartGame] = 1
        
        logging.debug('Created model_array with {} elements'.format(len(self._model_array)))
    
        for gs in GameState:
            if not hasattr(self, gs.name):
                setattr(self, gs.name, self.default_return_array_handler)
            
    @property
    def model_data(self):
        self._return_array[...] = 0
        return self.create_player_array(), np.concatenate((self._model_array_gs_view, self._input_validation_card_array), axis = 0), self._return_array
    
    @property
    def map_name(self):
        return self._map_name
    
    @property
    def players(self):
        return self._players
    
    @property
    def player_array_conquerd_index(self):
        return self._player_array_conquerd_index
    
    @property
    def territories(self):
        return self._territories
    
    @property
    def territory_owner_start(self):
        return self._territory_owner_start
    
    @property
    def territory_troop_start(self):
        return self._territory_troop_start
    
    @property
    def territory_card_start(self):
        return self._territory_card_start
    
    def create_player_array(self):
        
        player_array = self._model_array[:self._player_array_index].copy()
            
        # Hide the identity of the other players cards from current player
        non_player_cards = np.where(self._territory_card_array_view != 0)[0]
        player_array_card_view = player_array[self._territory_card_start:self._alliance_start:1]
        player_array_card_view[non_player_cards] = UNINIT
        
        # ID how many cards each player has
        for i in range(1, MAX_PLAYERS):
            player_array[self._player_array_card_index + i - 1] = len(list(np.where(self._territory_card_array_view == i)[0]))
    
        # Indicate if player has taken a territory this turn
        player_array[self._player_array_conquerd_index] = self._model_array[self._territory_conquered_index]
    
        return player_array
    
    def get_player_summary(self, i):
    
        owner_array = np.where(self._territory_owner_array_view == i)[0]
        if not i:
            attacking_array = np.where(self._territory_owner_array_view > MAX_PLAYERS)[0]
            #print(owner_array, attacking_array)
            owner_array = np.concatenate((owner_array, attacking_array), axis = 0)
            
        #owner_array = owner_array[0]
        terr_count = len(list(owner_array))
        troop_count = int(np.sum(self._territory_troop_array_view[owner_array]))
        card_count = len(list(np.where(self._territory_card_array_view == i)[0]))
        #print(terr_count, troop_count, card_count)
        
        return terr_count, troop_count, card_count
    
    def update_text(self, new_text):
        self._info_text = new_text
        logging.info(self._info_text)
        
        for callback in self._info_text_observers:
            callback(self._info_text)
                
    def bind_to_update_text(self, callback):
        
        self._info_text_observers.append(callback)
    
    def handle_return_array(self, return_array):
        
        #logging.debug('Updating model in handle_return_array')
        #print(return_array)
        self._return_array_gs_view =  return_array[:self._territory_owner_start]
        self._return_array_card_view = return_array[self._territory_owner_start:]
        valid_returns = sorted(list(np.where((self._return_array_gs_view > 0) & (self._model_array_gs_view > 0))[0]), key=lambda x: self._return_array_gs_view[x], reverse = True)
        
        if not valid_returns:
            print(self._model_array_gs_view, self._return_array_gs_vew)
            raise Exception('Invalid return array passed to risk_model')
            
        name = GameState[valid_returns[0]].name
        if getattr(self, name)():
            return
        else:
            print(return_array)
            raise Exception(f'Unable to handle {name} in model')
            
    
    def default_return_array_handler(self):
        
        valid_returns = sorted(list(np.where((self._return_array_gs_view > 0) & (self._model_array_gs_view > 0))[0]), key=lambda x: self._return_array_gs_view[x], reverse = True)
        raise Exception(f'Need to add {GameState[valid_returns[0]].name} handler in model')
    
    def StartGame(self):
        
        if not self._return_array_gs_view[GameState.StartGame]:
            return False
        
        if len(self._players) < 2:
            raise Exception(f'Trying to start game with less than 2 players ({len(self._players)})')
        
        #self._model_array[GameState.AddPlayer] = 0
        self._model_array[GameState.StartGame] = 0
        
        # Need to update here is we implement territory selection
        self._model_array[GameState.RandomTerritories] = 1
            
        logging.debug('Updating model to start the game')
        return True
    
    def RandomTerritories(self):
        
        if not self._return_array_gs_view[GameState.RandomTerritories]:
            return False
        
        self.random_initialization()
        self._model_array[GameState.RandomTerritories] = 0
        self.init_start_turn()
        
        return True
    
    def StartTurn(self):
        
        if not self._return_array_gs_view[GameState.StartTurn]:
            return False
        
        self._model_array[GameState.StartTurn] = 0
        
        self._post_card_territory_troops = 0
        self.init_turn_in_cards()
        
        #If SelectCard set from init_turn_in_cards, we have 5, so we cant place troops yet
        if not self._model_array[GameState.SelectCard]:
            self._model_array[GameState.StartTroopPlacement] = 1
        else:
            self._post_card_territory_troops = self.new_troops()
            
        return True
    
    def StartTroopPlacement(self):
        
        if not self._return_array_gs_view[GameState.StartTroopPlacement]:
            return False
        
        self._model_array[GameState.TurnInCards] = 0
        self._model_array[GameState.StartTroopPlacement] = 0
        self._model_array[GameState.PlaceTroops] += self.new_troops()
        
        self.init_place_troops()
        return True
    
    def PlaceTroops(self):
        
        if not self._return_array_gs_view[GameState.PlaceTroops]:
            return False
        
        terr_index = np.where(self._return_array_card_view > 0)[0]
        
        if not list(terr_index):
            raise Exception('No territory passed into PlaceTroops in risk_model')
        
        if self._territory_owner_array_view[terr_index[0]] > 0:
            print(terr_index[0], self._territory_owner_array_view[terr_index[0]], self._territory_owner_array_view)
            raise Exception('Territory passed in PlaceTroops in risk_model not owned by current player')
        
        #print(card_view[terr_index[0]], self._model_array[GameState.PlaceTroops], int(card_view[terr_index[0]] * self._model_array[GameState.PlaceTroops]))
        troops_to_place = ceil(self._return_array_card_view[terr_index[0]] * self._model_array[GameState.PlaceTroops])
        
        self._territory_troop_array_view[terr_index[0]] += troops_to_place
        text = 'Added {} troop(s) to {}'.format(troops_to_place, self._territories[terr_index[0]].name)
        
        self._model_array[GameState.PlaceTroops] -= troops_to_place
        
        if self._model_array[GameState.PlaceTroops] > 0:
            text += ', {} has {} troops to place'.format(self.players[0].name, int(self._model_array[GameState.PlaceTroops]))
        else:
            self._model_array[GameState.PlaceTroops] = 0
            text += ', select a territory to attack from'
            self.init_attack_from()
        
        self.update_text(text)
        
        return True
    
    def SelectAttackingTerritory(self):
        
        if not self._return_array_gs_view[GameState.SelectAttackingTerritory]:
            return False
        
        attack_terr_index = np.where(self._return_array_card_view != 0)[0]
        if len(list(attack_terr_index)) != 1:
            print(attack_terr_index, self._return_array_card_view)
            raise Exception('Invalid return_array in SelectAttackingTerritory')
        
        attack_terr_index = attack_terr_index[0]
        max_troops_to_attack_with = min(3, self._territory_troop_array_view[attack_terr_index] - 1)
        
        self._territory_owner_array_view[attack_terr_index] = EXTRA_ENUM_OFFSET
        self._model_array[GameState.SelectAttackingTerritory] = 0
        self._model_array[GameState.EndTurn] = 0
        self._model_array[GameState.SelectDefendingTerritory] = max_troops_to_attack_with
        
        self._input_validation_card_array[...] = 0
        self._input_validation_card_array[self._territories[attack_terr_index].borders] = 1
        # Cant attack ourselves
        self._input_validation_card_array[np.where(self._territory_owner_array_view == 0)[0]] = 0
        
        self.update_text('{} is attacking from {}, select territory to attack'. \
            format(self.players[0].name, self._territories[attack_terr_index].name))
        
        return True
    
    def SelectDefendingTerritory(self):
        
        if not self._return_array_gs_view[GameState.SelectDefendingTerritory]:
            return False
        
        attack_index = np.where(self._territory_owner_array_view > MAX_PLAYERS)[0]
        if len(list(attack_index)) != 1:
            print(self._model_array)
            print(self._territory_owner_array_view)
            raise Exception('Invalid attack_index for execute_attack')
        
        defend_terr_index = np.where(self._return_array_card_view != 0)[0]
        if len(list(defend_terr_index)) != 1:
            print(self._return_array_card_view)
            raise Exception('Invalid return_array in SelectDefendingTerritory')
        
        attack_index = attack_index[0]
        defend_terr_index = defend_terr_index[0]
        #print(attack_index, defend_terr_index, self._territory_troop_array_view[defend_terr_index])
        
        max_troops = min(3, int(self._territory_troop_array_view[attack_index]) - 1)
        troop_options = list(range(1, max_troops + 1)) + [BLITZ_VALUE]
        attack_troops_to_use = BLITZ_VALUE
        if self._return_array_card_view[defend_terr_index] < 1:
            attack_troops_to_use_index = int((len(troop_options) + 1) * self._return_array_card_view[defend_terr_index]) - 1
            attack_troops_to_use = troop_options[attack_troops_to_use_index]
        #print(troop_options, work_array[defend_terr_index], attack_troops_to_use)
        self._territory_owner_array_view[attack_index] += attack_troops_to_use
            
        if attack_troops_to_use == BLITZ_VALUE:
            self.update_text('{} is blitzing {} ({}) from {} ({})'. \
                format(self.players[0].name, self._territories[defend_terr_index].name, self._territory_troop_array_view[defend_terr_index], \
                self._territories[attack_index].name, self._territory_troop_array_view[attack_index]))
        else:
            if attack_troops_to_use > max_troops:
                raise Exception('Invalid input for SelectDefendingTerritory, attempting to use {} troop(s), only {} available'\
                    .format(attack_troops_to_use, max_troops))
                
            self.update_text('{} is attacking {} ({}) from {} ({}) with {} troop(s)'. \
                 format(self.players[0].name, self._territories[defend_terr_index].name, self._territory_troop_array_view[defend_terr_index], \
                        self._territories[attack_index].name, self._territory_troop_array_view[attack_index], \
                        attack_troops_to_use))

        attack_lost = [0]
        defend_lost = [0]
        attackers_last_used = [0]
        self.execute_attack(attack_index, defend_terr_index, attack_lost, defend_lost, attackers_last_used)
        
        text_str = '{} lost {} troop(s), {} lost {} troop(s)'.format( \
            self._territories[attack_index].name, attack_lost[0], \
            self._territories[defend_terr_index].name, defend_lost[0])
        
        self._model_array[GameState.SelectDefendingTerritory] = 0
        
        # Territory defended, just start over with attacking
        if self._territory_troop_array_view[defend_terr_index] > 0:
            self._territory_owner_array_view[attack_index] = 0
            self.update_text(text_str + ', {} failed to take over {}, select next territory to attack from'. \
                format(self.players[0].name, self._territories[defend_terr_index].name))
            self.init_attack_from()
            return True
        
        # Territory taken over
        self._model_array[GameState.TakeOverReinforcement] = attackers_last_used[0]
        self.update_text(text_str + ', {} took over {} from {}, select how many troops move'. \
                format(self.players[0].name, self._territories[defend_terr_index].name, self._territories[attack_index].name))
           
        return True
    
    def TakeOverReinforcement(self):
        
        if not self._return_array_gs_view[GameState.TakeOverReinforcement]:
            return False
        
        attack_index = np.where(self._territory_owner_array_view > MAX_PLAYERS)[0]
        if len(list(attack_index)) != 1:
            raise Exception('Invalid attack_index for TakeOverReinforcement')
        
        attack_index = attack_index[0]
        
        defend_index = np.where(self._territory_troop_array_view == 0)[0]
        if len(list(defend_index)) != 1:
            raise Exception('Invalid defend_index for TakeOverReinforcement')
        
        defend_index = defend_index[0]
        
        min_troops_to_move = self._model_array[GameState.TakeOverReinforcement]
        max_troops_to_move = self._territory_troop_array_view[attack_index] - 1
        frac = self._return_array_gs_view[GameState.TakeOverReinforcement]
        troops_to_move = int((max_troops_to_move - min_troops_to_move) * frac + min_troops_to_move)
        
        self.update_text('{} moved {} troop(s) from {} to {}, select next territory to attack from'. \
             format(self.players[0].name, troops_to_move, self._territories[attack_index].name, \
            self._territories[defend_index].name))
        
        old_owner = int(self._territory_owner_array_view[defend_index])
        self._territory_troop_array_view[attack_index] -= troops_to_move
        self._territory_troop_array_view[defend_index] += troops_to_move
        
        self._territory_owner_array_view[attack_index] = 0
        self._territory_owner_array_view[defend_index] = 0
        
        self._model_array[self._territory_conquered_index] = 1
        self._model_array[GameState.TakeOverReinforcement] = 0
        
        old_owner_terr = np.where(self._territory_owner_array_view == old_owner)[0]
        #print(old_owner, old_owner_terr)
        if not list(old_owner_terr):
            self.elimate_player(old_owner)
            return True
            
        self.init_attack_from()
        
        #print(self._model_array)
        return True
    
    def EndTurn(self):
        
        if not self._return_array_gs_view[GameState.EndTurn]:
            return False
        
        # Took over atleast one territory, we get a card
        if self._model_array[self._territory_conquered_index]:
            free_card_index = list(np.where(self._territory_card_array_view == UNINIT)[0])
            if not free_card_index:
                free_card_index = list(np.where(self._territory_card_array_view == TURNED_IN)[0])
                self._territory_card_array_view[free_card_index] = UNINIT
                #print(self._model_array)

            self._territory_card_array_view[random.choice(free_card_index)] = 0
               
        self._model_array[GameState.SelectAttackingTerritory] = 0
        self._model_array[GameState.EndTurn] = 0
        
        # Make sure we have a valid territory that could supply troops
        # Has more than one troop
        my_terr_index = list(np.where((self._territory_owner_array_view == 0) & (self._territory_troop_array_view > 1))[0])
        #print(my_terr_index)
        
        # make sure each has a border with the same player
        i = 0
        while i < len(my_terr_index):
            terr = self._territories[int(my_terr_index[i])]
            border_view = self._territory_owner_array_view[terr.borders]
            #print(terr.name, border_view)
            if not list(np.where(border_view == 0)[0]):
                del my_terr_index[i]
                #print('deleting')
            else:
                i += 1
        
        if not my_terr_index:
            logging.info('Ending turn, No valid territories to reinforce from, moving to next player')
            self.change_player()
            return True
        
        self._model_array[GameState.SelectReiforceSource] = 1
        self._model_array[GameState.SkipReinforcement] = 1
        
        self._input_validation_card_array[...] = 0
        self._input_validation_card_array[my_terr_index] = 1
        
        self.update_text('Ending turn, Select territory to reiforce from or skip')
        return True

    def SkipReinforcement(self):
        
        if not self._return_array_gs_view[GameState.SkipReinforcement]:
            return False
        
        self._model_array[GameState.SkipReinforcement] = 0
        self._model_array[GameState.SelectReiforceSource] = 0
        
        self.update_text('Skipping reiforcement')
        
        self.change_player()
        return True

    def SelectReiforceDestination(self):

        if not self._return_array_gs_view[GameState.SelectReiforceDestination]:
            return False
        
        self._model_array[GameState.SelectReiforceDestination] = 0
        dest_index = np.where(self._return_array_card_view != 0)[0]
        source_index = np.where(self._territory_owner_array_view > MAX_PLAYERS)[0]
        
        # Dont want to actually move any troops
        if not list(dest_index):
            self.update_text('Decided not to move any troops')
            self._territory_owner_array_view[source_index] = 0
            self.change_player()
            return True
        
        dest_index = dest_index[0]
        if not list(source_index) or len(list(source_index)) > 1:
            print(self._model_array, source_index)
            raise Exception('Invalid setup during SelectReiforceDestination')
        
        source_index = source_index[0]
        max_troops_to_move = self._territory_troop_array_view[source_index] - 1
        troops_to_move = math.ceil(self._return_array_card_view[dest_index] * max_troops_to_move)
        
        self._territory_owner_array_view[source_index] = 0
        self._territory_troop_array_view[source_index] -= troops_to_move
        self._territory_troop_array_view[dest_index] += troops_to_move
        
        self.update_text('Moved {} troop(s) from {} to {}'.format( \
            troops_to_move, self._territories[source_index].name, self._territories[dest_index].name))
        
        self.change_player()
        return True

    def SelectReiforceSource(self):
        
        if not self._return_array_gs_view[GameState.SelectReiforceSource]:
            return False
        
        self._model_array[GameState.SkipReinforcement] = 0
        self._model_array[GameState.SelectReiforceSource] = 0
        
        terr_index = np.where(self._return_array_card_view != 0)[0]
        
        # Dont want to actually move any troops
        if not list(terr_index):
            self.change_player()
            return True
        
        terr_index = terr_index[0]
        self._territory_owner_array_view[terr_index] = EXTRA_ENUM_OFFSET
        max_troops_to_move = self._territory_troop_array_view[terr_index] - 1
        
        self._model_array[GameState.SelectReiforceDestination] = max_troops_to_move
        
        self._input_validation_card_array[...] = 0
        self.update_validate_array_from_borders(terr_index)
        
        self.update_text('Moving troops from {}, select destination'.format(self._territories[terr_index].name))
        return True

    def TurnInCards(self):
        
        if not self._return_array_gs_view[GameState.TurnInCards]:
            return False
        
        self._model_array[GameState.TurnInCards] = 0
        self._model_array[GameState.StartTroopPlacement] = 0
        self.init_select_card()
        return True
    
    def SelectCard(self):
        
        if not self._return_array_gs_view[GameState.SelectCard]:
            return False
        
        card_index = list(np.where(self._return_array_card_view != 0)[0])
        if len(card_index) != 1:
            raise Exception('Invalid return_array in SelectCard')
        
        card_index = card_index[0]
        prev_card_index = np.where(self._territory_card_array_view > MAX_PLAYERS)[0]
        new_entry = len(list(prev_card_index)) + 1
        
        self._territory_card_array_view[card_index] = new_entry + EXTRA_ENUM_OFFSET
        
        if card_index < len(self._territories):
            terr = self._territories[card_index]
            self.update_text('Selected Card {} - {}, Index: {}, Value {}'.format(new_entry, terr.name, card_index, terr.card_value))
        else:
            self.update_text('Selected Card {} - Wild'.format(new_entry))
        
        if new_entry == 3:
            self.turn_in_cards()
            return True
        
        self.init_select_card(list(prev_card_index) + [card_index])
        return True
   
   # HELPER FUNCTIONS 
    
    def random_initialization(self):
            
        logging.debug('Calling random_initialization for {} players'.format(len(self.players)))
            
        start_armies = 40 - 5 * (len(self.players) - 2)

        for _ in range(start_armies):
            for i, p in enumerate(self.players):
                unit_terr = list(np.where(self._territory_owner_array_view == UNINIT)[0])
                if unit_terr:
                    terr = random.choice(unit_terr)
                    self._territory_owner_array_view[terr] = i
                    self._territory_troop_array_view[terr] = 1
                    terr_obj = self._territories[terr]
                    logging.debug('Adding {} to {} control in random_initialization'.format(terr_obj.name, p.name))
                else:
                    my_terr = list(np.where(self._territory_owner_array_view == i)[0])
                    terr = random.choice(my_terr)
                    self._territory_troop_array_view[terr] += 1
    
    def init_start_turn(self):
        
        #print(self._model_array)
        self._model_array[GameState.StartTurn] = 1
        self._model_array[self._territory_conquered_index] = 0
        card_index = np.where(self._territory_card_array_view == 0)[0]
        #print(self._territory_card_array_view, card_index)
        self.update_text('Current Player Turn: {}, {} cards'.format(self.players[0].name, len(card_index)))
    
    def init_place_troops(self):
        
        self._model_array[GameState.SelectCard] = 0
        
        self._input_validation_card_array[...] = 0
        self._input_validation_card_array[np.where(self._territory_owner_array_view == 0)[0]] = 1
        self.update_text('{} has {} troops to place'.format(self.players[0].name, int(self._model_array[GameState.PlaceTroops])))
    
    def init_turn_in_cards(self):
        
        # Check how many cards current player has
        card_index = list(np.where(self._territory_card_array_view == 0)[0])
        
        if len(card_index) < 3:
            return False
        
        # Have to turn in cards, go straight to card selection
        if len(card_index) >= MAX_CARDS:
            self.init_select_card()
            return True

        for c in combinations(card_index, 3):
            if self.card_combo_valid(c):
                # Just need one valid combo to know its OK for TurnInCards
                self._model_array[GameState.TurnInCards] = 1
                return True

    def new_troops(self):
        
        # territory Count Troops
        my_territories = list(np.where(self._territory_owner_array_view == 0)[0])
        troops = int(len(my_territories) / 3)
        if troops < 3:
            troops = 3
            
        logging.debug(' {} territory troops'.format(troops))
        # Continent Bonus
        for n, cont in self._continents.items():
            if cont <= set(my_territories):
                cont_troops = int(n[-1])
                logging.debug(' {} troops for {}'.format(cont_troops, n[:-1]))
                troops += cont_troops
                
        return troops
   
    def init_attack_from(self):
        
        self._model_array[GameState.EndTurn] = 1
        
        self._input_validation_card_array[...] = 0        
        self._input_validation_card_array[np.where(self._territory_owner_array_view == 0)[0]] = 1
        
        # Cant attack from single troop countries
        self._input_validation_card_array[np.where(self._territory_troop_array_view == 1)[0]] = 0
        
        # Cant attack from a territory completely surrounded by our own
        potential_attack_locations = np.where(self._input_validation_card_array == 1)[0]
        for i in potential_attack_locations:
            border_array = self._territory_owner_array_view[self._territories[i].borders]
            attackable = np.where(border_array > 0)[0]
            if not list(attackable):
                self._input_validation_card_array[i] = 0
        
        if list(np.where(self._input_validation_card_array == 1)[0]):
            self._model_array[GameState.SelectAttackingTerritory] = 1
        else:
            self.update_text('No more valid territories to attack from, time to end your turn')
            
    def execute_attack(self, attack_index, defend_index, attack_lost, defend_lost, attackers_last_used):
        
        #logging.debug('{} is defending'.format(self._territories[defend_index].name))

        attack_troops_used = int(self._territory_owner_array_view[attack_index] - EXTRA_ENUM_OFFSET)
        defend_troops_used = int(min(2, self._territory_troop_array_view[defend_index]))
        
        if attack_troops_used == BLITZ_VALUE:
            while self._territory_troop_array_view[defend_index] and self._territory_troop_array_view[attack_index] > 1:
                attack_troops_used = int(min(3, self._territory_troop_array_view[attack_index] - 1))
                defend_troops_used = int(min(2, self._territory_troop_array_view[defend_index]))
                self.execute_single_attack(attack_index, attack_troops_used, defend_index, defend_troops_used, attack_lost, defend_lost)
        else:
            self.execute_single_attack(attack_index, attack_troops_used, defend_index, defend_troops_used, attack_lost, defend_lost)
            
        attackers_last_used[0] = attack_troops_used
    
    def execute_single_attack(self, attack_index, attack_troops_used, defend_index, defend_troops_used, attack_lost, defend_lost):
        
        attack_list = sorted([random.randint(1, 6) for _ in range(attack_troops_used)], reverse = True)
        defend_list = sorted([random.randint(1, 6) for _ in range(defend_troops_used)], reverse = True)
        
        for i in range(min(attack_troops_used, defend_troops_used)):
            if attack_list[i] > defend_list[i]:
                self._territory_troop_array_view[defend_index] -= 1
                defend_lost[0] += 1
            else:
                self._territory_troop_array_view[attack_index] -= 1
                attack_lost[0] += 1
            
    def change_player(self):
        
        # Move current player to num_players + 1 so subtracting moves back to last
        self._territory_owner_array_view[np.where(self._territory_owner_array_view == 0)[0]] = len(self.players)
        self._territory_card_array_view [np.where(self._territory_card_array_view == 0) [0]] = len(self.players)
        self._territory_owner_array_view -= 1
        self._territory_card_array_view[self._territory_card_array_view > 0]  -= 1
            
        # Move current player to back of the line
        self.players.append(self.players.pop(0))
        self.update_alliance_data()
        
        self.init_start_turn()
     
    def update_validate_array_from_borders(self, terr_index):
        
        for ti in self._territories[terr_index].borders:
            # Already added
            if self._input_validation_card_array[ti] == 1:
                continue
            
            # Other owner or the source
            if self._territory_owner_array_view[ti]:
                continue
            
            self._input_validation_card_array[ti] = 1
            self.update_validate_array_from_borders(ti)
        
    def card_combo_valid(self, combo):
        
        wild_count = 0
        out_set = set()
        
        for c in combo:
            if c >= len(self._territories):
                wild_count += 1
                continue
            
            out_set.add(self._territories[c].card_value[-1])
            
        if len(out_set) == 2 and not wild_count:
            return 0
        
        if len(out_set) == 3 or wild_count == 2 or (len(out_set) == 2 and wild_count == 1):
            return 10
        
        if len(out_set) == 1:
            return int(list(out_set)[0])
        
        print (out_set, wild_count)
        raise Exception('HERE')
    
    def init_select_card(self, prev_selected = []):
        
        self._model_array[GameState.SelectCard] = 1
        
        card_index = list(np.where(self._territory_card_array_view == 0)[0])

        self._input_validation_card_array[...] = 0        
        
        for c in combinations(card_index, 3 - len(prev_selected)):
            if self.card_combo_valid(list(c) + prev_selected):
                self._input_validation_card_array[list(c)] = 1
    
    def turn_in_cards(self):
        
        cards_to_turn_in = list(np.where(self._territory_card_array_view > MAX_PLAYERS)[0])
        
        if len(cards_to_turn_in) != 3:
            raise Exception('turn in cards called, but cards_to_turn_in size: {}'.format(len(cards_to_turn_in)))
    
        extra_troops = self.card_combo_valid(cards_to_turn_in)
        
        if not extra_troops:
            print(cards_to_turn_in)
            raise Exception('Invalid card combo in turn in cards')
        
        self._model_array[GameState.PlaceTroops] += extra_troops
        self.update_text('{} troops from turning in cards'.format(extra_troops))
        
        first_card = np.where(self._territory_card_array_view == (EXTRA_ENUM_OFFSET + 1))[0][0]
        if first_card < len(self._territories) and not self._territory_owner_array_view[first_card]:
            #self._model_array[GameState.PlaceTroops] += 2
            self._territory_troop_array_view[first_card] += 2
            self.update_text('2 bonus troops from turning owning {}'.format(self._territories[first_card].name))
        
        self._territory_card_array_view[cards_to_turn_in] = TURNED_IN
        
        remaining_cards = list(np.where(self._territory_card_array_view == 0)[0])
        # From a takeover, need to get back down under 
        if len(remaining_cards) > MAX_CARDS:
            #raise Exception('HERE')
            self.update_text('Still have too many cards, keep turning them in')
            self.init_select_card()
            return
        
        # Down below limit, we can move on to placing troops
        self._model_array[GameState.SelectCard] = 0
        self._model_array[GameState.PlaceTroops] += self._post_card_territory_troops
        
        self.init_place_troops()
        return True
    
    def elimate_player(self, player_index):
        
        player_cards = np.where(self._territory_card_array_view == player_index)[0]
        self._territory_card_array_view[player_cards] = 0
        
        self.update_text('{} ({}) elimated from game, {} receives {} cards'.format( \
            self.players[player_index].name, player_index, self.players[0].name, len(player_cards)))
        
        #print(player_index, self._territory_owner_array_view)
        self._territory_owner_array_view[self._territory_owner_array_view > player_index] -= 1
        self._territory_card_array_view[self._territory_card_array_view > player_index] -= 1
        #print(player_index, self._territory_owner_array_view)
        
        self.players.pop(player_index)
        
        if len(self.players) == 1:
            self.update_text('{} wins'.format(self.players[0].name))
            self._model_array[GameState.GameOver] = 1
            return
        
       
        new_player_cards = list(np.where(self._territory_card_array_view == 0)[0])
        #print(self._territory_card_array_view, new_player_cards) 
        self.update_text('{} now has {} cards'.format( \
            self.players[0].name, len(new_player_cards)))
        if len(new_player_cards) > MAX_CARDS:
            #print(len(new_player_cards), self._model_array, self._model_array[GameState.SelectAttackingTerritory])
            #raise Exception('Implement elimiation card turn in')
            self._post_card_territory_troops = 0
            self.init_select_card()
        else:
            self.init_attack_from()
    
    def update_alliance_data(self):
        
        alliance_states = np.where(self._alliance_array_view > 0)[0]
        
        # If no alliance set, no need to do anything
        if not list(alliance_states):
            return
            
        raise Exception('Implement update_alliance_data')
    ''''        
    def changeable_alliances(self, set_state=False):
        
        for i in range(MAX_PLAYERS):
            if self._alliance_array_view[i] > 0
    '''        
    def get_border_dist(self, terr_index):
        
        border_dist = defaultdict(list)
        
        for i in self._territories[terr_index].borders:
            border_dist[self._territory_owner_array_view[i]].append(i)
            
        return border_dist
    '''
    def SelectMap(self):
        
        if not self._return_array_gs_view[GameState.SelectMap] or not self._map_name:
            return False
        
        #We have a map_name and are being told it was just entered
        
        # No need to enter any more maps
        self._model_array[GameState.SelectMap] = 0
        
        # If we have atleast 2 players, we can start the game
        if len(self.players) > 1:
            self._model_array[GameState.StartGame] = 1
            self._input_validation_array[GameState.StartGame] = 1
            
        return True
    
    def AddPlayer(self):
        
        if not self._return_array_gs_view[GameState.AddPlayer]:
            return False
        
        # No more players
        if len(self.players) == MAX_PLAYERS:
            self._model_array[GameState.AddPlayer] = 0
            
        # If we have atleast 2 players and a map, we can start the game
        if len(self.players) > 1 and self.map_name:
            self._model_array[GameState.StartGame] = 1
            self._input_validation_array[GameState.StartGame] = 1
            
        logging.debug('Updating model to have {} players'.format(len(self.players)))
        return True
    '''