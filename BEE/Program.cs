using System;
using GeoAPI.Geometries;
using NetTopologySuite.Geometries;
using OSGeo.GDAL;
using OSGeo.OGR;
using OSGeo.OSR;

namespace BEE
{
    class Program
    {
        public static Coordinate latLongtoPix(double lat, double lon, string rasterFp)
        {
            Gdal.AllRegister();

            // Source projection
            SpatialReference src = new SpatialReference("");
            src.ImportFromProj4("+proj=latlong +datum=WGS84 +no_defs");
            OSGeo.OGR.Geometry geom = new OSGeo.OGR.Geometry(wkbGeometryType.wkbPoint);
            geom.AddPoint(lon, lat, 0);

            // Raster projection
            Dataset raster = Gdal.Open(rasterFp, Access.GA_ReadOnly);
            SpatialReference dst = new SpatialReference("");
            string rasterProj = raster.GetProjectionRef();
            dst.ImportFromWkt(ref rasterProj);
            CoordinateTransformation ct =  new CoordinateTransformation(src, dst);

            double[] transform = new double[6];
            raster.GetGeoTransform(transform);

            double xOrigin = transform[0];
            double yOrigin = transform[3];
            double pixelWidth = transform[1];
            double pixelHeight = transform[5];

            geom.Transform(ct);
            double[] points = new double[2];
            geom.GetPoint(0, points);
            double xPix = (points[0] - xOrigin) / pixelWidth;
            double yPix = (points[1] - yOrigin) / pixelHeight;

            return new Coordinate(xPix, yPix);
        }

        public static OSGeo.OGR.Geometry pixToLatLong(double xPix, double yPix, string rasterFp)
        {
            Gdal.AllRegister();

            // Raster projection
            Dataset raster = Gdal.Open(rasterFp, Access.GA_ReadOnly);
            SpatialReference src = new SpatialReference("");
            string rasterProj = raster.GetProjectionRef();
            src.ImportFromWkt(ref rasterProj);

            // Destination projection
            SpatialReference dst = new SpatialReference("");
            dst.ImportFromProj4("+proj=latlong +datum=WGS84 +no_defs");
            CoordinateTransformation ct = new CoordinateTransformation(src, dst);

            OSGeo.OGR.Geometry geom = new OSGeo.OGR.Geometry(wkbGeometryType.wkbPoint);

            double[] transform = new double[6];
            raster.GetGeoTransform(transform);

            double xOrigin = transform[0];
            double yOrigin = transform[3];
            double pixelWidth = transform[1];
            double pixelHeight = transform[5];

            double xCoord = (xPix * pixelWidth) + xOrigin;
            double yCoord = (yPix * pixelHeight) + yOrigin;

            geom.AddPoint(xCoord, yCoord, 0);
            geom.Transform(ct);
            return geom;
        }

        public static double calculateJaccard(Polygon poly1, Polygon poly2)
        {
            double intersection = poly1.Intersection(poly2).Area;
            System.Diagnostics.Debug.WriteLine("area of intersection:" + intersection);
            double union = poly1.Union(poly2).Area;
            System.Diagnostics.Debug.WriteLine("area of union:" + union);
            return intersection/union;
        }

        static void Main(string[] args)
        {
            // Factory for Cartesion Coordinates
            GeometryFactory cartFactory = new GeometryFactory();

            // Factory for EPSG:4326 - wgs 84 (lat/longs) * global
            GeometryFactory gcsfactory = new GeometryFactory(new PrecisionModel(), 4326);

            //Factory for EPSG:32754 - wgs 84 / utm zone 54s * regional boundaries
            GeometryFactory utmfactory = new GeometryFactory();

            // Test Cartesian Coordinates
            Coordinate[] coords1 = new Coordinate[]{
                new Coordinate(62, 135),
                new Coordinate(120, 208),
                new Coordinate(144, 188),
                new Coordinate(86, 115),
                new Coordinate(62, 135)
			};
            Coordinate[] coords2 = new Coordinate[]{
                new Coordinate(65, 115),
                new Coordinate(120, 208),
                new Coordinate(144, 188),
                new Coordinate(86, 120),
                new Coordinate(65, 115)
			};
            Coordinate[] coords3 = new Coordinate[]{
                new Coordinate(60, 95),
                new Coordinate(111, 190),
                new Coordinate(143, 178),
                new Coordinate(86, 120),
                new Coordinate(60, 95)
			};
            Coordinate[] coords4 = new Coordinate[]{
                new Coordinate(50, 145),
                new Coordinate(124, 190),
                new Coordinate(143, 178),
                new Coordinate(90, 115),
                new Coordinate(50, 145)
			};
            Polygon poly1 = (Polygon)cartFactory.CreatePolygon(new LinearRing(coords1));
            Polygon poly2 = (Polygon)cartFactory.CreatePolygon(new LinearRing(coords2));
            Polygon poly3 = (Polygon)cartFactory.CreatePolygon(new LinearRing(coords3));
            Polygon poly4 = (Polygon)cartFactory.CreatePolygon(new LinearRing(coords4));
            System.Diagnostics.Debug.WriteLine("Jacard(poly1, poly1):" + calculateJaccard(poly1, poly1));
            System.Diagnostics.Debug.WriteLine("Jacard(poly1, poly2)" + calculateJaccard(poly1, poly2));
            System.Diagnostics.Debug.WriteLine("Jacard(poly1, poly3)" + calculateJaccard(poly1, poly3));
            System.Diagnostics.Debug.WriteLine("Jacard(poly1, poly4)" + calculateJaccard(poly1, poly4));

            // Test UTM Coordinates
            string testJsonFp = "C:\\Users\\todd\\Documents\\Visual Studio 2015\\Projects\\BEE\\Data\\SampleChips\\Chip1\\TestChip1.geojson";
            string truthJsonFp = "C:\\Users\\todd\\Documents\\Visual Studio 2015\\Projects\\BEE\\Data\\SampleChips\\Chip1\\TruthChip1.geojson";
            System.IO.StreamReader file = new System.IO.StreamReader(testJsonFp);
            var reader = new NetTopologySuite.IO.GeoJsonReader();
            string geoJsonText = file.ReadToEnd();
            var testFeatures = reader.Read<NetTopologySuite.Features.FeatureCollection>(geoJsonText);
            file.Close();
            file = new System.IO.StreamReader(truthJsonFp);
            geoJsonText = file.ReadToEnd();
            var truthFeatures = reader.Read<NetTopologySuite.Features.FeatureCollection>(geoJsonText);
            file.Close();

            foreach (var testFeature in testFeatures.Features)
            {
                Polygon testPoly = (Polygon)testFeature.Geometry;
                foreach (var truthFeature in testFeatures.Features)
                {
                    Polygon truthPoly = (Polygon)truthFeature.Geometry;
                    System.Diagnostics.Debug.WriteLine("testPoly:" + testPoly);
                    System.Diagnostics.Debug.WriteLine("truthPoly:" + truthPoly);
                    System.Diagnostics.Debug.WriteLine("Jacard(testPoly, truthPoly):" + calculateJaccard(testPoly, truthPoly));

                }
            }
        }
    }
}
