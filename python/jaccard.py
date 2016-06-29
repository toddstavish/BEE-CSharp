from shapely.geometry import box, Polygon
import numpy as np
from geojson import load

def compare_polys(poly_a, poly_b):
    """Compares two polygons via IoU.

    Input:
        poly_a: A Shapely polygon.
        poly_b: Another Shapely polygon.

    Returns:
        The IoU between these two polygons.
    """
    intersection = poly_a.intersection(poly_b).area
    union = poly_a.union(poly_b).area
    jaccard = intersection/union
    return jaccard

if __name__ == "__main__":
    ground_truth_boxes = [np.array([[ 62, 135],
            [120, 208],
            [144, 188],
            [ 86, 115],
            [ 62, 135]], dtype=np.int32),
    np.array([[ 65, 115],
            [120, 208],
            [144, 188],
            [ 86, 120],
            [ 65, 115]], dtype=np.int32),
    np.array([[ 60, 95],
            [111, 190],
            [143, 178],
            [ 86, 120],
            [ 60, 95]], dtype=np.int32),
    np.array([[ 50, 145],
            [124, 190],
            [143, 178],
            [ 90, 115],
            [ 50, 145]], dtype=np.int32)]

    polys_gt = [Polygon(c) for c in ground_truth_boxes]
    centroids_gt = [np.asarray(p.centroid) for p in polys_gt]
    areas_gt = [p.area for p in polys_gt]
    bounds_gt = [p.bounds for p in polys_gt]
    sizes_gt = [[p[2]-p[0], p[3]-p[1]] for p in bounds_gt]
    radii_gt = [np.sqrt( size[0]**2 + size[1]**2 ) for size in sizes_gt]

    # comare all polygons to the first polygoin
    poly = polys_gt[0]

    for itmp in range(len(polys_gt)):
        poly_tmp = polys_gt[itmp]
        print 'Jaccard: ', compare_polys(poly, poly_tmp)

    # Test Jaccard over Adelaide chip 1
    testJsonFp = '/Users/tstavish/Projects/BEE-CSharp/data/SampleChips/Chip1/TestChip1.geojson'
    truthJsonFp = '/Users/tstavish/Projects/BEE-CSharp/data/SampleChips/Chip1/TruthChip1.geojson'

    # load GeoJSON file
    f = open(testJsonFp)
    testFeatures = load(f)
    f = open(truthJsonFp)
    truthFeatures = load(f)

    # Run jaccard
    for testFeature in testFeatures['features']:
        testPoly = Polygon(testFeature['geometry']['coordinates'][0])
        for truthFeature in truthFeatures['features']:
            truthPoly = Polygon(truthFeature['geometry']['coordinates'][0])
            if compare_polys(testPoly, truthPoly) != 0 and compare_polys(testPoly, truthPoly) != 1:
                print "testPoly: ", testPoly
                print "truthPoly:", truthPoly
                print "GDAL/GEOS Jaccard(testPoly, truthPoly): ", compare_polys(testPoly, truthPoly)
