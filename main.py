# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import os
import cv2
import numpy as np
import matplotlib as plt

colors = []
for c in ['blue', 'green', 'red', 'yellow', 'orange', 'purple']:
    norm = list(plt.colors.to_rgb('xkcd:dark {}'.format(c)))
    light = list(plt.colors.to_rgb('xkcd:light {}'.format(c)))
    
    brgnorm = [i * 255 for i in reversed(norm)]
    brglight = [i * 255 for i in reversed(light)]
    colors.append([brgnorm, brglight])
    #colors.append([brglight, brgnorm])

def main():
    
    #img1 = cv2.imread('Pictures/Risk_game_map_fixed_greylevel.png')
    img1 = cv2.imread('Pictures/Risk_game_map.png')
    #img1 = cv2.bitwise_not(img1)
    print(img1)
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
        
        print(new_file)
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
        text = str(i)
        border = 10
        
        # get boundary of this text
        textsize = cv2.getTextSize(text, font, 1, 2)[0]
        
        # get coords based on boundary
        lowerL = cX - (textsize[0] + border) / 2
        lowerR = cY + (textsize[1] + border) / 2
        upperL = cX + (textsize[0] + border) / 2
        upperR = cY - (textsize[1] + border) / 2
        lowerLT = cX - textsize[0] / 2
        lowerRT = cY + textsize[1] / 2
        
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