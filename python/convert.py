import os
import csv
import ogr
import osr
import gdal
from geojson import load
from shapely.geometry import box, Polygon
from jaccard import compare_polys

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
        # Test Jaccard over Adelaide chip 1
        truthJsonFp = '/Users/tstavish/Projects/BEE-CSharp/data/Rio/rio_test_aoi1.geojson'
        inputRaster = '/Users/tstavish/Projects/BEE-CSharp/data/Rio/rio_mosaic_clip_aoi1.TIF'

        # load GeoJSON file
        f = open(truthJsonFp)
        truthFeatures = load(f)

        # Convert
        with open('rio_test_aoi1.csv', 'wb') as csvfile:
            writer = csv.writer(csvfile, delimiter=',')
            for truthFeature in truthFeatures['features']:
                truthPoly = Polygon(truthFeature['geometry']['coordinates'][0])
                coord_arr = []
                for coord in list(truthPoly.exterior.coords):
                    lat1, lon1 = coord[0], coord[1]
                    print 'Original lat/long: ', lat1, '/', lon1
                    xPix, yPix = latLonToPixel(coord[0], coord[1], inputRaster)
                    coord_arr.append((xPix, yPix))
                    print 'Pixel x/y: ', xPix, '/', yPix
                    lat2, lon2 = pixelToLatLon(xPix, yPix, inputRaster)
                    print 'Converted lat/long: ', lat2, '/', lon2
                writer.writerow(coord_arr)
