﻿using System;
using GeoAPI.Geometries;
using NetTopologySuite.Geometries;

namespace BEE
{
    class Program
    {
        public static double calculateJaccard(Polygon poly1, Polygon poly2)
        {
            double intersection = poly1.Intersection(poly2).Area; poly1.
            System.Diagnostics.Debug.WriteLine("area of intersection:" + intersection);
            double union = poly2.Union(poly2).Area;
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
