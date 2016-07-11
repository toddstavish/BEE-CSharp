using System;
using System.Collections.Generic;
using GeoAPI.Geometries;
using NetTopologySuite.Geometries;
using OSGeo.GDAL;
using OSGeo.OGR;
using OSGeo.OSR;
using ClipperLib;
using Kaggle.Metrics.Utilities;

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
            CoordinateTransformation ct = new CoordinateTransformation(src, dst);

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
            double union = poly1.Union(poly2).Area;
            return intersection / union;
        }

        public static double areaOfUnion(Polygon poly1, Polygon poly2)
        {
            double aOfU = poly1.Union(poly2).Area;
            return aOfU;
        }

        static void Main(string[] args)
        {
            // Factory for Cartesion Coordinates
            GeometryFactory cartFactory = new GeometryFactory();

            // Factory for EPSG:4326 - wgs 84 (lat/longs) * global
            GeometryFactory gcsfactory = new GeometryFactory(new PrecisionModel(), 4326);

            //
            // Test Cartesian Coordinates in both implementations of Jaccard
            //

            // NetTopologySuite
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

            // Clipper
            List<IntPoint> polyA = new List<IntPoint>();
            polyA.Add(new IntPoint(62, 135));
            polyA.Add(new IntPoint(120, 208));
            polyA.Add(new IntPoint(144, 188));
            polyA.Add(new IntPoint(86, 115));
            polyA.Add(new IntPoint(62, 135));
            List<IntPoint> polyB = new List<IntPoint>();
            polyB.Add(new IntPoint(65, 115));
            polyB.Add(new IntPoint(120, 208));
            polyB.Add(new IntPoint(144, 188));
            polyB.Add(new IntPoint(86, 120));
            polyB.Add(new IntPoint(65, 115));
            List<IntPoint> polyC = new List<IntPoint>();
            polyC.Add(new IntPoint(60, 95));
            polyC.Add(new IntPoint(111, 190));
            polyC.Add(new IntPoint(143, 178));
            polyC.Add(new IntPoint(86, 120));
            polyC.Add(new IntPoint(60, 95));
            List<IntPoint> polyD = new List<IntPoint>();
            polyD.Add(new IntPoint(50, 145));
            polyD.Add(new IntPoint(124, 190));
            polyD.Add(new IntPoint(143, 178));
            polyD.Add(new IntPoint(90, 115));
            polyD.Add(new IntPoint(50, 145));
            // Print results
            System.Diagnostics.Debug.WriteLine("NetTopologySuite Jaccard(poly1, poly1):" + calculateJaccard(poly1, poly1));
            System.Diagnostics.Debug.WriteLine("ClipperLib Jaccard(poly1, poly1):" + PolygonUtil.Jaccard(polyA, polyA));
            System.Diagnostics.Debug.WriteLine("NetTopologySuite Jacard(poly1, poly2)" + calculateJaccard(poly1, poly2));
            System.Diagnostics.Debug.WriteLine("ClipperLib Jaccard(poly1, poly2)" + PolygonUtil.Jaccard(polyA, polyB));
            System.Diagnostics.Debug.WriteLine("NetTopologySuite Jaccard(poly1, poly3)" + calculateJaccard(poly1, poly3));
            System.Diagnostics.Debug.WriteLine("ClipperLib Jaccard(poly1, poly3)" + PolygonUtil.Jaccard(polyA, polyC));
            System.Diagnostics.Debug.WriteLine("NetTopologySuite Jaccard(poly1, poly4)" + calculateJaccard(poly1, poly4));
            System.Diagnostics.Debug.WriteLine("ClipperLib Jaccard(poly1, poly4)" + PolygonUtil.Jaccard(polyA, polyD));

            //
            // Test precsion accross implemenations using UTM Coordinates and Area of Union
            //
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
                List<IntPoint> polyTest = new List<IntPoint>();
                foreach (var coordinate in testPoly.Coordinates)
                {
                    polyTest.Add(new IntPoint(Convert.ToInt32(coordinate.X), Convert.ToInt32(coordinate.Y)));
                }
                foreach (var truthFeature in truthFeatures.Features)
                {
                    Polygon truthPoly = (Polygon)truthFeature.Geometry;
                    List<IntPoint> polyTruth = new List<IntPoint>();
                    foreach (var coordinate in truthPoly.Coordinates)
                    {
                        polyTruth.Add(new IntPoint(Convert.ToInt32(coordinate.X), Convert.ToInt32(coordinate.Y)));
                    }
                    if (calculateJaccard(testPoly, truthPoly) != 0)
                    {
                        System.Diagnostics.Debug.WriteLine("testPoly:" + testPoly);
                        System.Diagnostics.Debug.WriteLine("truthPoly:" + truthPoly);
                        System.Diagnostics.Debug.WriteLine("NetTopologySuite Jaccard(testPoly, truthPoly): " + calculateJaccard(testPoly, truthPoly));
                        System.Diagnostics.Debug.WriteLine("Clipper Jaccard(testPoly, truthPoly): " + PolygonUtil.Jaccard(polyTest, polyTruth));
                    }
                }
            }

        }
    }
}