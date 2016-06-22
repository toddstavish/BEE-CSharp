import os
import csv
import ogr
import osr
import gdal
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
    yOrigin = transform[3]
    pixelWidth = transform[1]
    pixelHeight = transform[5]
    geom.Transform(coordTrans)
    xPix = (geom.GetPoint()[0]-xOrigin)/pixelWidth
    yPix = (geom.GetPoint()[1]-yOrigin)/pixelHeight

    return (xPix, yPix)


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
    return (geom.GetY(), geom.GetX())

if __name__ == "__main__":

    with open('rio_test.csv', 'wb') as csvfile:

        for image_id in range(1,4):
            truthJsonFp = ''.join(['Rio/rio_test_aoi',str(image_id),'.geojson'])
            inputRaster = ''.join(['Rio/rio_mosaic_clip_aoi',str(image_id),'.TIF'])

            print('reading truthJsonFp=%s' % truthJsonFp)
            # load GeoJSON file
            f = open(truthJsonFp)
            truthFeatures = load(f)

            # Convert        
            writer = csv.writer(csvfile, delimiter=',')
            writer.writerow(['ImageId', 'BuildingId', 'X', 'Y'])
            building_id = 1
            for truthFeature in truthFeatures['features']:
                truthPoly = Polygon(truthFeature['geometry']['coordinates'][0])
                # coord_arr = []
                for coord in list(truthPoly.exterior.coords):
                    lat1, lon1 = coord[0], coord[1]
                    # print 'Original lat/long: ', lat1, '/', lon1
                    xPix, yPix = latLonToPixel(coord[0], coord[1], inputRaster)
                    # coord_arr.append([int(image_id), int(building_id), int(xPix), int(yPix)])
                    writer.writerow([int(image_id), int(building_id), int(xPix), int(yPix)])
                    # print 'Pixel x/y: ', xPix, '/', yPix
                    lat2, lon2 = pixelToLatLon(xPix, yPix, inputRaster)
                    # print 'Converted lat/long: ', lat2, '/', lon2
                    
                building_id += 1
