# -*- coding: utf-8 -*-
"""
Created on Mon Jun 27 17:19:00 2016

@author: avanetten
"""

import numpy as np
import matplotlib.pyplot as plt
from skimage import draw

show_plots = True

#########################
# open file, if known  
#import PIL      
#img_in = PIL.Image.open(...).convert('RGBA')
#width, height = img_in.size
# else, assign size
width, height = 250, 250

#########################
# sample bounding polygons
ground_truth_boxes = [np.array([[ 62, 135],
        [120, 208],
        [144, 188],
        [ 86, 115]], dtype=np.int32), 
np.array([[ 6, 65],
        [80, 108],
        [100, 120],
        [ 26, 60]], dtype=np.int32), 
np.array([[ 140, 100],
        [179, 140],
        [195, 128],
        [ 150, 75]], dtype=np.int32),
np.array([[ 150, 195],
        [174, 240],
        [193, 228],
        [ 140, 165]], dtype=np.int32)]

# create proposed boxes, shifted slightly from ground truth
prop_boxes = []
for b in ground_truth_boxes:
    p0 = b + np.random.randint(-5, 5, b.shape)
    prop_boxes.append(p0)

#########################
# create truth mask
truth_mask = np.zeros((height, width))
for b in ground_truth_boxes:
#skifor (y, x), v in polys:
    x = b[:,0]
    y = b[:,1]
    rr, cc = draw.polygon(y, x)#, (H, W))
    truth_mask[rr, cc] += 1 
if show_plots:
    plt.matshow(truth_mask)   
    plt.title("Ground truth polygons") 
    #plt.imshow(truth_mask, interpolation="None")

#########################
# create proposed mask
prop_mask = np.zeros((height, width))
for b in prop_boxes:
#skifor (y, x), v in polys:
    x = b[:,0]
    y = b[:,1]
    rr, cc = draw.polygon(y, x)#, (H, W))
    prop_mask[rr, cc] += 1 
if show_plots:
    plt.matshow(prop_mask)    
    plt.title("Proposed polygons") 

#########################
# get pixel counts of ground truth
truth_pos_idxs = np.nonzero(truth_mask)
truth_pos_count = len(truth_pos_idxs[0])
truth_size = truth_mask.size
truth_neg_count = truth_size - truth_pos_count

#########################
# find true pos, false pos, true neg, false neg
# multiply truth_mask by 2, and subtract.  make sure arrays are clipped
#   so that overlapping regions don't cause problems
truth_mask_clip = np.clip(truth_mask, 0, 1)
prop_mask_clip = 2*np.clip(prop_mask, 0, 1)
# subtract array
sub_mask = prop_mask_clip - truth_mask_clip
# true pos = 1, false_pos = 2, true_neg = 0, false_neg = -1
true_pos_count = len(np.where(sub_mask == 1)[0])
false_pos_count = len(np.where(sub_mask == 2)[0])
true_neg_count = len(np.where(sub_mask == 0)[0])
false_neg_count = len(np.where(sub_mask == -1)[0])
precision = float(true_pos_count) / float( true_pos_count + false_pos_count)
recall = float(true_pos_count) / float( true_pos_count + false_neg_count)
# check count 
if true_pos_count + false_pos_count + true_neg_count + false_neg_count != truth_size:
    print "\nError in counting true and false positives and negatives!\n"

#########################
# plot both
if show_plots:
    fig = plt.figure()
    ax = fig.add_subplot(1,1,1)
    plot = ax.pcolor(sub_mask)
    # axis gets inverted for some reason
    plt.gca().invert_yaxis()
    fig.colorbar(plot)
    title = "true pos = 1, false_pos = 2, true_neg = 0, false_neg = -1\nprecision: " +\
            str(np.round(precision,4)) + "  recall: " +  str(np.round(recall, 4))
    plt.title(title)
    plt.tight_layout()
    #plt.matshow(sub_mask)  
  
#########################
print "Num ground truth pos pixels:", len(np.nonzero(truth_mask)[0])
print "Num proposed pos pixels:", len(np.nonzero(prop_mask)[0])    
print "Num ground truth boxes:", len(ground_truth_boxes)
print "Num proposed boxes:", len(prop_boxes)
print "\n"
print "True positive pixel count:", true_pos_count  
print "False positive pixel count:", false_pos_count  
print "True negative pixel count:", true_neg_count  
print "False negative pixel count:", false_neg_count  
print "Precision:", precision
print "Recall:", recall
