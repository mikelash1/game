# -*- coding: utf-8 -*-
"""
Created on Thu Feb  8 12:16:12 2018

@author: LashMi
"""

lines = []
with open('MapInfo.txt', 'r') as fid:
    lines = fid.readlines()
    
i = 0
countries = []
while lines[i].strip():
    useful = lines[i].split('[')[1].replace(']','').replace("'",'').split(',')[:-1]
    continent = useful[-1].strip() + useful[-2].strip()
    for u in useful[:-2]:
        countries.append([u.strip().replace(' ','_'), continent])
        print(len(countries),u.strip())
    print(useful)
    i += 1
    
    

#fid.write('\n')
i += 1
while lines[i].strip():
    
    nums = [int(n) for n in lines[i].strip().split()]
    i2 = nums.pop(0)
    nums.sort()
    print(i2)
    print(countries[i2 - 1][0])
    #print(nums)
    str1 = '{}\t{}\n'.format(i2, ' '.join([str(n) for n in nums]))
    lines[i] = str1
    print(str1.strip())
    #fid.write(str1)
    borders = [countries[n-1][0] for n in nums]
    print(borders)
    
    i += 1

with open('MapInfo.txt', 'w') as fid:
    fid.write(''.join(lines))