from __future__ import print_function, division
from glob import glob
from random import random
import os
from numpy import array
from geojson import load
from shapely.geometry import Polygon
import numpy as np
import pandas as pd

def polygonize(csv_path):
    polys = []
    polys_df = pd.read_csv(csv_path)
    image_ids = set(polys_df['ImageId'].tolist())
    for image_id in image_ids:
        img_df = polys_df.loc[polys_df['ImageId'] == image_id]
        building_ids = set(img_df['BuildingId'].tolist())
        for building_id in building_ids:
            if building_id != 0:
                building_df = img_df.loc[img_df['BuildingId'] == building_id]
                poly = zip(building_df['X'].astype(int), building_df['Y'].astype(int))
                polys.append({'ImageId': image_id, 'BuildingId': building_id, 'poly': Polygon(poly)})
            else:
                polys.append({'ImageId': image_id, 'BuildingId': building_id, 'poly': Polygon()})
    return polys

def get_image_ids(csv_path):
    polys_df = pd.read_csv(csv_path)
    return set(polys_df['ImageId'].tolist())

def load_sorted_polygons(test_csv_path, truth_csv_path):
    # Assumes -
    # 1. Polygons are presorted for descending confindence.
    # 2. Chips with no buildings assign zero for the BuildingId
    return polygonize(test_csv_path), polygonize(truth_csv_path)

def score(test_polys, truth_polys):

    # Define internal functions
    IoU = lambda p1, p2: (print(p2),p1.intersection(p2).area/p1.union(p2).area)
    argmax = lambda iterable, func: max(iterable, key=func)

    # Find detections using threshold/argmax/IoU for test polygons
    true_pos_count = 0
    false_pos_count = 0
    B = len(truth_polys)
    M = len(test_polys)
    for test_poly in test_polys:
        print('test poly: ', test_poly)
        IoUs = map(lambda x:IoU(test_poly,x)[1],truth_polys)
        maxIoU = max(IoUs)
        threshold = 0.5
        if maxIoU >= threshold:
            true_pos_count += 1
            del truth_polys[np.argmax(IoUs)]
        else:
            false_pos_count += 1
    false_neg_count = B - true_pos_count
    precision = true_pos_count/(true_pos_count+false_pos_count)
    recall = true_pos_count/(true_pos_count+false_neg_count)
    return true_pos_count, false_pos_count, false_neg_count


if __name__ == "__main__":
    true_pos_counts = []
    false_pos_counts = []
    false_neg_counts = []

    test_fp = 'Submission_1.0.csv'
    truth_fp = 'Solution.csv'
    prop_polys, sol_polys = load_sorted_polygons(test_fp, truth_fp)

    test_image_ids = get_image_ids(test_fp)
    bad_count = 0
    for image_id in test_image_ids:
        test_polys = []
        truth_polys = []
        image_test_polys = [item for item in prop_polys if item["ImageId"] == image_id]
        for poly in image_test_polys:
            test_polys.append(poly['poly'])
        image_truth_polys = [item for item in sol_polys if item["ImageId"] == image_id]
        for poly in image_truth_polys:
            p = poly['poly']
            if False == p.is_valid:
                bad_count += 1
                p = p.buffer(0.0)
            truth_polys.append(p)
        true_pos_count, false_pos_count, false_neg_count = score(test_polys, truth_polys)
        true_pos_counts.append(true_pos_count)
        false_pos_counts.append(false_pos_count)
        false_neg_counts.append(false_neg_count)
        precision = float(sum(true_pos_counts))/float(sum(true_pos_counts)+sum(false_pos_counts))
        recall = float(sum(true_pos_counts))/float(sum(true_pos_counts)+sum(false_neg_counts))
        F1score  = 2.0*precision*recall/(precision+recall)
        print('F1 Score: ', F1score)
        print('bad count: ', bad_count)
