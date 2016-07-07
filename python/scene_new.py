from __future__ import print_function, division
from glob import glob
from random import random
from numpy import array
from geojson import load
from shapely.geometry import Polygon
import numpy as np
from rtree import index
import os


def average_precision(truth_fp, test_fp):
    IoU = lambda p1, p2: p1.intersection(p2).area / p1.union(p2).area
    f = open(truth_fp)
    truth_features = load(f, encoding='latin-1')
    f = open(test_fp)
    test_features = load(f, encoding='latin-1')
    pos_det = 0
    for truth_feature in truth_features['features']:
        truth_poly = Polygon(truth_feature['geometry']['coordinates'][0])
        for test_feature in test_features['features']:
            test_poly = Polygon(test_feature['geometry']['coordinates'][0])
            if test_poly.intersects(truth_poly):
                pos_det += 1
    return pos_det/len(test_features['features'])


def average_localization_error(truth_fp, test_fp):
    IoU = lambda p1, p2: p1.intersection(p2).area / p1.union(p2).area
    f = open(truth_fp)
    truth_features = load(f, encoding='latin-1')
    f = open(test_fp)
    test_features = load(f, encoding='latin-1')
    pos_det = 0
    for truth_feature in truth_features['features']:
        truth_poly = Polygon(truth_feature['geometry']['coordinates'][0])
        for test_feature in test_features['features']:
            test_poly = Polygon(test_feature['geometry']['coordinates'][0])
            if 0 < IoU(test_poly, truth_poly) < 0.5:
                pos_det += 1
    return pos_det/len(test_features['features'])


def remove_dupes(test_polys):
    unique = []
    for test_poly in test_polys:
        if test_poly not in unique:
            unique.append(test_poly)
        else:
            print('Removed duplicate.')
    return unique


def score(test_geojson_path, truth_geojson_path):

    # Define internal functions
    IoU = lambda p1, p2: p1.intersection(p2).area/p1.union(p2).area
    argmax = lambda iterable, func: max(iterable, key=func)
    polygonize = lambda feature: Polygon(feature['geometry']['coordinates'][0])

    # Convert geojson files of features/geometries to arrays of polygons
    test_features = load(open(test_geojson_path), encoding='latin-1')
    truth_features = load(open(truth_geojson_path), encoding='latin-1')
    test_polys = [polygonize(f) for f in test_features['features']]
    truth_polys = [polygonize(f) for f in truth_features['features']]

    # Generate artifical confidences and sort
    test_polys =  [[random(), test_poly] for test_poly in test_polys]
    test_polys = sorted(test_polys, key=lambda l:l[0], reverse=True)

    # Find detections using threshold/argmax/IoU for test polygons
    true_pos_count = 0
    false_pos_count = 0
    B = len(truth_polys)
    M = len(test_polys)
    for test_poly in test_polys:
        IoUs = map(lambda x:IoU(test_poly[1],x),truth_polys)
        maxIoU = max(IoUs)
        threshold = 0.5
        if maxIoU >= threshold:
            true_pos_count += 1
            del truth_polys[np.argmax(IoUs)]
        else:
            false_pos_count += 1
    false_neg_count = B - true_pos_count
    print('1 - Num truths: ', B)
    print('1 - Num proposals: ', M)
    print('1 - True pos count: ', true_pos_count)
    print('1 - False pos count: ', false_pos_count)
    print('1 - False neg count: ', false_neg_count)
    precision = true_pos_count/(true_pos_count+false_pos_count)
    recall = true_pos_count/(true_pos_count+false_neg_count)
    return (precision, recall)


def score2(test_geojson_path, truth_geojson_path):

    # Define internal functions
    IoU = lambda p1, p2: p1.intersection(p2).area/p1.union(p2).area
    argmax = lambda iterable, func: max(iterable, key=func)
    polygonize = lambda feature: Polygon(feature['geometry']['coordinates'][0])

    # Convert geojson files of features/geometries to arrays of polygons
    test_features = load(open(test_geojson_path), encoding='latin-1')
    truth_features = load(open(truth_geojson_path), encoding='latin-1')
    test_polys = [polygonize(f) for f in test_features['features']]
    truth_polys = [polygonize(f) for f in truth_features['features']]

    # Generate artifical confidences and sort
    test_polys =  [[random(), test_poly] for test_poly in test_polys]
    test_polys = sorted(test_polys, key=lambda l:l[0], reverse=True)

    # Find detections using threshold/argmax/IoU for test polygons
    matched = np.zeros(len(truth_polys))
    true_pos_count = 0
    false_pos_count = 0
    B = len(truth_polys)
    M = len(test_polys)
    for test_poly in test_polys:
        IoUs = map(lambda x:IoU(test_poly[1],x),truth_polys)
        maxIoU = max(IoUs)
        threshold = 0.5
        if maxIoU >= threshold:
            true_pos_count += 1
            if matched[np.argmax(IoUs)] > 0.0:
                true_pos_count -= 1
                false_pos_count += 1
            matched[np.argmax(IoUs)] += 1.0
        else:
            false_pos_count += 1
    false_neg_count = B - true_pos_count
    print('2 - Num truths: ', B)
    print('2 - Num proposals: ', M)
    print('2 - True pos count: ', true_pos_count)
    print('2 - False pos count: ', false_pos_count)
    print('2 - False neg count: ', false_neg_count)
    precision = true_pos_count/(true_pos_count+false_pos_count)
    recall = true_pos_count/(true_pos_count+false_neg_count)
    return (precision, recall)


def score3(test_geojson_path, truth_geojson_path):

    # Define internal functions
    IoU = lambda p1, p2: p1.intersection(p2).area/p1.union(p2).area
    polygonize = lambda feature: Polygon(feature['geometry']['coordinates'][0])

    # Convert geojson files of features/geometries to arrays of polygons
    test_features = load(open(test_geojson_path), encoding='latin-1')
    truth_features = load(open(truth_geojson_path), encoding='latin-1')
    test_polys = remove_dupes([polygonize(f) for f in test_features['features']])
    # test_polys = [(i, p.bounds, p) for i, p in enumerate(test_polys)]
    truth_polys = [polygonize(f) for f in truth_features['features']]
    truth_polys = [(i, p.bounds, p) for i, p in enumerate(truth_polys)]

    # Use a geospatial index to compare the polygons
    idx = index.Index()
    for i, bounds, truth_poly in truth_polys:
        idx.insert(i, bounds, obj=truth_poly)

    threshold = 0.5
    true_pos_count = 0
    false_pos_count = 0
    B = len(truth_polys)
    M = len(test_polys)
    for test_poly in test_polys:
        maxIoU = 0
        if idx.count(test_poly.bounds) > 0:
            for truth_poly in idx.intersection(test_poly.bounds, objects='raw'):
                iou = IoU(test_poly, truth_poly)
                if iou >= threshold:
                    if maxIoU > 0:
                        false_pos_count += 1
                    else:
                        true_pos_count += 1
                    maxIoU = iou
                elif 0 < iou and iou < threshold:
                    # print('False positive: ', iou)
                    false_pos_count += 1
        else:
            print('total miss-----------------------------------------')
            false_pos_count += 1
    false_neg_count = B - true_pos_count
    print('3 - Num truths: ', B)
    print('3 - Num proposals: ', M)
    print('3 - True pos count: ', true_pos_count)
    print('3 - False pos count: ', false_pos_count)
    print('3 - False neg count: ', false_neg_count)
    precision = true_pos_count/(true_pos_count+false_pos_count)
    recall = true_pos_count/(true_pos_count+false_neg_count)
    return (precision, recall)


if __name__ == "__main__":
    # DG sample submissions
    #baseDirectory = '/Users/dlindenbaum/Documents/CosmiQCode_09282015/BEE-CSharp/Data/'
    for image_id in range(1,6):
        truth_fp = ''.join(['Rio/rio_test_aoi',str(image_id),'.geojson'])
        test_fp = ''.join(['Rio_Submission_Testing/Rio_sample_challenge_submission',str(image_id),'.geojson'])
        print('truth_fp=%s' % truth_fp)
        print('test_fp=%s' % test_fp)
        precision, recall = score(test_fp, truth_fp)
        print('Score1 Precision = ', precision)
        print('Score1 Recall = ', recall)
        precision, recall = score2(test_fp, truth_fp)
        print('Score2 Precision = ', precision)
        print('Score2 Recall = ', recall)
        precision, recall = score3(test_fp, truth_fp)
        print('Score3 Precision = ', precision)
        print('Score3 Recall = ', recall)

    # CosmiQ sample submissions
    path = 'Rio_Hand_Truth_AOI1/*.geojson'
    for test_fp in glob(path):
        truth_fp = 'Rio/rio_test_aoi1.geojson'
        print('truth_fp=%s' % truth_fp)
        print('test_fp=%s' % test_fp)
        precision, recall = score(test_fp, truth_fp)
        print('Score1 Precision = ', precision)
        print('Score1 Recall = ', recall)
        precision, recall = score2(test_fp, truth_fp)
        print('Score2 Precision = ', precision)
        print('Score2 Recall = ', recall)
        precision, recall = score3(test_fp, truth_fp)
        print('Score3 Precision = ', precision)
        print('Score3 Recall = ', recall)
