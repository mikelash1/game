# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import cv2
import numpy as np

def main():
    
    #img1 = cv2.imread('Pictures/Risk_game_map_fixed_greylevel.png')
    img1 = cv2.imread('Pictures/Risk_game_map.png')
    
    cv2.imshow('image', img1)
    cv2.waitKey(0)
    
    for i in range(15):
        new_file = 'Pictures/Maps/{:02d}.png'.format(i+1)
        print(new_file)
        image = cv2.imread(new_file, cv2.IMREAD_GRAYSCALE)
        img1[np.where(image!=[0])] = [70,70,130]
        
        edges = cv2.Canny(image,100,200)
        #cv2.imshow('image', edges)
        #cv2.waitKey(0)   
        
        img1[np.where(edges!=[0])] = [0,0,255]
        
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