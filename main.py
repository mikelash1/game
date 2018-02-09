# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import os
import cv2
import numpy as np
import matplotlib as plt

'''
self.continents.append (Continent (['Congo', 'East Africa', 'Egypt', 'Madagascar', 'North Africa', 'South Africa']
, 3, 'Africa', self))
self.continents.append (Continent (['Alaska', 'Alberta', 'Central America', 'Eastern US', 'Greenland', 'Northwest Territories', 'Ontario', 'Quebec' , 'Western US']
, 5, 'North America', self))
self.continents.append (Continent ([ 'Venezuela', 'Brazil', 'Peru', 'Argentina']
, 2, 'South America', self))
self.continents.append (Continent ([Afghanistan ',' China ',' India ',' Irkutsk ',' Japan ',' Kamchatka ',' Middle East ',' Mongolia ',' Siam ',' Siberia ' , Ural ',' Yakutsk ']
7, Asia 'self))
self.continents.append (Continent (['Great Britain', 'Iceland', 'Northern Europe', 'Scandinavia', 'Southern Europe', 'Ukraine', 'Western Europe']
5, 'Europe', self))
self.continents.append (Continent (['Eastern Australia', 'Indonesia', 'New Guinea', 'Western Australia']
, 2, 'Oceania', self))

            self.continents[0].pays[0].voisins=[2,5,6]
			self.continents[0].pays[1].voisins=[1,3,4,5,26]
			self.continents[0].pays[2].voisins=[2,5,36,26]
			self.continents[0].pays[3].voisins=[2,6]
			self.continents[0].pays[4].voisins=[1,2,3,17,36,38]
			self.continents[0].pays[5].voisins=[1,2,4]
			self.continents[1].pays[0].voisins=[8,12,25]
			self.continents[1].pays[1].voisins=[7,12,13,15]
			self.continents[1].pays[2].voisins=[15,10,19]#Am centrale
			self.continents[1].pays[3].voisins=[9,15,13,14]#10
			self.continents[1].pays[4].voisins=[12,13,14,33]
			self.continents[1].pays[5].voisins=[7,8,13,11]
			self.continents[1].pays[6].voisins=[8,15,10,14,11,12]
			self.continents[1].pays[7].voisins=[10,13,11]
			self.continents[1].pays[8].voisins=[9,10,8,13]
			self.continents[2].pays[0].voisins=[17,18]
			self.continents[2].pays[1].voisins=[16,18,19,5]
			self.continents[2].pays[2].voisins=[16,17,19]
			self.continents[2].pays[3].voisins=[18,17,9]#Argentine
			self.continents[3].pays[0].voisins=[21,22,26,30,37]#20
			self.continents[3].pays[1].voisins=[20,22,28,27,29,30]
			self.continents[3].pays[2].voisins=[20,21,26,28]
			self.continents[3].pays[3].voisins=[29,27,25,31]
			self.continents[3].pays[4].voisins=[27,25]
			self.continents[3].pays[5].voisins=[31,23,27,24,7]
			self.continents[3].pays[6].voisins=[20,22,37,2,3]
			self.continents[3].pays[7].voisins=[24,21,29,25,23]
			self.continents[3].pays[8].voisins=[21,22,40]
			self.continents[3].pays[9].voisins=[30,21,23,31,27]
			self.continents[3].pays[10].voisins=[20,21,29,37]#30
			self.continents[3].pays[11].voisins=[29,23,25]
			self.continents[4].pays[0].voisins=[33,35,34,38]
			self.continents[4].pays[1].voisins=[32,35,11]
			self.continents[4].pays[2].voisins=[32,35,37,36,38]
			self.continents[4].pays[3].voisins=[37,32,33,34]
			self.continents[4].pays[4].voisins=[38,34,37,3,26,5]
			self.continents[4].pays[5].voisins=[35,34,36,20,26,30]
			self.continents[4].pays[6].voisins=[32,34,36,5]
			self.continents[5].pays[0].voisins=[42,41]
			self.continents[5].pays[1].voisins=[42,41,28]#40
			self.continents[5].pays[2].voisins=[42,40,39]
			self.continents[5].pays[3].voisins=[39,41,40]
'''

colors = []
for c in ['blue', 'green', 'red', 'yellow', 'orange', 'purple']:
    norm = list(plt.colors.to_rgb('xkcd:dark {}'.format(c)))
    light = list(plt.colors.to_rgb('xkcd:light {}'.format(c)))
    
    brgnorm = [int(i * 255) for i in reversed(norm)]
    brglight = [int(i * 255) for i in reversed(light)]
    colors.append([brgnorm, brglight])
    #colors.append([brglight, brgnorm])

def main():
    
    #img1 = cv2.imread('Pictures/Risk_game_map_fixed_greylevel.png')
    img1 = cv2.imread('Risk_game_map.png')
    #img1 = cv2.bitwise_not(img1)
    #print(img1)
    #return
    
    cv2.imshow('image', img1)
    cv2.waitKey(0)
    
    #for i in range(3):
    i = -1
    while True:
        i += 1
        
        new_file = 'Pictures/Maps/{:02d}.png'.format(i+1)
        if not os.path.isfile(new_file):
            break
        
        c = i % len(colors)
        
        #print(new_file)
        image = cv2.imread(new_file, cv2.IMREAD_GRAYSCALE)
        img1[np.where(image!=[0])] = colors[c][1]
        
        edges = cv2.Canny(image,100,200)
        #cv2.imshow('image', edges)
        #cv2.waitKey(0)   
        
        img1[np.where(edges!=[0])] = colors[c][0]
        
        M = cv2.moments(image)
        cX = int(M["m10"] / M["m00"])
        cY = int(M["m01"] / M["m00"])
        
        # setup text
        font = cv2.FONT_HERSHEY_SIMPLEX
        text = str(i+1)
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
        
        cv2.rectangle(img1, (lowerL, lowerR), (upperL, upperR), colors[c][0], -1)
        #cv2.putText(img1, str(i), (cX, cY), cv2.FONT_HERSHEY_SIMPLEX, 0.5, \
        #    colors[c][1], 2)
        
        # add text centered on image
        cv2.putText(img1, text, (lowerLT, lowerRT), font, 1, colors[c][1], 2)
        
        # Detect blobs.
        #keypoints = detector.detect(image)
 
        # Draw detected blobs as red circles.
        # cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS ensures the size of the circle corresponds to the size of blob
        #img1 = cv2.drawKeypoints(img1, keypoints, np.array([]), (0,0,255), cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
 
        #img1 += image
        cv2.imshow('image', img1)
        
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == '__main__':
    
    main()