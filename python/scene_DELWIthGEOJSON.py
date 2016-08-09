from __future__ import print_function, division
from glob import glob
from random import random
import os
from numpy import array
from geojson import load
from shapely.geometry import Polygon
import numpy as np
import pandas as pd
import time
import cPickle as pickle

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
    return polys

def get_image_ids(csv_path):
    polys_df = pd.read_csv(csv_path)
    return set(polys_df['ImageId'].tolist())

def load_sorted_polygons(test_csv_path, truth_csv_path):
    # Assumes -
    # 1. Polygons are presorted for descending confindence.
    # 2. Chips with no buildings assign zero for the BuildingId
    return polygonize(test_csv_path), polygonize(truth_csv_path)

def IoU2(test_poly, truth_polys):
    iouList = []
    for idx, truth_poly in enumerate(truth_polys):
        #truth_poly=truth_poly.buffer(0.0)
        #test_poly = test_poly.buffer(0.0)
        #print(idx)
        #if idx == 74:
        #    pass
        intersectionResult = test_poly.intersection(truth_poly)
        if intersectionResult.geom_type == 'Polygon':
            intersectionArea = intersectionResult.area
        else:
            intersectionArea = 0
        #print(intersectionArea)
        unionArea = test_poly.union(truth_poly).area
        #print(unionArea)

        iouList.append(intersectionArea/unionArea)


    return iouList


def score(test_polys, truth_polys):

    # Define internal functions

    IoU = lambda p1, p2: (p1.intersection(p2).area/p1.union(p2).area)
    argmax = lambda iterable, func: max(iterable, key=func)

    # Find detections using threshold/argmax/IoU for test polygons
    true_pos_count = 0
    false_pos_count = 0
    B = len(truth_polys)
    M = len(test_polys)
    idx = 0
    for test_poly in test_polys:
        #print(idx)
        idx = idx +1
        #if idx == 25:
        #    pass
        IoUs = IoU2(test_poly, truth_polys)
        #IoUs = map(lambda x:IoU(test_poly,x),truth_polys)
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

def addbuffer(polys):
    polysNewList = []
    for poly in polys:
        polyNew=poly
        polyNew['poly'] = poly['poly'].buffer(0.0)
        polysNewList.append(polyNew)

    return polysNewList


from osgeo import ogr
def writeToGeoJson(polysList, geoJsonName):
        driver = ogr.GetDriverByName('geojson')
        if os.path.exists(geoJsonName):
            driver.DeleteDataSource(geoJsonName)
        dataSource = driver.CreateDataSource(geoJsonName)
        layer = dataSource.CreateLayer('buildings', geom_type=ogr.wkbPolygon)
        layer.CreateField(ogr.FieldDefn("ImageId", ogr.OFTInteger))
        layer.CreateField(ogr.FieldDefn("ContainsBuildings", ogr.OFTInteger))
        layer.CreateField(ogr.FieldDefn("BuildingId", ogr.OFTInteger))
        emptyCount = 0

        for poly in polysList:
            feature = ogr.Feature(layer.GetLayerDefn())
            feature.SetField("ImageId", poly['ImageId'])
            feature.SetField("BuildingId", poly['BuildingId'])

            if poly['poly'].is_empty:
                emptyCount = emptyCount + 1
                print(emptyCount)
                feature.SetField("ContainsBuildings", 0)
            else:
                feature.SetField("ContainsBuildings", 1)
            polygonImport = ogr.CreateGeometryFromWkt(poly['poly'].wkt)
            feature.SetGeometry(polygonImport)
            # Create the feature in the layer (shapefile)
            layer.CreateFeature(feature)
            # Destroy the feature to free resources
            feature.Destroy()

        dataSource.Destroy()




if __name__ == "__main__":
    true_pos_counts = []
    false_pos_counts = []
    false_neg_counts = []

    test_fp = '/Users/dlindenbaum/Documents/CosmiQCode_09282015/BEE-CSharp/data/Solution_Submission_v4.csv'
    truth_fp = 'data/Solution_v4.csv'

    pickleLocation = 'solution_v4.p'
    t0 = time.time()
    sol_polys = pickle.load(open(pickleLocation, "rb"))
    sol_polys = addbuffer(sol_polys)
    prop_polys = sol_polys

    #prop_polys, sol_polys = load_sorted_polygons(test_fp, truth_fp)
    t1 = time.time()
    total = t1-t0
    print('time of ingest: ', total)

    t0 = time.time()
    test_image_ids = get_image_ids(test_fp)
    bad_count = 0
    for image_id in test_image_ids:
        print('Imaged ID: ', image_id)
        test_polys = []
        truth_polys = []
        image_test_polys = [item for item in prop_polys if item["ImageId"] == image_id]
        for poly in image_test_polys:
            test_polys.append(poly['poly'])
        image_truth_polys = [item for item in sol_polys if item["ImageId"] == image_id]
        if image_truth_polys == []:
            true_pos_count = 0
            false_pos_count = len(image_test_polys)
            false_neg_count = 0
        else:
            for poly in image_truth_polys:
                truth_polys.append(poly['poly'])
            true_pos_count, false_pos_count, false_neg_count = score(test_polys, truth_polys)
        true_pos_counts.append(true_pos_count)
        false_pos_counts.append(false_pos_count)
        false_neg_counts.append(false_neg_count)
        if (sum(true_pos_counts) > 0 ) and ((sum( false_neg_counts ) > 0 ) and (sum(false_pos_counts) > 0)):
            precision = float(sum(true_pos_counts))/float(sum(true_pos_counts)+sum(false_pos_counts))
            recall = float(sum(true_pos_counts))/float(sum(true_pos_counts)+sum(false_neg_counts))
            F1score  = 2.0*precision*recall/(precision+recall)
            print('F1 Score: ', F1score)
            print('bad count: ', bad_count)
    t1 = time.time()
    total = t1-t0
    print('time of evaluation: ', total)
