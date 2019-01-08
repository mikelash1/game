import numpy as np
import math

import random
import logging
from collections import OrderedDict, defaultdict
from enum import Enum
from GameState import GameState, Card
from itertools import combinations

MAX_PLAYERS = 6
MAX_CARDS = 5
UNINIT = -1
TURNED_IN = -2

EXTRA_ENUM_OFFSET = MAX_PLAYERS + 1
BLITZ_VALUE = 4

class Territory:
    def __init__(self, name, borders, card_value):
        self.name = name
        self.borders = borders
        self.card_value = card_value
        
    
class AutoNumber(Enum):
    def __new__(cls):
        value = len(cls.__members__)
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

class GameState(AutoNumber):
    SelectMap = ()
    AddPlayer = ()
    RemovePlayer = ()
    StartGame = ()
    RandomTerritories = ()
    StartTurn = ()
    TurnInCards = ()
    SelectCard = ()
    StartTroopPlacement = ()
    PlaceTroops = ()
    SelectTroopPlacement = ()
    SelectAttackingTerritory = ()
    AttackingTroopCount = ()
    SelectDefendingTerritory = ()
    TakeOverReinforcement = ()
    EndTurn = ()
    SkipReinforcement = ()
    SelectReiforceSource = ()
    SelectReiforceDestination = ()
    GameOver = ()

class risk_model():
 
    def __init__(self, controller):
        self.controller = controller
        self._model_array = np.zeros(len(GameState) + MAX_PLAYERS + 1)
        self._territory_conquered_index = len(GameState)
        
        # Initial states of selecting map and adding players valid
        self._model_array[GameState.SelectMap.value] = 1
        self._model_array[GameState.AddPlayer.value] = 1
        
        self._input_validation_array = self._model_array.copy()
        self._input_validation_array_card_view = None
        
        self._return_array = self._input_validation_array.copy()
        
        self.players = []
        self.territory_owner_start = len(self._model_array)
        self._territory_owner_array_view = None
        self._territory_all_array_view = None
        self.territory_troop_start = -1
        self._territory_troop_array_view = None
        self.territory_card_start = -1
        self._territory_card_array_view = None
        self.map_name = None
        self.turns_started = False
        self._info_text = 'Sample'
        self._info_text_observers = []
        
        self.territories = []
        self.continents = defaultdict(set)
        
        logging.debug('Created model_array with {} elements'.format(len(self._model_array)))
        
    def get_model_data(self):
        
        return_array = self._return_array.copy()
        return_array[...] = 0
        
        return self.create_player_array(), self._input_validation_array.copy(), return_array
    
    def create_player_array(self):
        
        # Until we start taking turns, all data is public, so no need to trim to player version
        player_array = self._model_array.copy()
        
        if not self.turns_started:
            return player_array
        
        # ID how many cards each player has
        for i in range(MAX_PLAYERS):
            player_array[len(GameState) + i + 1] = len(list(np.where(self._territory_card_array_view == i)[0]))
            #print(len(GameState) + i, player_array[len(GameState) + i])
            
        # Hide the identity of the other players cards from current player
        non_player_cards = np.where(self._territory_card_array_view != 0)[0]
        player_array_card_view = player_array[self.territory_card_start:]
        player_array_card_view[non_player_cards] = UNINIT
    
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
    
    def SelectMap(self, return_array):
        
        if not return_array[GameState.SelectMap.value] or not self.map_name:
            return False
        
        #We have a map_name and are being told it was just entered
        
        # No need to enter any more maps
        self._model_array[GameState.SelectMap.value] = 0
        
        # If we have atleast 2 players, we can start the game
        if len(self.players) > 1:
            self._model_array[GameState.StartGame.value] = 1
            
        return True
    
    def AddPlayer(self, return_array):
        
        if not return_array[GameState.AddPlayer.value]:
            return False
        
        # No more players
        if len(self.players) == MAX_PLAYERS:
            self._model_array[GameState.AddPlayer.value] = 0
            
        # If we have atleast 2 players and a map, we can start the game
        if len(self.players) > 1 and self.map_name:
            self._model_array[GameState.StartGame.value] = 1
            
        logging.debug('Updating model to have {} players'.format(len(self.players)))
        return True
    
    def StartGame(self, return_array):
        
        if not return_array[GameState.StartGame.value]:
            return False
        
        self._model_array[GameState.AddPlayer.value] = 0
        self._model_array[GameState.StartGame.value] = 0
        
        # Need to update here is we implement territory selection
        self._model_array[GameState.RandomTerritories.value] = 1
            
        logging.debug('Updating model to start the game')
        return True
    
    def RandomTerritories(self, return_array):
        
        if not return_array[GameState.RandomTerritories.value]:
            return False
        
        self.random_initialization()
        self._model_array[GameState.RandomTerritories.value] = 0
        self.init_start_turn()
        
        self.turns_started = True
        return True
    
    def StartTroopPlacement(self, return_array):
        
        if not return_array[GameState.StartTroopPlacement.value]:
            return False
        
        self._model_array[GameState.TurnInCards.value] = 0
        self._model_array[GameState.StartTroopPlacement.value] = 0
        self._model_array[GameState.PlaceTroops.value] += self.new_troops()
        
        self.init_place_troops()
        return True
    
    def init_place_troops(self):
        
        self._model_array[GameState.SelectCard.value] = 0
        
        self._input_validation_array[...] = 0
        self._input_validation_array[GameState.PlaceTroops.value] = 1
        self._input_validation_array_card_view[np.where(self._territory_owner_array_view == 0)[0]] = 1
        self.update_text('{} has {} troops to place'.format(self.players[0].name, int(self._model_array[GameState.PlaceTroops.value])))
        
    
    def PlaceTroops(self, return_array):
        
        if not return_array[GameState.PlaceTroops.value]:
            return False
        
        self._return_array = return_array
        card_view = self.get_return_array_card_view()
        terr_index = np.where(card_view > 0)[0]
        
        if not list(terr_index):
            raise Exception('No territory passed into PlaceTroops in risk_model')
        
        if self._territory_owner_array_view[terr_index[0]] > 0:
            raise Exception('Territory passed in PlaceTroops in risk_model not owned by current player')
        
        #print(card_view[terr_index[0]], self._model_array[GameState.PlaceTroops.value], int(card_view[terr_index[0]] * self._model_array[GameState.PlaceTroops.value]))
        troops_to_place = int(card_view[terr_index[0]] * self._model_array[GameState.PlaceTroops.value]) + 1
        
        self._territory_troop_array_view[terr_index[0]] += troops_to_place
        text = 'Added {} troop(s) to {}'.format(troops_to_place, self.territories[terr_index[0]].name)
        
        self._model_array[GameState.PlaceTroops.value] -= troops_to_place
        
        if self._model_array[GameState.PlaceTroops.value] > 0:
            text += ', {} has {} troops to place'.format(self.players[0].name, int(self._model_array[GameState.PlaceTroops.value]))
        else:
            self._model_array[GameState.PlaceTroops.value] = 0
            text += ', select a territory to attack from'
            self.init_attack_from()
        
        self.update_text(text)
        
        return True
    
    def init_start_turn(self):
        
        #print(self._model_array)
        self._model_array[GameState.StartTurn.value] = 1
        self._model_array[self._territory_conquered_index] = 0
        num_cards = len(np.where(self._territory_card_array_view == 0)[0])
        self.update_text('Current Player Turn: {}, {} cards'.format(self.players[0].name, num_cards))
        
        self._input_validation_array[...] = 0
        self._input_validation_array[GameState.StartTurn.value] = 1
        #print(self._model_array)
        
    def card_combo_valid(self, combo):
        
        wild_count = 0
        out_set = set()
        
        for c in combo:
            if c >= len(self.territories):
                wild_count += 1
                continue
            
            out_set.add(self.territories[c].card_value[-1])
            
        if len(out_set) == 2 and not wild_count:
            return 0
        
        if len(out_set) == 3 or wild_count == 2 or (len(out_set) == 2 and wild_count == 1):
            return 10
        
        if len(out_set) == 1:
            return int(list(out_set)[0])
        
        print (out_set, wild_count)
        raise Exception('HERE')
        
    def init_turn_in_cards(self):
        
        # Check how many cards current player has
        card_index = list(np.where(self._territory_card_array_view == 0)[0])
        
        if len(card_index) < 3:
            return False
        
        # Have to turn in cards, go straight to placement
        if len(card_index) >= MAX_CARDS:
            self.init_select_card()
            return True

        for c in combinations(card_index, 3):
            if self.card_combo_valid(c):
                # Just need one valid combo to know its OK for TurnInCards
                self._model_array[GameState.TurnInCards.value] = 1
                return False
            
    def init_select_card(self, prev_selected = []):
        
        self._model_array[GameState.SelectCard.value] = 1
        
        card_index = list(np.where(self._territory_card_array_view == 0)[0])
        self._input_validation_array[...] = 0        
        self._input_validation_array[GameState.SelectCard.value] = 1
        
        for c in combinations(card_index, 3 - len(prev_selected)):
            if self.card_combo_valid(list(c) + prev_selected):
                self._input_validation_array_card_view[list(c)] = 1
            
    def TurnInCards(self, return_array):
        
        if not return_array[GameState.TurnInCards.value]:
            return False
        
        self._model_array[GameState.TurnInCards.value] = 0
        self._model_array[GameState.StartTroopPlacement.value] = 0
        self.init_select_card()
        return True
    
    def turn_in_cards(self):
        
        cards_to_turn_in = list(np.where(self._territory_card_array_view > MAX_PLAYERS)[0])
        
        if len(cards_to_turn_in) != 3:
            raise Exception('turn in cards called, but cards_to_turn_in size: {}'.format(len(cards_to_turn_in)))
    
        extra_troops = self.card_combo_valid(cards_to_turn_in)
        
        if not extra_troops:
            print(cards_to_turn_in)
            raise Exception('Invalid card combo in turn in cards')
        
        self._model_array[GameState.PlaceTroops.value] += extra_troops
        self.update_text('{} troops from turning in cards'.format(extra_troops))
        
        first_card = np.where(self._territory_card_array_view == (EXTRA_ENUM_OFFSET + 1))[0][0]
        if first_card < len(self.territories) and not self._territory_owner_array_view[first_card]:
            #self._model_array[GameState.PlaceTroops.value] += 2
            self._territory_troop_array_view[first_card] += 2
            self.update_text('2 bonus troops from turning owning {}'.format(self.territories[first_card].name))
        
        self._territory_card_array_view[cards_to_turn_in] = TURNED_IN
        
        remaining_cards = list(np.where(self._territory_card_array_view == 0)[0])
        # From a takeover, need to get back down under 
        if len(remaining_cards) > MAX_CARDS:
            self.init_select_card()
            return
        
        # Down below limit, we can move on to placing troops
        self._model_array[GameState.SelectCard.value] = 0
        self._model_array[GameState.StartTroopPlacement.value] = 1
    
    def SelectCard(self, return_array):
        
        if not return_array[GameState.SelectCard.value]:
            return False
        
        work_array = self.get_return_array_card_view(return_array)
        card_index = list(np.where(work_array != 0)[0])
        if len(card_index) != 1:
            raise Exception('Invalid return_array in SelectCard')
        
        card_index = card_index[0]
        prev_card_index = np.where(self._territory_card_array_view > MAX_PLAYERS)[0]
        new_entry = len(list(prev_card_index)) + 1
        
        self._territory_card_array_view[card_index] = new_entry + EXTRA_ENUM_OFFSET
        
        if card_index < len(self.territories):
            terr = self.territories[card_index]
            self.update_text('Selected Card {} - {}: {}'.format(new_entry, terr.name, terr.card_value))
        else:
            self.update_text('Selected Card {} - Wild'.format(new_entry))
        
        if new_entry == 3:
            self.turn_in_cards()
            return True
        
        self.init_select_card(list(prev_card_index) + [card_index])
        return True

    def StartTurn(self, return_array):
        
        if not return_array[GameState.StartTurn.value]:
            return False
        
        self._model_array[GameState.StartTurn.value] = 0
        
        if self.init_turn_in_cards():
            return True
        
        self._model_array[GameState.StartTroopPlacement.value] = 1
        
        return True
    
    def init_attack_from(self):
        
        self._model_array[GameState.EndTurn.value] = 1
        
        self._input_validation_array[...] = 0        
        self._input_validation_array[GameState.EndTurn.value] = 1
        self._input_validation_array_card_view[np.where(self._territory_owner_array_view == 0)[0]] = 1
        
        # Cant attack from single troop countries
        self._input_validation_array_card_view[np.where(self._territory_troop_array_view == 1)[0]] = 0
        
        # Cant attack from a territory completely surrounded by our own
        potential_attack_locations = np.where(self._input_validation_array_card_view == 1)[0]
        for i in potential_attack_locations:
            border_array = self._territory_owner_array_view[self.territories[i].borders]
            attackable = np.where(border_array > 0)[0]
            if not list(attackable):
                self._input_validation_array_card_view[i] = 0
        
        if list(np.where(self._input_validation_array_card_view == 1)[0]):
            self._model_array[GameState.SelectAttackingTerritory.value] = 1
            self._input_validation_array[GameState.SelectAttackingTerritory.value] = 1
        else:
            self.update_text('No more valid territories to attack from, time to end your turn')
    
    def SelectAttackingTerritory(self, return_array):
        
        if not return_array[GameState.SelectAttackingTerritory.value]:
            return False
        
        work_array = self.get_return_array_card_view(return_array)
        
        attack_terr_index = np.where(work_array != 0)[0]
        if len(list(attack_terr_index)) != 1:
            raise Exception('Invalid return_array in SelectAttackingTerritory')
        
        attack_terr_index = attack_terr_index[0]
        
        attack_troops_to_use = BLITZ_VALUE
        if work_array[attack_terr_index] < 1:
            attack_troop_options = list(range(1, min(4, self._territory_troop_array_view[attack_terr_index] + 1)))
            attack_troop_options.append(BLITZ_VALUE)
            attack_troops_to_use_index = int(len(attack_troop_options) * work_array[attack_terr_index])
            attack_troops_to_use = attack_troop_options[attack_troops_to_use_index]
            
        if attack_troops_to_use == BLITZ_VALUE:
            self.update_text('{} is blitzing from {}, select territory to attack'. \
            format(self.players[0].name, self.territories[attack_terr_index].name))
        else:
            self.update_text('{} is attacking from {} with {} troop(s), select territory to attack'. \
                format(self.players[0].name, self.territories[attack_terr_index].name, attack_troops_to_use))
        
        self._territory_owner_array_view[attack_terr_index] = attack_troops_to_use + EXTRA_ENUM_OFFSET
        self._model_array[GameState.SelectAttackingTerritory.value] = 0
        self._model_array[GameState.EndTurn.value] = 0
        self._model_array[GameState.SelectDefendingTerritory.value] = 1
        
        self._input_validation_array[...] = 0
        self._input_validation_array[GameState.SelectDefendingTerritory.value] = 1
        self._input_validation_array_card_view[self.territories[attack_terr_index].borders] = 1
        # Cant attack ourselves
        self._input_validation_array_card_view[np.where(self._territory_owner_array_view == 0)[0]] = 0
        
        return True
    
    def SelectDefendingTerritory(self, return_array):
        
        if not return_array[GameState.SelectDefendingTerritory.value]:
            return False
        
        work_array = self.get_return_array_card_view(return_array)
        
        defend_terr_index = np.where(work_array != 0)[0]
        if len(list(defend_terr_index)) != 1:
            print(return_array, work_array)
            raise Exception('Invalid return_array in SelectDefendingTerritory')
        
        defend_terr_index = defend_terr_index[0]
        
        attack_index = np.where(self._territory_owner_array_view > MAX_PLAYERS)[0]
        if len(list(attack_index)) != 1:
            print(self._model_array)
            print(self._territory_owner_array_view)
            raise Exception('Invalid attack_index for execute_attack')
        
        attack_index = attack_index[0]
        
        attack_lost = [0]
        defend_lost = [0]
        attackers_last_used = [0]
        self.execute_attack(attack_index, defend_terr_index, attack_lost, defend_lost, attackers_last_used)
        
        text_str = '{} lost {} troop(s), {} lost {} troop(s)'.format( \
            self.territories[attack_index].name, attack_lost[0], \
            self.territories[defend_terr_index].name, defend_lost[0])
        
        self._model_array[GameState.SelectDefendingTerritory.value] = 0
        
        # Territory defended, just start over with attacking
        if self._territory_troop_array_view[defend_terr_index] > 0:
            self._territory_owner_array_view[attack_index] = 0
            self.update_text(text_str + ', {} failed to take over {}, select next territory to attack from'. \
                format(self.players[0].name, self.territories[defend_terr_index].name))
            self.init_attack_from()
            return True
        
        # Territory taken over
        self._input_validation_array[...] = 0
        self._input_validation_array[GameState.TakeOverReinforcement.value] = attackers_last_used[0]
        self._model_array[GameState.TakeOverReinforcement.value] = 1
        self.update_text(text_str + ', {} took over {} from {}, select how many troops move'. \
                format(self.players[0].name, self.territories[defend_terr_index].name, self.territories[attack_index].name))
           
        return True
    
    def execute_attack(self, attack_index, defend_index, attack_lost, defend_lost, attackers_last_used):
        
        logging.debug('{} is defending'.format(self.territories[defend_index].name))

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
    
    def TakeOverReinforcement(self, return_array):
        
        if not return_array[GameState.TakeOverReinforcement.value]:
            return False
        
        attack_index = np.where(self._territory_owner_array_view > MAX_PLAYERS)[0]
        if len(list(attack_index)) != 1:
            raise Exception('Invalid attack_index for TakeOverReinforcement')
        
        attack_index = attack_index[0]
        
        defend_index = np.where(self._territory_troop_array_view == 0)[0]
        if len(list(defend_index)) != 1:
            raise Exception('Invalid defend_index for TakeOverReinforcement')
        
        defend_index = defend_index[0]
        
        max_troops_to_move = self._territory_troop_array_view[attack_index] - 1
        troops_to_move = int(max_troops_to_move * return_array[GameState.TakeOverReinforcement.value]) + 1
        
        self.update_text('{} moved {} troop(s) from {} to {}, select next territory to attack from'. \
             format(self.players[0].name, troops_to_move, self.territories[attack_index].name, \
            self.territories[defend_index].name))
        
        old_owner = int(self._territory_owner_array_view[defend_index])
        self._territory_troop_array_view[attack_index] -= troops_to_move
        self._territory_troop_array_view[defend_index] += troops_to_move
        
        self._territory_owner_array_view[attack_index] = 0
        self._territory_owner_array_view[defend_index] = 0
        
        self._model_array[self._territory_conquered_index] = 1
        self._model_array[GameState.TakeOverReinforcement.value] = 0
        
        old_owner_terr = np.where(self._territory_owner_array_view == old_owner)[0]
        if not list(old_owner_terr):
            self.elimate_player(old_owner)
            return True
            
        self.init_attack_from()
        
        #print(self._model_array)
        return True
    
    def elimate_player(self, player_index):
        
        player_cards = np.where(self._territory_card_array_view == player_index)[0]
        self._territory_card_array_view[player_cards] = 0
        
        self.update_text('{} elimated from game, {} receives {} cards'.format( \
            self.players[player_index].name, self.players[0].name, len(player_cards)))
        
        self.players.pop(player_index)
        
        if len(self.players) == 1:
            self.update_text('{} wins'.format(self.players[0].name))
            self._model_array[GameState.GameOver.value] = 1
            return
        
        new_player_cards = list(np.where(self._territory_card_array_view == 0)[0])
        if len(new_player_cards) > MAX_CARDS:
            #print(len(new_player_cards), self._model_array, self._model_array[GameState.SelectAttackingTerritory.value])
            #raise Exception('Implement elimiation card turn in')
            self.init_select_card()
        else:
            self.init_attack_from()
    
    def change_player(self):
        
        # Move current player to num_players + 1 so subtracting moves back to last
        #print(self._model_array)
        self._territory_all_array_view[np.where(self._territory_all_array_view == 0)[0]] = len(self.players)
        self._territory_owner_array_view[np.where(self._territory_owner_array_view > 0)[0]] -= 1
        self._territory_card_array_view[np.where(self._territory_card_array_view > 0)[0]] -= 1
        #print(self._model_array)
            
        # Move current player to back of the line
        self.players.append(self.players.pop(0))
        
        self.init_start_turn()
    
    def EndTurn(self, return_array):
        
        if not return_array[GameState.EndTurn.value]:
            return False
        
        # Took over atleast one territory, we get a card
        if self._model_array[self._territory_conquered_index]:
            free_card_index = list(np.where(self._territory_card_array_view == UNINIT)[0])
            if not free_card_index:
                free_card_index = list(np.where(self._territory_card_array_view == TURNED_IN)[0])
                self._territory_card_array_view[free_card_index] = UNINIT
                #print(self._model_array)

            self._territory_card_array_view[random.choice(free_card_index)] = 0
               
        self._model_array[GameState.SelectAttackingTerritory.value] = 0
        self._model_array[GameState.EndTurn.value] = 0
        
        # Make sure we have a valid territory that could supply troops
        # Has more than one troop
        #print(self._model_array)
        #print(self._territory_owner_array_view)
        #print(np.where(self._territory_owner_array_view == 0))
        my_terr_index = list(np.where((self._territory_owner_array_view == 0) & (self._territory_troop_array_view > 1))[0])
        #print(my_terr_index)
        
        # make sure each has a border with the same player
        i = 0
        while i < len(my_terr_index):
            terr = self.territories[int(my_terr_index[i])]
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
        
        self._model_array[GameState.SelectReiforceSource.value] = 1
        self._model_array[GameState.SkipReinforcement.value] = 1
        
        self._input_validation_array[...] = 0
        self._input_validation_array[GameState.SelectReiforceSource.value] = 1
        self._input_validation_array[GameState.SkipReinforcement.value] = 1
        self._input_validation_array_card_view[my_terr_index] = 1
        
        self.update_text('Ending turn, Select territory to reiforce from or skip')
        return True

    def SelectReiforceSource(self, return_array):
        
        if not return_array[GameState.SelectReiforceSource.value]:
            return False
        
        self._model_array[GameState.SkipReinforcement.value] = 0
        self._model_array[GameState.SelectReiforceSource.value] = 0
        work_array = self.get_return_array_card_view(return_array)
        
        terr_index = np.where(work_array != 0)[0]
        
        # Dont want to actually move any troops
        if not list(terr_index):
            self.change_player()
            return True
        
        terr_index = terr_index[0]
        max_troops_to_move = self._territory_troop_array_view[terr_index] - 1
        troops_to_move = math.ceil(work_array[terr_index] * max_troops_to_move)
        self._territory_owner_array_view[terr_index] = troops_to_move + EXTRA_ENUM_OFFSET
        
        self._model_array[GameState.SelectReiforceDestination.value] = 1
        
        self._input_validation_array[...] = 0
        self._input_validation_array[GameState.SelectReiforceDestination.value] = 1
        self.update_validate_array_from_borders(terr_index)
        
        self.update_text('Moving {} troop(s) from {}, select destination'.format(troops_to_move, self.territories[terr_index].name))
        return True

    def update_validate_array_from_borders(self, terr_index):
        
        for ti in self.territories[terr_index].borders:
            # Already added
            if self._input_validation_array_card_view[ti] == 1:
                continue
            
            # Other owner or the source
            if self._territory_owner_array_view[ti]:
                continue
            
            self._input_validation_array_card_view[ti] = 1
            self.update_validate_array_from_borders(ti)

    def SkipReinforcement(self, return_array):
        
        if not return_array[GameState.SkipReinforcement.value]:
            return False
        
        self._model_array[GameState.SkipReinforcement.value] = 0
        self._model_array[GameState.SelectReiforceSource.value] = 0
        
        self.update_text('Skipping reiforcement')
        
        self.change_player()
        return True

    def SelectReiforceDestination(self, return_array):
        
        if not return_array[GameState.SelectReiforceDestination.value]:
            return False
        
        self._model_array[GameState.SelectReiforceDestination.value] = 0
        work_array = self.get_return_array_card_view(return_array)
        dest_index = np.where(work_array != 0)[0]
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
        troops_to_move = int(self._territory_owner_array_view[source_index]) - EXTRA_ENUM_OFFSET
        
        self._territory_owner_array_view[source_index] = 0
        self._territory_troop_array_view[source_index] -= troops_to_move
        self._territory_troop_array_view[dest_index] += troops_to_move
        
        self.update_text('Moved {} troop(s) from {} to {}'.format( \
            troops_to_move, self.territories[source_index].name, self.territories[dest_index].name))
        
        self.change_player()
        return True
    
    def handle_return_array(self, return_array):
        
        #logging.debug('Updating model in handle_return_array')
        #print(return_array)
        return_array_gs_view = return_array[:len(GameState)]
        valid_returns = sorted(list(np.where(return_array_gs_view > 0)[0]), key=lambda x: return_array[x], reverse = True)
        
        if not valid_returns:
            raise Exception('Invalid return array passed to risk_model')
            
        gs = [gs for gs in GameState if gs.value == valid_returns[0]][0]
        if hasattr(self, gs.name):
            if getattr(self, gs.name)(return_array):
                return
            else:
                print(return_array)
                raise Exception('Unable to handle {} in model'.format(gs.name))
        else:
            raise Exception('Need to add {} handler in model'.format(gs.name))
        
    def set_map(self, map_name):
        
        self.map_name = map_name
        logging.debug('Setting map to {} in model'.format(self.map_name))
        
        with open('{}/Territories.txt'.format(self.map_name), 'r') as fid:
            for l in fid.readlines():
                parts = l.strip().split()
                new_terr = Territory(parts[0], parts[2:-1], parts[-1])
                self.continents[parts[1]].add(len(self.territories))
                self.territories.append(new_terr)
            
        for t in self.territories:
            t.borders = [i for t2 in t.borders for i, t3 in enumerate(self.territories) if t2 == t3.name]
            
        # Need to resize _model_array, 1..N for onwer, troop count, card holder, plus 2 for 2 extra wild cards
        new_array = np.zeros(len(self.territories) * 3 + 2)
        new_array.fill(UNINIT)
        self._model_array = np.concatenate((self._model_array, new_array), axis = 0)
        self.territory_troop_start = self.territory_owner_start + len(self.territories)
        self.territory_card_start = self.territory_troop_start + len(self.territories)
        self._territory_owner_array_view = self._model_array[self.territory_owner_start:self.territory_troop_start:1]
        self._territory_all_array_view = self._model_array[self.territory_owner_start:]
        self._territory_troop_array_view = self._model_array[self.territory_troop_start:self.territory_card_start:1]
        self._territory_card_array_view = self._model_array[self.territory_card_start:]
        
        new_validation_array = np.zeros(len(self.territories) + 2)
        self._input_validation_array = np.concatenate((self._input_validation_array, new_validation_array), axis = 0)
        self._input_validation_array_card_view = self._input_validation_array[self.territory_owner_start:]
        
        self._return_array = np.concatenate((self._return_array, new_validation_array), axis = 0)
        
        logging.debug('New _model_array size is {}'.format(len(self._model_array)))
        
    def get_return_array_card_view(self, return_array = None):
        
        if not return_array is None:
            return return_array[self.territory_owner_start:]
        
        return self._return_array[self.territory_owner_start:]
            
    def add_player(self, player):
        self.players.append(player)
        
    def new_troops(self):
        
        # territory Count Troops
        my_territories = list(np.where(self._territory_owner_array_view == 0)[0])
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
            
        logging.debug('Calling random_initialization for {} players'.format(len(self.players)))
            
        start_armies = 40 - 5 * (len(self.players) - 2)

        for _ in range(start_armies):
            for i, p in enumerate(self.players):
                unit_terr = list(np.where(self._territory_owner_array_view == UNINIT)[0])
                if unit_terr:
                    terr = random.choice(unit_terr)
                    self._territory_owner_array_view[terr] = i
                    self._territory_troop_array_view[terr] = 1
                    terr_obj = self.territories[terr]
                    logging.debug('Adding {} to {} control in random_initialization'.format(terr_obj.name, p.name))
                else:
                    my_terr = list(np.where(self._territory_owner_array_view == i)[0])
                    terr = random.choice(my_terr)
                    self._territory_troop_array_view[terr] += 1
                    