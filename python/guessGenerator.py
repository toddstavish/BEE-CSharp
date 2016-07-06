#%% Import Calls
import os
import ogr
import osr
import subprocess
import gdal
import csv
import cv2
import math
import datetime
from pixel import geoUtils
import numpy as np
import random
##




## createEnvelope
def createEnvelope(polyGeom, performInUTMSpace=True, wgs84Input=True):
    if performInUTMSpace and wgs84Input:
        transform_WGS84_To_UTM, transform_UTM_To_WGS84 = geoUtils.createUTMTransform(polyGeom)
        polyGeom.Transform(transform_WGS84_To_UTM)

    geom_Envelope = polyGeom.GetEnvelope()
    minX = geom_Envelope[0]
    minY = geom_Envelope[2]
    maxX = geom_Envelope[1]
    maxY = geom_Envelope[3]

    ring = ogr.Geometry(ogr.wkbLinearRing)
    ring.AddPoint(minX,minY)
    ring.AddPoint(minX,maxY)
    ring.AddPoint(maxX,maxY)
    ring.AddPoint(maxX,minY)
    ring.AddPoint(minX,minY)
    polyEnvelope = ogr.Geometry(ogr.wkbPolygon)
    polyEnvelope.AddGeometry(ring)

    if performInUTMSpace and wgs84Input:
        polyGeom.Transform(transform_UTM_To_WGS84)
        polyEnvelope.Transform(transform_UTM_To_WGS84)

    return polyEnvelope


## createBufferMeters
def createBufferMeters(polyGeom, bufferDistanceMeters, wgs84Input=True):
    if wgs84Input:
        transform_WGS84_To_UTM, transform_UTM_To_WGS84 = geoUtils.createUTMTransform(polyGeom)
        polyGeom.Transform(transform_WGS84_To_UTM)
    polyBuffer = polyGeom.Buffer(bufferDistanceMeters)


    if wgs84Input:
        polyGeom.Transform(transform_UTM_To_WGS84)
        polyBuffer.Transform(transform_UTM_To_WGS84)

    return polyBuffer

## createBufferPercent

def createBufferPercent(polyGeom, bufferperCent, wgs84Input=True):
    if wgs84Input:
        transform_WGS84_To_UTM, transform_UTM_To_WGS84 = geoUtils.createUTMTransform(polyGeom)
        polyGeom.Transform(transform_WGS84_To_UTM)
    polyArea = polyGeom.GetArea()
    polylength = math.sqrt(polyArea)
    polyBuffer = polyGeom.Buffer(polylength*bufferperCent)
    print polylength*bufferperCent
    if wgs84Input:
        polyGeom.Transform(transform_UTM_To_WGS84)
        polyBuffer.Transform(transform_UTM_To_WGS84)

    return polyBuffer



## translateMeters

def createTranslateMeters(polyGeom, translateDistanceMetersX,
                          translateDistanceMetersY, wgs84Input=True):
    if wgs84Input:
        transform_WGS84_To_UTM, transform_UTM_To_WGS84 = geoUtils.createUTMTransform(polyGeom)
        polyGeom.Transform(transform_WGS84_To_UTM)
    ring = ogr.Geometry(ogr.wkbLinearRing)
    geomRing = polyGeom.GetGeometryRef(0)
    for i in range(0, geomRing.GetPointCount()):
        # GetPoint returns a tuple not a Geometry
        pt = geomRing.GetPoint(i)
        ring.AddPoint(pt[0]+translateDistanceMetersX,
                      pt[1]+translateDistanceMetersY)


    polyTranslate = ogr.Geometry(ogr.wkbPolygon)
    polyTranslate.AddGeometry(ring)




    if wgs84Input:
        polyGeom.Transform(transform_UTM_To_WGS84)
        polyTranslate.Transform(transform_UTM_To_WGS84)

    return polyTranslate



def createNewFileFromGuess(sourceFile,dstFileName, guessMultiple=3):
    dataSource = ogr.Open(sourceFile, 0)
    srcLayer = dataSource.GetLayer()
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)
    # Create the output shapefile
    geoJSONdriver = ogr.GetDriverByName("GeoJson")
    if os.path.exists(dstFileName):
        geoJSONdriver.DeleteDataSource(dstFileName)
    outDataSource = geoJSONdriver.CreateDataSource(dstFileName)
    outLayer = outDataSource.CreateLayer(dstFileName, srs, geom_type=ogr.wkbPolygon)
    # Create the feature and set values
    featureDefn = outLayer.GetLayerDefn()
    numGuesses = random.randint(0, 3*srcLayer.GetFeatureCount())
    for x in xrange(numGuesses):
        srcFeature = srcLayer.GetFeature(np.random.choice(srcLayer.GetFeatureCount()))
        srcGeom = srcFeature.GetGeometryRef()
        print srcGeom.ExportToJson()

        translateType = random.randint(0,2)

        if translateType == 0:
            bufferPercent = np.random.normal(0, 0.25)
            dstGeom = createBufferPercent(srcGeom, bufferPercent)
        elif translateType == 1:
            bufferDistanceMeters = np.random.normal(0, 10)
            dstGeom = createBufferMeters(srcGeom, bufferDistanceMeters)
        elif translateType == 2:
            translateX = np.random.normal(0, 30)
            translateY = np.random.normal(0, 30)
            dstGeom = createTranslateMeters(srcGeom, translateX, translateY)
        print dstGeom.ExportToJson()
        feature = ogr.Feature(featureDefn)
        feature.SetGeometry(dstGeom)
        outLayer.CreateFeature(feature)

    dataSource.Destroy()
    outDataSource.Destroy()


def createEnvelopeTest(sourceFile,dstFileName):
    dataSource = ogr.Open(sourceFile, 0)
    srcLayer = dataSource.GetLayer()
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)
    # Create the output shapefile
    geoJSONdriver = ogr.GetDriverByName("GeoJson")
    if os.path.exists(dstFileName):
        geoJSONdriver.DeleteDataSource(dstFileName)
    outDataSource = geoJSONdriver.CreateDataSource(dstFileName)
    outLayer = outDataSource.CreateLayer(dstFileName, srs, geom_type=ogr.wkbPolygon)
    # Create the feature and set values
    featureDefn = outLayer.GetLayerDefn()
    numPolys = srcLayer.GetFeatureCount()
    for x in xrange(numPolys):
        srcFeature = srcLayer.GetFeature(x)
        srcGeom = srcFeature.GetGeometryRef()

        translateType = random.randint(0,2)
        dstGeom = createEnvelope(srcGeom, performInUTMSpace=True, wgs84Input=True)
        feature = ogr.Feature(featureDefn)
        feature.SetGeometry(dstGeom)
        outLayer.CreateFeature(feature)

    dataSource.Destroy()
    outDataSource.Destroy()

def createUnitTest(sourceFile,dstFileName):
    dataSource = ogr.Open(sourceFile, 0)
    srcLayer = dataSource.GetLayer()
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)
    # Create the output shapefile
    geoJSONdriver = ogr.GetDriverByName("GeoJson")
    if os.path.exists(dstFileName):
        geoJSONdriver.DeleteDataSource(dstFileName)
    outDataSource = geoJSONdriver.CreateDataSource(dstFileName)
    outLayer = outDataSource.CreateLayer(dstFileName, srs, geom_type=ogr.wkbPolygon)
    # Create the feature and set values

    featureDefn = outLayer.GetLayerDefn()
    numGuesses = srcLayer.GetFeatureCount()

    featureList = np.random.choice(numGuesses, replace=False)
    for x in xrange(numGuesses):

        srcFeature = srcLayer.GetFeature(np.random.choice(srcLayer.GetFeatureCount()))
        srcGeom = srcFeature.GetGeometryRef()
        print srcGeom.ExportToJson()

        translateType = random.randint(0,2)

        if translateType == 0:
            bufferPercent = np.random.normal(0, 0.25)
            dstGeom = createBufferPercent(srcGeom, bufferPercent)
        elif translateType == 1:
            bufferDistanceMeters = np.random.normal(0, 10)
            dstGeom = createBufferMeters(srcGeom, bufferDistanceMeters)
        elif translateType == 2:
            translateX = np.random.normal(0, 30)
            translateY = np.random.normal(0, 30)
            dstGeom = createTranslateMeters(srcGeom, translateX, translateY)
        print dstGeom.ExportToJson()
        feature = ogr.Feature(featureDefn)
        feature.SetGeometry(dstGeom)
        outLayer.CreateFeature(feature)

    dataSource.Destroy()
    outDataSource.Destroy()





if __name__ == '__main__':
    ## Load geoJSON:
    bufferPercent=0.10
    sourceFileName = '/Users/dlindenbaum/Documents/CosmiQCode_09282015/BEE-CSharp/data/Rio/rio_test_aoi2.geojson'
    dstFolder = '/Users/dlindenbaum/Documents/CosmiQCode_09282015/BEE-CSharp/data/Rio_Submission_Testing_CQW'
    dstFolderUnitTest = '/Users/dlindenbaum/Documents/CosmiQCode_09282015/BEE-CSharp/data/Rio_Submission_Testing_UnitTest'
    dstFileBase = os.path.join(dstFolder, os.path.basename(sourceFileName))
    numberOfTests = 50
    for testNum in xrange(numberOfTests):
        dstFileName = dstFileBase.replace('.geojson', '_test{}.geojson'.format(testNum))
        createNewFileFromGuess(sourceFileName, dstFileName, guessMultiple=3)


    dstFileName = dstFileBase.replace('.geojson', '_Envelope.geojson'.format(testNum))
    createEnvelopeTest(sourceFileName, dstFileName, guessMultiple=3)


    createUnitTest(sourceFileName, dstFileName)



















