import tkinter as Tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import cv2
import numpy as np
from PIL import ImageTk, Image
import logging
from risk_model import GameState, UNINIT, MAX_PLAYERS
from time import sleep
import math
import matplotlib as plt
from email.policy import default

RECHECK_TIME = 500

def img(cv2image):
    return ImageTk.PhotoImage(Image.fromarray(cv2image))

class territory_image():
    def __init__(self, board, name, card_value):
        self.name = name
        self.card_value = card_value
        image_name = '{}/{}.png'.format(board, name)
        self.image = cv2.imread(image_name, cv2.IMREAD_GRAYSCALE)
        self.outline = cv2.Canny(self.image,100,200)
        M = cv2.moments(self.image)
        self.cX = int(M["m10"] / M["m00"])
        self.cY = int(M["m01"] / M["m00"])
        
        #logging.debug('Territory {} has center {} {}'.format(name, self.cX, self.cY))

class RightSidePanel():
    def __init__(self, root):
        self.frame = Tk.Frame( root )
        self.frame.pack(side=Tk.RIGHT, fill=Tk.BOTH, expand=1)
        self.buttons = {}
        
    def add_button(self, text, bind_func):
        
        button = Tk.Button(self.frame, text=text)
        button.pack(side="top",fill=Tk.BOTH)
        button.bind("<Button>", bind_func)
        button.pack_forget()
        self.buttons[text] = button

class LeftSidePanel():
    def __init__(self, root):
        self.frame = Tk.Frame( root )
        self.frame.pack(side=Tk.LEFT, fill=Tk.BOTH, expand=1)
        self.labels = []
        
        self.leftsubframe = Tk.Frame(self.frame)
        self.leftsubframe.pack(side=Tk.LEFT, fill=Tk.BOTH, expand=1)
        
        self.rightsubframe = Tk.Frame(self.frame)
        self.rightsubframe.pack(side=Tk.LEFT, fill=Tk.BOTH, expand=1)
        
        self.labels = []
        
    def reset_labels(self, num_terr):
        
        if len(self.labels) == num_terr:
            return
        
        self.labels = []
        
    def update_label(self, i, p, text, left=True):
        
        while len(self.labels) <= i:
            label = None
            if left:
                label = Tk.Label(self.leftsubframe)
            else:
                label = Tk.Label(self.rightsubframe)
            self.labels.append(label)
            
        label = self.labels[i]
        label.config(text = text, bg = p.color.lighthex, fg = p.color.darkhex)
        #label.config(text = text, bg = p.color.lighthex, fg = p.color.darkhex, font=("Courier", 6))
        label.pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)

class BottomPanel():
    def __init__(self, root):
        self.root = root
        self.frame3 = Tk.Frame(self.root)
        self.frame3.pack(side=Tk.BOTTOM, fill=Tk.BOTH, expand=1)
        self.labels = []
        
    def reset_labels(self, num_players):
        
        if len(self.labels) == num_players:
            return

        for l in self.labels:
            print(l)
            l.forget()
            
        #self.frame3.pack_forget()
        #self.frame3.destroy()
        
        #self.frame3 = Tk.Frame(self.root)
        #self.frame3.pack(side=Tk.BOTTOM, fill=Tk.BOTH, expand=1)
        
        self.labels = []
        
    def update_label(self, i, p, text):
        
        while len(self.labels) <= i:
            label = Tk.Label(self.frame3)
            self.labels.append(label)
            
        label = self.labels[i]
        label.config(text = text, bg = p.color.lighthex, fg = p.color.darkhex)
        label.pack(side=Tk.LEFT, fill=Tk.BOTH, expand=1)
        
class BottomPanel2():
    def __init__(self, root):
        self.frame4 = Tk.Frame( root )
        self.frame4.pack(side=Tk.BOTTOM, fill=Tk.BOTH, expand=1)
        self._label = Tk.Label(self.frame4)
        self._text = ['BottomPanel2']
        
    def update_text(self, new_text):
        
        if new_text != self._text[-1]:
            self._text.append(new_text)
            
        self._label.config(text = '\n'.join(self._text[-3:]), bg = 'black', fg = 'white')
        self._label.pack(side=Tk.BOTTOM, fill=Tk.BOTH, expand=1)
            
            
class TroopSpinBoxFrame:
    def __init__(self, root):
        self.root = root
        self.frame = Tk.Frame(self.root)
        self.frame.pack(side=Tk.BOTTOM, fill=Tk.BOTH, expand=1)
        self.frame.pack_forget()
        self._label = Tk.Label(self.frame, text='Troops:')
        self._label.pack(side=Tk.LEFT, fill=Tk.BOTH, expand=1)
        self._value = Tk.IntVar()
        self._spinbox = Tk.Spinbox(self.frame, textvariable=self._value, width=5, wrap=True)
        self._spinbox.pack(side=Tk.RIGHT, fill=Tk.BOTH, expand=1)
        
    def get(self):
        
        return self._value.get()
        
    def config(self, min_value=1, max_value=2, default_value=1):
        
        self._value.set(default_value)
        self._spinbox.config(from_=min_value, to=max_value)
        self.frame.pack()
        
    def forget(self):
        
        self.frame.pack_forget()

class risk_view():
    def __init__(self, controller, model):
        
        self.territory_images = {}
        self._player_array = np.zeros(1)
        self._territory_owner_array_view = np.zeros(1)
        self._territory_troop_array_view = np.zeros(1)
        self._input_validation_array = np.zeros(1)
        self._input_validation_card_view = np.zeros(1)
        self._return_array = np.zeros(1)
        self._return_card_view = np.zeros(1)
        self.controller = controller
        self.model = model
        self.root = Tk.Tk()
        self.root.withdraw()
        

        self.board_base_image = None

        self.frame = Tk.Frame(self.root)
        self.root.bind("<Button-1>", self.button1_mouse_callback)
        self.root.bind("<Button-3>", self.button3_mouse_callback)
        self.sidepanel = RightSidePanel(self.root)
        self.leftsidepanel = None
        #self.leftsidepanel = LeftSidePanel(self.root)
        self.bottompanel = BottomPanel(self.root)
        self.bottompanel2 = BottomPanel2(self.root)
        self.model.bind_to_update_text(self.bottompanel2.update_text)
        self.current_player = None
        self.needed = False
        self.last_button3_i = -1
        
        self._troop_spinbox = TroopSpinBoxFrame(self.sidepanel.frame)
        
        for gs in GameState:
            if hasattr(self, gs.name + 'Button'):
                self.sidepanel.add_button(gs.name, getattr(self, gs.name + 'Button'))
                
        self.sidepanel.add_button('Wild', self.WildCardButton)
                
    def button1_mouse_callback(self, event):
        
        for gs in GameState:
            if self._player_array[gs.value]:
                #print(gs.name)
                if hasattr(self, gs.name + 'OnClick'):
                    getattr(self, gs.name + 'OnClick')(event.x, event.y)
                    
    def button3_mouse_callback(self, event):
        
        terr, i = self.territory_name_from_click(event.x, event.y)
        if not terr:
            return 
        
        if i != self.last_button3_i:
            i = self.last_button3_i
            self.bottompanel2.update_text('Terr: {}'.format(terr.name))
                
    def set_board(self, map_name):
        
        self.board_base_image = cv2.imread('{0}/{0}.png'.format(map_name))

        image = img(self.board_base_image)
        self.label = Tk.Label(image = image)
        self.label.image = image
        self.label.pack(side=Tk.LEFT, fill=Tk.BOTH, expand=1)
        
        for t in self.model.territories:
            self.territory_images[t.name] = territory_image(map_name, t.name, t.card_value)
        
        self.show_board()
        
    def update_terr_panel(self):
        
        num_players = len(self.model.players)
        #print(num_players)
        self.bottompanel.reset_labels(num_players) 
        
        for i, p in enumerate(self.model.players):
            terr_count, troop_count, card_count = self.model.get_player_summary(i)
            text = '{}: {} Terr, {} Troop(s), {} Card(s)'.format(p.name, terr_count, troop_count, card_count)
            self.bottompanel.update_label(i, p, text)
            
        if self.leftsidepanel:
            num_terr = len(self.territory_images)
            self.leftsidepanel.reset_labels(num_terr)
            
            for i, t in enumerate(self.territory_images.values()):
                
                p_index = int(self._territory_owner_array_view[i])
                if p_index > MAX_PLAYERS:
                    p_index = 0
                    
                p = self.model.players[p_index]
                text = '{}: {} ({})'.format(i, t.name[:15], int(self._territory_troop_array_view[i]))
                self.leftsidepanel.update_label(i, p, text, i < num_terr / 2)
    
    def WildCardButton(self, _):
        
        self.sidepanel.buttons['Wild'].forget()
        wild_return_view = self._return_array[-2:]
        wild_input_view = self._input_validation_card_view[-2:]
        wild_card_index = np.where(wild_input_view == 1)[0]
        
        wild_return_view[wild_card_index[0]] = 1
        
        self._return_array[GameState.SelectCard.value] = 1
        self.model.handle_return_array(self._return_array)
    
    def StartTurnButton(self, _):
        
        self._return_array[GameState.StartTurn.value] = 1
        self.model.handle_return_array(self._return_array)

    def EndTurnButton(self, _):
        
        self._return_array[GameState.EndTurn.value] = 1
        self.model.handle_return_array(self._return_array)
    
    def StartTroopPlacement(self):
        
        if self._input_validation_array[GameState.TurnInCards.value]:
            self.sidepanel.buttons['StartTroopPlacement'].pack()
            return
        
        self._return_array[GameState.StartTroopPlacement.value] = 1
        self.model.handle_return_array(self._return_array)
            
    def StartTroopPlacementButton(self, _):
        
        self._return_array[GameState.StartTroopPlacement.value] = 1
        self.model.handle_return_array(self._return_array)
    
    def TurnInCardsButton(self, _):
        
        self._return_array[GameState.TurnInCards.value] = 1
        self.model.handle_return_array(self._return_array)
    
    
    def SkipReinforcementButton(self, _):
        
        self._return_array[GameState.SkipReinforcement.value] = 1
        self.model.handle_return_array(self._return_array)
    
    def territory_name_from_click(self, x, y):
        
        #logging.debug('x: {} y: {}'.format(x, y))
        #print(self._input_validation_array)
        
        distance = float('Inf')
        terr = None
        i = -1
        for it, t in enumerate(self.territory_images.values()):
            this_distance = int(math.sqrt((x - t.cX)**2 + (y - t.cY)**2))
            if this_distance < distance:
                distance = this_distance
                terr = t
                i = it
              
        #logging.debug('Closest Terr: {}, distance: {}, index: {}'.format(terr.name, distance, i))
        if distance > 20:
            return '', -1
                
        
        
        return terr, i
    
    def SelectCard(self):
        
        self.sidepanel.buttons['Wild'].forget()
        
        # Need to highlight 
        valid_card_index = np.where(self._input_validation_card_view == 1)[0]
        
        base_image = self.board_base_image.copy()
        
        territories = self.model.territories
        player_array = self.model.create_player_array()
        
        for i, t in enumerate(territories):
            self.show_territory_background(base_image, t, i, player_array)
        
        font = cv2.FONT_HERSHEY_COMPLEX_SMALL

        for v in valid_card_index:
            
            if v >= len(self.territory_images):
                self.sidepanel.buttons['Wild'].pack()
                continue
            
            territory = self.territory_images[list(self.territory_images.keys())[v]]
            text = territory.card_value[-1]
            cX = territory.cX
            cY = territory.cY
     
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
            cv2.rectangle(base_image, (lowerL, lowerR), (upperL, upperR), (0,0,0), -1)
            
            # add text centered on image
            cv2.putText(base_image, text, (lowerLT, lowerRT), font, 1, (255,255,255), 2)
            
        image = img(base_image)
        self.label.config(image = image)
        self.label.image = image
        
        
    def SelectCardOnClick(self, x, y):
        
        terr, i = self.territory_name_from_click(x, y)
        
        if not terr:
            return
        
        if not self._input_validation_card_view[i]:
            logging.debug('{} does not own card {}'.format(self.model.players[0].name, terr.name))
            return
        
        self._return_array[GameState.SelectCard.value] = 1
        self._return_card_view[i] = 1
        self.model.handle_return_array(self._return_array)
        
    def PlaceTroopsOnClick(self, x, y):
        
        terr, i = self.territory_name_from_click(x, y)
        
        if not terr:
            return
        #print(self._input_validation_card_view.shape, i)
        if not self._input_validation_card_view[i]:
            logging.debug('{} does not own {}'.format(self.model.players[0].name, terr.name))
            return
        
        troop_fraction = (self._troop_spinbox.get() - 1.0) / self._player_array[GameState.PlaceTroops.value]
        #print(self._troop_spinbox.get(), self._player_array[GameState.PlaceTroops.value], troop_fraction)
        self._return_array[GameState.PlaceTroops.value] = 1
        self._return_card_view[i] = troop_fraction
        self.model.handle_return_array(self._return_array)
        
    def SelectAttackingTerritoryOnClick(self, x, y):
        
        terr, i = self.territory_name_from_click(x, y)
                
        if not terr:
            return
        
        if not self._input_validation_card_view[i]:
            print(i, self._input_validation_array)
            logging.debug('{} does not own {} or it only has 1 troop'.format(self.model.players[0].name, terr.name))
            return
        
        self._return_array[GameState.SelectAttackingTerritory.value] = 1
        self._return_card_view[i] = 1
        self.model.handle_return_array(self._return_array)

    def SelectDefendingTerritoryOnClick(self, x, y):
        
        terr, i = self.territory_name_from_click(x, y)
                
        if not terr:
            return
        
        if not self._input_validation_card_view[i]:
            print(i, terr, self._input_validation_array)
            logging.debug('{} cannot be attacked'.format(terr.name))
            return
        
        self._return_array[GameState.SelectDefendingTerritory.value] = 1
        self._return_card_view[i] = 1
        self.model.handle_return_array(self._return_array)

    
    def SelectReiforceSourceOnClick(self, x, y):
        
        terr, i = self.territory_name_from_click(x, y)
                
        if not terr:
            print(terr)
            logging.debug('SelectReiforceSourceOnClick, terr:') 
            return
        
        if not self._input_validation_card_view[i]:
            print(i, self._input_validation_array)
            logging.debug('{} cannot be used to supply troops'.format(terr.name))
            return
        
        self._return_array[GameState.SelectReiforceSource.value] = 1
        self._return_card_view[i] = 1
        print('SelectReiforceSource', self._return_array)
        self.model.handle_return_array(self._return_array)
             
    def SelectReiforceDestinationOnClick(self, x, y):
        
        terr, i = self.territory_name_from_click(x, y)
                
        if not terr:
            return
        
        if not self._input_validation_card_view[i]:
            print(i, self._input_validation_array)
            logging.debug('{} cannot receive troops'.format(terr.name))
            return
        
        self._return_array[GameState.SelectReiforceDestination.value] = 1
        self._return_card_view[i] = 1
        print('SelectReiforceDest', self._return_array)
        self.model.handle_return_array(self._return_array)
             
    def PlaceTroopsSpinBox(self):
             
        max_value = self._player_array[GameState.PlaceTroops.value]
        self._troop_spinbox.config(max_value=max_value, default_value=max_value)
             
    def random_init(self, _):
        logging.debug('Pressed Random Init Button in risk_view')
        self.controller.random_init()
        self.show_board()
    
    def show_board(self):
        
        if not self.model.map_name:
            return
        
        if self.board_base_image is None:
            self.set_board(self.model.map_name)
    
        base_image = self.board_base_image.copy()
        territories = self.model.territories
        
        #logging.debug('Showing board for {} territories'.format(len(territories)))
        
        player_array = self.model.create_player_array()
        
        for i, t in enumerate(territories):
            self.show_territory_background(base_image, t, i, player_array)
            
        for i, t in enumerate(territories):
            self.show_territory_troops(base_image, t, i, player_array)
            
        image = img(base_image)
        self.label.config(image = image)
        self.label.image = image

    def show_territory_background(self, base_image, territory, index, player_array):
        
        #logging.debug('Territory {} has index {}'.format(territory.name, index))
        owner_index = int(player_array[self.model.territory_owner_start + index])
        if owner_index  == UNINIT:
            return
            
        # This is an attacking territory
        if owner_index > MAX_PLAYERS:
            owner_index = 0
            
        player = self.model.players[owner_index]
        cl = player.color.light
        cd = player.color.dark
            
        territory = self.territory_images[territory.name]
        
        # Fill in the background
        base_image[np.where(territory.image!=[0])] = cl
            
        # FIll in the edges
        base_image[np.where(territory.outline!=[0])] = cd
                
    
                
    def show_territory_troops(self, base_image, territory, index, player_array):
        
        owner_index = int(player_array[self.model.territory_owner_start + index])
        troop_index = int(player_array[self.model.territory_troop_start + index])
        if owner_index  == UNINIT:
            return
        
        # This is an attacking territory
        if owner_index > MAX_PLAYERS:
            owner_index = 0
        
        player = self.model.players[owner_index]
        cl = player.color.dark
        cd = player.color.normal
        text = '{}:{}'.format(index, troop_index)
        font = cv2.FONT_HERSHEY_COMPLEX_SMALL
        
        territory = self.territory_images[territory.name]
        
        cX = territory.cX
        cY = territory.cY
        
        # setup text
        if not self.leftsidepanel:
            text = str(troop_index)
            font = cv2.FONT_HERSHEY_COMPLEX

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
        
    def handle_array(self, player_array, input_validation_array, return_array):
        
        #logging.debug('Calling risk_view handle_array')
        if np.array_equal(self._player_array, player_array):
            return

        self.show_board()
        
        terr_data_start = len(input_validation_array) - len(self.territory_images) - 2
        troop_data_start = terr_data_start + len(self.territory_images)
        card_data_start = troop_data_start + len(self.territory_images)
        self._player_array = player_array
        self._territory_owner_array_view = player_array[terr_data_start:troop_data_start]
        self._territory_troop_array_view = player_array[troop_data_start:card_data_start]
        self._input_validation_array = input_validation_array
        self._input_validation_card_view = self._input_validation_array[terr_data_start:]
        self._return_array = return_array
        self._return_card_view = self._return_array[terr_data_start:]
        self.update_terr_panel()
        
        #print(self._player_array)
        self.show_board()
        self.root.deiconify()
        self._troop_spinbox.forget()
        
        for gs in GameState:
            if player_array[gs.value]:
                
                if hasattr(self, gs.name + 'SpinBox'):
                    getattr(self, gs.name + 'SpinBox')()
                    
                if hasattr(self, gs.name):
                    getattr(self, gs.name)()
                elif hasattr(self, gs.name + 'Button'):
                    
                    self.sidepanel.buttons[gs.name].pack()
                elif hasattr(self, gs.name + 'OnClick'):
                    pass
                else:
                    raise Exception('Need to add {} function/button in view'.format(gs.name))
            elif hasattr(self, gs.name + 'Button'):
                    self.sidepanel.buttons[gs.name].pack_forget()

    def run(self):

        title = 'Risk'
        if self.model.map_name:
            title += ': {}'.format(self.model.map_name)
            
        self.root.title(title)
        self.root.mainloop()
 
