# -*- coding: latin-1 -*-


import sys
import os
import csv
import numpy as np
import ogr
import osr
import gdal
from shutil import copyfile
from geojson import load
from shapely.geometry import box, Polygon


def latLonToPixel(lat, lon, inputRaster='', targetSR='', geomTransform=''):
    sourceSR = osr.SpatialReference()
    sourceSR.ImportFromEPSG(4326)

    geom = ogr.Geometry(ogr.wkbPoint)
    geom.AddPoint(lon, lat)

    if targetSR == '':
        srcRaster = gdal.Open(inputRaster)
        targetSR = osr.SpatialReference()
        targetSR.ImportFromWkt(srcRaster.GetProjectionRef())
    coordTrans = osr.CoordinateTransformation(sourceSR,targetSR)
    if geomTransform == '':
        srcRaster = gdal.Open(inputRaster)
        transform = srcRaster.GetGeoTransform()
    else:
        transform = geomTransform

    xOrigin = transform[0]
    # print xOrigin
    yOrigin = transform[3]
    # print yOrigin
    pixelWidth = transform[1]
    # print pixelWidth
    pixelHeight = transform[5]
    # print pixelHeight
    geom.Transform(coordTrans)
    # print geom.GetPoint()
    xPix = (geom.GetPoint()[0]-xOrigin)/pixelWidth
    yPix = (geom.GetPoint()[1]-yOrigin)/pixelHeight

    return (xPix, yPix)

# The following method translates given latitude/longitude pairs into pixel locations on a given GEOTIF
# INPUTS: geotifAddr - The file location of the GEOTIF
#      latLonPairs - The decimal lat/lon pairings to be translated in the form [[lat1,lon1],[lat2,lon2]]
# OUTPUT: The pixel translation of the lat/lon pairings in the form [[x1,y1],[x2,y2]]
# NOTE:   This method does not take into account pixel size and assumes a high enough
#     image resolution for pixel size to be insignificant
def latLonToPixel2(geotifAddr, latLonPairs):
    # Load the image dataset
    ds = gdal.Open(geotifAddr)
    # Get a geo-transform of the dataset
    gt = ds.GetGeoTransform()
    # Create a spatial reference object for the dataset
    srs = osr.SpatialReference()
    srs.ImportFromWkt(ds.GetProjection())
    # Set up the coordinate transformation object
    srsLatLong = srs.CloneGeogCS()
    ct = osr.CoordinateTransformation(srsLatLong,srs)
    # Go through all the point pairs and translate them to latitude/longitude pairings
    pixelPairs = []
    for point in latLonPairs:
        # Change the point locations into the GeoTransform space
        (point[1],point[0],holder) = ct.TransformPoint(point[1],point[0])
        # Translate the x and y coordinates into pixel values
        x = (point[1]-gt[0])/gt[1]
        y = (point[0]-gt[3])/gt[5]
        # Add the point to our return array
        pixelPairs.append([int(x),int(y)])
    return pixelPairs

def pixelToLatLon(xPix, yPix, inputRaster, targetSR=''):
    if targetSR == '':
        targetSR = osr.SpatialReference()
        targetSR.ImportFromEPSG(4326)

    geom = ogr.Geometry(ogr.wkbPoint)
    srcRaster = gdal.Open(inputRaster)
    sourceSR = osr.SpatialReference()
    sourceSR.ImportFromWkt(srcRaster.GetProjectionRef())
    coordTrans = osr.CoordinateTransformation(sourceSR,targetSR)

    transform = srcRaster.GetGeoTransform()
    xOrigin = transform[0]
    yOrigin = transform[3]
    pixelWidth = transform[1]
    pixelHeight = transform[5]

    xCoord = (xPix*pixelWidth)+xOrigin
    yCoord = (yPix*pixelHeight)+yOrigin
    geom.AddPoint(xCoord, yCoord)
    geom.Transform(coordTrans)
    return (geom.GetX(), geom.GetY())

# The following method translates given pixel locations into latitude/longitude locations on a given GEOTIF
# INPUTS: geotifAddr - The file location of the GEOTIF
#      pixelPairs - The pixel pairings to be translated in the form [[x1,y1],[x2,y2]]
# OUTPUT: The lat/lon translation of the pixel pairings in the form [[lat1,lon1],[lat2,lon2]]
# NOTE:   This method does not take into account pixel size and assumes a high enough
#     image resolution for pixel size to be insignificant
def pixelToLatLon2(geotifAddr,pixelPairs):
    # Load the image dataset
    ds = gdal.Open(geotifAddr)
    # Get a geo-transform of the dataset
    gt = ds.GetGeoTransform()
    # Create a spatial reference object for the dataset
    srs = osr.SpatialReference()
    srs.ImportFromWkt(ds.GetProjection())
    # Set up the coordinate transformation object
    srsLatLong = srs.CloneGeogCS()
    ct = osr.CoordinateTransformation(srs,srsLatLong)
    # Go through all the point pairs and translate them to pixel pairings
    latLonPairs = []
    for point in pixelPairs:
        # Translate the pixel pairs into untranslated points
        ulon = point[0]*gt[1]+gt[0]
        ulat = point[1]*gt[5]+gt[3]
        # Transform the points to the space
        (lon,lat,holder) = ct.TransformPoint(ulon,ulat)
        # Add the point to our return array
        latLonPairs.append([lat,lon])

    return latLonPairs

def geoPolygonToPixelPolygonWKT(geom, inputRaster, targetSR, geomTransform):
    # Returns Pixel Coordinate List and GeoCoordinateList

    polygonPixBufferList = []
    polygonPixBufferWKTList = []
    if geom.GetGeometryName()=='POLYGON':
        polygonPix = ogr.Geometry(ogr.wkbPolygon)
        for ring in geom:
            # GetPoint returns a tuple not a Geometry
            ringPix = ogr.Geometry(ogr.wkbLinearRing)

            for pIdx in xrange(ring.GetPointCount()):
                    lon, lat, z = ring.GetPoint(pIdx)
                    xPix, yPix = latLonToPixel(lat, lon, inputRaster, targetSR, geomTransform)
                    ringPix.AddPoint(xPix, yPix)

            polygonPix.AddGeometry(ringPix)
        polygonPixBuffer  = polygonPix.Buffer(0.0)
        polygonPixBufferList.append([polygonPixBuffer, geom])

    elif geom.GetGeometryName() == 'MULTIPOLYGON':


        for poly in geom:
            polygonPix = ogr.Geometry(ogr.wkbPolygon)
            for ring in poly:
                # GetPoint returns a tuple not a Geometry
                ringPix = ogr.Geometry(ogr.wkbLinearRing)

                for pIdx in xrange(ring.GetPointCount()):
                    lon, lat, z = ring.GetPoint(pIdx)
                    xPix, yPix = latLonToPixel(lat, lon, inputRaster, targetSR, geomTransform)
                    ringPix.AddPoint(xPix, yPix)

                polygonPix.AddGeometry(ringPix)
                polygonPixBuffer = polygonPix.Buffer(0.0)
            polygonPixBufferList.append([polygonPixBuffer, geom])


    for polygonTest in polygonPixBufferList:
        if polygonTest[0].GetGeometryName() == 'POLYGON':
            polygonPixBufferWKTList.append([polygonTest[0].ExportToWkt(), polygonTest[1].ExportToWkt()])
        elif polygonTest[0].GetGeometryName() == 'MULTIPOLYGON':
            for polygonTest2 in polygonTest[0]:
                polygonPixBufferWKTList.append([polygonTest2.ExportToWkt(), polygonTest[1].ExportToWkt()])





    return polygonPixBufferWKTList











if __name__ == "__main__":



    privateList = ['013022232030.tif',
                '013022232031.tif',
                '013022232032.tif',
                '013022232033.tif',
                '013022232120.tif',
                '013022232122.tif',
                '013022232210.tif',
                '013022232211.tif',
                '013022232300.tif'
                   ]


    ## write to files





    ## writetoDirectory
    public_8bandRasterLocation = '../data/spacenet/stageToAWS/processedData/8band/'
    public_3bandRasterLocation = '../data/spacenet/stageToAWS/processedData/3band/'
    public_geoJsonFileLocation = '../data/spacenet/stageToAWS/processedData/vectorData/geoJson/'
    public_summaryFiles        = '../data/spacenet/stageToAWS/processedData/vectorData/summaryData/'

    private_8bandRasterLocation = '../data/spacenet/private/processedData/8band/'
    private_3bandRasterLocation = '../data/spacenet/private/processedData/3band/'
    private_geoJsonFileLocation = '../data/spacenet/private/processedData/vectorData/geoJson'
    private_summaryFiles        = '../data/spacenet/private/processedData/vectorData/summaryData/'

    csvFileTotalName_3Band = '../data/spacenet/all_polygons_solution_3Band.csv'
    csvFilePublicName_3Band = os.path.join(public_summaryFiles, 'public_polygons_solution_3Band.csv')
    csvFilePrivateName_3Band = os.path.join(private_summaryFiles, 'private_polygons_solution_3Band.csv')

    csvFileTotalName_8Band = '../data/spacenet/all_polygons_solution_8Band.csv'
    csvFilePublicName_8Band = os.path.join(public_summaryFiles, 'public_polygons_solution_8Band.csv')
    csvFilePrivateName_8Band = os.path.join(private_summaryFiles, 'private_polygons_solution_8Band.csv')

    csvFileImageKeyIndexName = '../data/imageKeyIndex.csv'

    if not os.path.exists(public_8bandRasterLocation):
        os.makedirs(public_8bandRasterLocation)

    if not os.path.exists(public_3bandRasterLocation):
        os.makedirs(public_3bandRasterLocation)

    if not os.path.exists(public_geoJsonFileLocation):
        os.makedirs(public_geoJsonFileLocation)

    if not os.path.exists(public_summaryFiles):
        os.makedirs(public_summaryFiles)

    if not os.path.exists(private_8bandRasterLocation):
        os.makedirs(private_8bandRasterLocation)

    if not os.path.exists(private_3bandRasterLocation):
        os.makedirs(private_3bandRasterLocation)

    if not os.path.exists(private_geoJsonFileLocation):
        os.makedirs(private_geoJsonFileLocation)

    if not os.path.exists(private_summaryFiles):
        os.makedirs(private_summaryFiles)


    aoiFile = '../data/chipNames_inAOI.txt'
    imageFileList = []
    with open(aoiFile, 'rb') as csvfile:
        fileReader = csv.reader(csvfile, delimiter=' ', quotechar='|')
        for row in fileReader:
            imageFileList.append(row[0])
    privimageId = 0
    pubimageId = 0
    imageFileListTranslate = []
    imageFileIdx = 0
    for imageFile in imageFileList:
        imageFileIdx = imageFileIdx+1
        print(imageFileIdx)

        imageFileSplt = imageFile.split('_')
        if "{}.tif".format(imageFileSplt[1]) in privateList:
            usage='Private'
            print(usage)
            privimageId = privimageId + 1
            imageFileBase = "{}_Private_img{}".format(imageFileSplt[1], privimageId)
        else:
            usage='Public'
            pubimageId = pubimageId+1
            imageFileBase = "{}_Public_img{}".format(imageFileSplt[1], pubimageId)

        imageFileListTranslate.append([
                                imageFile,
                                usage,
                                imageFileBase,
                                "3band_{}.tif".format(imageFileBase),
                                "3band_{}_Pix.geojson".format(imageFileBase),
                                "{}_Geo.geojson".format(imageFileBase),
                                "8band_{}.tif".format(imageFileBase),
                                "8band_{}_Pix.geojson".format(imageFileBase),
                                "{}_Geo.geojson".format(imageFileBase)
                                ])

    with open(csvFileImageKeyIndexName, 'wb') as csvfileImageKey:
        writerImageKey = csv.writer(csvfileImageKey, delimiter=',', lineterminator='\n')
        writerImageKey.writerow(['srcRaster',
                                 'Usage',
                                 'imageFileBase'
                                 '3BandTiffName',
                                 '3BandGeoJsonPixName',
                                 '3BandGeoJsonGeoName',
                                 '8BandTiffName',
                                 '8BandGeoJsonPixName',
                                 '8BandGeoJsonGeoName',
                                 ])
        for imageFileTranslate in imageFileListTranslate:
            writerImageKey.writerow(imageFileTranslate)

    with open(csvFileTotalName_3Band, 'wb') as csvfileTotal, \
            open(csvFileTotalName_8Band, 'wb') as csvfileTotal_8Band, \
            open(csvFilePublicName_3Band, 'wb') as csvfilePublic_3Band, \
            open(csvFilePrivateName_3Band, 'wb') as csvfilePrivate_3Band, \
            open(csvFilePublicName_8Band, 'wb') as csvfilePublic_8Band, \
            open(csvFilePrivateName_8Band, 'wb') as csvfilePrivate_8Band:

        # instantiate writers
        writerTotal         = csv.writer(csvfileTotal, delimiter=',',lineterminator='\n')
        writerTotal_8Band   = csv.writer(csvfileTotal_8Band, delimiter=',',lineterminator='\n')


        writerPublic_3band = csv.writer(csvfilePublic_3Band, delimiter=',', lineterminator='\n')
        writerPrivate_3band = csv.writer(csvfilePrivate_3Band, delimiter=',', lineterminator='\n')

        writerPublic_8band = csv.writer(csvfilePublic_8Band, delimiter=',', lineterminator='\n')
        writerPrivate_8band = csv.writer(csvfilePrivate_8Band, delimiter=',', lineterminator='\n')


        writerTotal.writerow(['ImageId','BuildingId', 'PolygonWKT_Pix', 'PolygonWKT_Geo', 'Usage'])
        writerTotal_8Band.writerow(['ImageId','BuildingId', 'PolygonWKT_Pix', 'PolygonWKT_Geo', 'Usage'])


        writerPublic_3band.writerow(['ImageId', 'BuildingId',  'PolygonWKT_Pix', 'PolygonWKT_Geo'])
        writerPrivate_3band.writerow(['ImageId','BuildingId',  'PolygonWKT_Pix', 'PolygonWKT_Geo'])

        writerPublic_8band.writerow(['ImageId', 'BuildingId', 'PolygonWKT_Pix', 'PolygonWKT_Geo'])
        writerPrivate_8band.writerow(['ImageId', 'BuildingId', 'PolygonWKT_Piz', 'PolygonWKT_Geo'])


        max_buildings = 0
        num_imgs_no_buildings = 0

        #imagefiles = sorted(os.listdir('image_chips_filtered/3band'))
        #geojsonfiles = sorted(os.listdir('image_chips_filtered/geojsons/'))


        errors = []
        for imageFileTranslate in imageFileListTranslate:
            

            usage = imageFileTranslate[1]
            truthJsonFp = ''.join(['../data/chipsBuildings/',imageFileTranslate[0].replace('.tif', '.geojson')])
            inputRaster = ''.join(['../data/image_chips/3band/',imageFileTranslate[0]])
            eightbandRaster = ''.join(['../data/image_chips/8band/',imageFileTranslate[0]])

            print('reading truthJsonFp=%s' % truthJsonFp)
            # load GeoJSON file

            dataSource = ogr.Open(truthJsonFp, 0)
            layer = dataSource.GetLayer()
            print(layer.GetFeatureCount())
            building_id = 0
            # check if geoJsonisEmpty
            if layer.GetFeatureCount()>0:
                srcRaster = gdal.Open(inputRaster)
                targetSR = osr.SpatialReference()
                targetSR.ImportFromWkt(srcRaster.GetProjectionRef())
                geomTransform = srcRaster.GetGeoTransform()

                srcRaster_8band = gdal.Open(eightbandRaster)
                targetSR_8band = osr.SpatialReference()
                targetSR_8band.ImportFromWkt(srcRaster_8band.GetProjectionRef())
                geomTransform_8band = srcRaster_8band.GetGeoTransform()


                for feature in layer:
                    building_id = building_id+1
                    geom = feature.GetGeometryRef()

                    ## Calculate 3 band
                    polygonWKTList = geoPolygonToPixelPolygonWKT(geom, inputRaster, targetSR, geomTransform)

                    for polygonWKT in polygonWKTList:
                        outputList = [imageFileTranslate[2], building_id, polygonWKT[0], polygonWKT[1], usage]
                        writerTotal.writerow(outputList)
                        if usage == 'Private':
                            writerPrivate_3band.writerow(outputList[:-1])
                        else:
                            writerPublic_3band.writerow(outputList[:-1])
                    ## Calculate 3 band
                    polygonWKTList_8Band = geoPolygonToPixelPolygonWKT(geom, eightbandRaster, targetSR_8band, geomTransform_8band)

                    for polygonWKT in polygonWKTList_8Band:
                        outputList = [imageFileTranslate[2], building_id, polygonWKT[0], polygonWKT[1], usage]
                        writerTotal_8Band.writerow(outputList)
                        if usage == 'Private':
                            writerPrivate_8band.writerow(outputList[:-1])
                        else:
                            writerPublic_8band.writerow(outputList[:-1])





            else:
                outputList = [imageFileTranslate[2], -1, Polygon([(0, 0), (0, 0), (0, 0)]).wkt, Polygon([(0, 0), (0, 0), (0, 0)]).wkt, usage]
                writerTotal.writerow(outputList)
                writerTotal_8Band.writerow(outputList)
                if usage == 'Private':
                    writerPrivate_3band.writerow(outputList[:-1])
                else:
                    writerPublic_3band.writerow(outputList[:-1])

    ### do file transfer



    for imageFileTranslate in imageFileListTranslate:
        print('startingCopying')

        usage = imageFileTranslate[1]
        truthJsonFp = ''.join(['../data/chipsBuildings/', imageFileTranslate[0].replace('.tif', '.geojson')])
        inputRaster = ''.join(['../data/image_chips/3band/', imageFileTranslate[0]])
        eightbandRaster = ''.join(['../data/image_chips/8band/', imageFileTranslate[0]])


        if usage == 'Public':

            # cp 3bandrasterFile to public/private and rename
            copyfile(inputRaster, os.path.join(public_3bandRasterLocation, imageFileTranslate[3]))

            # cp 8bandrasterFile to public/private and rename
            copyfile(eightbandRaster, os.path.join(public_8bandRasterLocation, imageFileTranslate[6]))

            # cp cpGeoJson to 3band/8band public/private
            copyfile(truthJsonFp, os.path.join(public_geoJsonFileLocation, imageFileTranslate[5]))

        else:
            # cp 3bandrasterFile to public/private and rename
            copyfile(inputRaster, os.path.join(private_3bandRasterLocation, imageFileTranslate[3]))

            # cp 8bandrasterFile to public/private and rename
            copyfile(eightbandRaster, os.path.join(private_8bandRasterLocation, imageFileTranslate[6]))

            # cp cpGeoJson to 3band/8band public/private
            copyfile(truthJsonFp, os.path.join(private_geoJsonFileLocation, imageFileTranslate[5]))












