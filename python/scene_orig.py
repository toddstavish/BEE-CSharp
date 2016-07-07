from __future__ import print_function, division
from glob import glob
from random import random
from geojson import load
from shapely.geometry import Polygon
from skimage import draw
from rtree import index
import numpy as np
import os

<<<<<<< HEAD
def remove_dupes(test_polys):
    unique = []
    for test_poly in test_polys:
        if test_poly not in unique:
            unique.append(test_poly)
        else:
            print('Removed duplicate.')
    return unique


def score_rtree(test_geojson_path, truth_geojson_path):

    # Define internal functions
    IoU = lambda p1, p2: p1.intersection(p2).area/p1.union(p2).area
    polygonize = lambda feature: Polygon(feature['geometry']['coordinates'][0])

    # Convert geojson files of features/geometries to arrays of polygons
    test_features = load(open(test_geojson_path), encoding='latin-1')
    truth_features = load(open(truth_geojson_path), encoding='latin-1')
    test_polys = remove_dupes([polygonize(f) for f in test_features['features']])
    test_polys = [(i, p.bounds, p) for i, p in enumerate(test_polys)]
    truth_polys = [polygonize(f) for f in truth_features['features']]

    # Use a geospatial index to compare the polygons
    idx = index.Index(interleaved=False)
    for i, bounds, test_poly in test_polys:
        idx.insert(i, bounds, obj=test_poly)

    threshold = 0.5
    true_pos_count = 0
    false_pos_count = 0
    B = len(truth_polys)
    for truth_poly in truth_polys:
        maxIoU = 0
        for test_poly in idx.intersection(truth_poly.bounds, objects=True):
            iou = IoU(test_poly.object, truth_poly)
            if iou >= threshold:
                maxIoU = iou
                print('Max: ', iou)
            elif iou != 0:
                print('False positive: ', iou)
                false_pos_count += 1
        if maxIoU != 0:
            true_pos_count += 1
    false_neg_count = B - true_pos_count
    print('rtree: True pos count: ', true_pos_count)
    print('rtree: False pos count: ', false_pos_count)
    print('rtree: False neg count: ', false_neg_count)
    precision = true_pos_count/(true_pos_count+false_pos_count)
    recall = true_pos_count/(true_pos_count+false_neg_count)
    return (precision, recall)


def score_max(test_geojson_path, truth_geojson_path):
=======
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

def getPolys(geojson_path):
    polyList = []
    features = load(open(geojson_path), encoding='latin-1')
    for f in features['features']:
        geometry = f['geometry']['coordinates'][0]
        polyType = f['geometry']['type']

        if geometry:
            if polyType == 'Polygon':
                poly=Polygon(geometry)
                polyList.append(poly)

    return polyList

def score(test_geojson_path, truth_geojson_path):
>>>>>>> 0c20647c9baf519dceb5c21dbdb82a25ecd8c236

    # Define internal functions
    IoU = lambda p1, p2: p1.intersection(p2).area/p1.union(p2).area
    polygonize = lambda feature: Polygon(feature['geometry']['coordinates'][0])

    # Convert geojson files of features/geometries to arrays of polygons
    #test_features = load(open(test_geojson_path), encoding='latin-1')
    #truth_features = load(open(truth_geojson_path), encoding='latin-1')
    #test_polys = [polygonize(f) for f in test_features['features']]
    #truth_polys = [polygonize(f) for f in truth_features['features']]
    test_polys = getPolys(test_geojson_path)
    truth_polys = getPolys(truth_geojson_path)
    # Generate artifical confidences and sort
    test_polys =  [[random(), test_poly] for test_poly in test_polys]
    test_polys = sorted(test_polys, key=lambda l:l[0], reverse=True)

    # Compare polygons using threshold/argmax/IoU
    threshold = 0.5
    true_pos_count = 0
    false_pos_count = 0
    B = len(truth_polys)
    for test_poly in test_polys:
        IoUs = map(lambda x:IoU(test_poly[1],x),truth_polys)
        maxIoU = max(IoUs)
        if maxIoU >= threshold:
            true_pos_count += 1
            del truth_polys[np.argmax(IoUs)]
        else:
            false_pos_count += 1
    false_neg_count = B - true_pos_count
<<<<<<< HEAD
    print('Max: True pos count: ', true_pos_count)
    print('Max: False pos count: ', false_pos_count)
    print('Max: False neg count: ', false_neg_count)
    precision = true_pos_count/(true_pos_count+false_pos_count)
    recall = true_pos_count/(true_pos_count+false_neg_count)
=======
    print('True pos count: ', true_pos_count)
    print('False pos count: ', false_pos_count)
    print('False neg count: ', false_neg_count)

    if (true_pos_count+false_pos_count) != 0:
        precision = true_pos_count/(true_pos_count+false_pos_count)
    else:
        precision = 0

    if (true_pos_count+false_neg_count) !=0:
        recall = true_pos_count/(true_pos_count+false_neg_count)
>>>>>>> 0c20647c9baf519dceb5c21dbdb82a25ecd8c236
    return (precision, recall)

def createMarkupFile(fileSavePath, precisionList, recallList, f1ScoreList, pathList, truthFile, gitHubPath):
    target = open(fileSavePath, 'w')
    target.write('# Testing of {} ->\n'.format(truthFile))
    target.write('## [Truth Polygon Map]({})\n'.format(os.path.join(gitHubPath,truthFile)))
    target.write('Tests below sorted in order of F1Score \n')
    target.write('\n')
    sort_index = np.array(f1ScoreList).argsort()[::-1]
    testCount = 1
    for idx in sort_index:
        target.write('# Test {} ->\n'.format(testCount))
        target.write('## [Test Polygon Map]({})\n'.format(os.path.join(gitHubPath, pathList[idx])))
        target.write('F1Score = {}\n'.format(f1ScoreList[idx]))
        target.write('Precision = {}\n'.format(precisionList[idx]))
        target.write('Recall = {}\n'.format(recallList[idx]))
        testCount=testCount+1
        target.write('\n')

    target.close()



if __name__ == "__main__":
    # DG sample submissions
    #baseDirectory = '/Users/dlindenbaum/Documents/CosmiQCode_09282015/BEE-CSharp/Data/'
    gitHubDirectory = 'https://github.com/toddstavish/BEE-CSharp/blob/master/data/'
    evalFileName = 'Rio_Submission_Testing_CQW/rio_test_aoiResults.md'
    for image_id in range(1,6):
        truth_fp = ''.join(['Rio/rio_test_aoi',str(image_id),'.geojson'])
        test_fp = ''.join(['Rio_Submission_Testing/Rio_sample_challenge_submission',str(image_id),'.geojson'])
        print('truth_fp=%s' % truth_fp)
        print('test_fp=%s' % test_fp)
        precision, recall = score_max(test_fp, truth_fp)
        print('Max: Precision = ', precision)
        print('Max: Recall = ', recall)
        precision, recall = score_rtree(test_fp, truth_fp)
        print('Rtree: Precision = ', precision)
        print('Rtree: Recall = ', recall)

    # CosmiQ sample submissions
    path = 'Rio_Hand_Truth_AOI1/*.geojson'
    for test_fp in glob(path):
        truth_fp = 'Rio/rio_test_aoi1.geojson'
        print('truth_fp=%s' % truth_fp)
        print('test_fp=%s' % test_fp)
<<<<<<< HEAD
        precision, recall = score_max(test_fp, truth_fp)
        print('Max: Precision = ', precision)
        print('Max: Recall = ', recall)
=======
        precision, recall = score(test_fp, truth_fp)
        print('Precision = ', precision)
        print('Recall = ', recall)

    # CosmiQ sample submissions
    path = 'Rio_Submission_Testing_CQW/rio_test_aoi2*'

    precisionList = []
    recallList    = []
    f1ScoreList   = []
    pathList      = glob(path)
    for test_fp in pathList:
        truth_fp = 'Rio/rio_test_aoi2.geojson'
        print('truth_fp=%s' % truth_fp)
        print('test_fp=%s' % test_fp)
        precision, recall = score(test_fp, truth_fp)
        if precision+recall != 0:
            F1score  = precision*recall/(precision+recall)
        else:
            F1score = 0
        precisionList.append(precision)
        recallList.append(recall)
        f1ScoreList.append(F1score)

        print('Precision = ', precision)
        print('Recall = ', recall)

    createMarkupFile(evalFileName, precisionList, recallList, f1ScoreList, pathList, truth_fp, gitHubDirectory)


>>>>>>> 0c20647c9baf519dceb5c21dbdb82a25ecd8c236
