# -*- coding: utf-8 -*-
"""
Created on Fri Feb  9 15:04:00 2018

@author: LashMi
"""

import cv2
import numpy as np
import matplotlib as plt
import logging

class Territory:
    def __init__(self, name, continent, borders, board):
        self.name = name
        self.continent = continent
        self.borders = borders
        self.owner = ''
        self.troops = 0
        
        image_name = 'World/{}.png'.format(name)
        self.image = cv2.imread(image_name, cv2.IMREAD_GRAYSCALE)
        self.outline = cv2.Canny(self.image,100,200)
        M = cv2.moments(self.image)
        self.cX = int(M["m10"] / M["m00"])
        self.cY = int(M["m01"] / M["m00"])
        
    def newOwner(self, owner):
        global players
        if self.owner and self.owner != owner:
            logging.info('{} captured {} from {}'.format(owner, self.name, self.owner))
            players[self.owner].removeCountry(self.name)
        
        self.owner = owner
        players[self.owner].addCountry(self.name)
        self.troops = 0
        
    def addTroops(self, troops=1):
        self.troops += troops
        
    def removeTroops(self, troops=1):
        self.troops -= troops

class GameState:
    def __init__(self, board):
        self.board = board
        self.board_base_image = '{0}/{0}.png'.format(board)
        self.territories = {}
        self.continents = {}
        self.colors = {}
        
        self.load_colors()
        
    def load_colors(self):
    
        for c in ['blue', 'green', 'red', 'yellow', 'orange', 'purple']:
            norm = list(plt.colors.to_rgb('xkcd:dark {}'.format(c)))
            light = list(plt.colors.to_rgb('xkcd:light {}'.format(c)))
            
            brgnorm = [int(i * 255) for i in reversed(norm)]
            brglight = [int(i * 255) for i in reversed(light)]
            self.colors[c] = [brgnorm, brglight]
            
    def load_territories(self):
        
        lines = []
        with open('{}/Territories.txt'.format(self.board), 'r') as fid:
            lines = fid.readlines()
            
        for l in lines:
            parts = l.strip().split()
            self.territories[parts[0]] = Territory(parts[0], parts[1], parts[2:-1])
            
            continent = self.continents.get(parts[1], set())
            continent.add(parts[0])
            self.continents[parts[1]] = continent
    
    def show_board(self, wait=0):
    
        base_image = cv2.imread(self.board_base_image)
        
        for cn, c in self.territories.items():
            self.show_territory_background(base_image, c)
            
        for cn, c in self.territories.items():
            self.show_territory_troops(base_image, c)
            
        cv2.imshow(self.board, base_image)
        cv2.waitKey(wait)
        
    def show_territory_background(self, base_image, territory):
        
        if not territory.owner:
            return
            
        c = territory.owner
        
        # Fill in the background
        base_image[np.where(territory.image!=[0])] = self.colors[c][1]
            
        # FIll in the edges
        base_image[np.where(territory.outline!=[0])] = self.colors[c][0]
                
    def show_territory_troops(self, base_image, territory):
        
        if not territory.owner:
            return
            
        c = territory.owner
        
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
        cv2.rectangle(base_image, (lowerL, lowerR), (upperL, upperR), self.colors[c][0], -1)
        
        # add text centered on image
        cv2.putText(base_image, text, (lowerLT, lowerRT), font, 1, self.colors[c][1], 2)
        
    def new_troops(self, my_territories):
        
        # territory Count Troops
        troops = int(len(my_territories) / 3)
        if troops < 3:
            troops = 3
            
        # Continent Bonus
        for n, cont in self.continents.items():
            if cont <= my_territories:
                troops += int(n[-1])
                
        return troops