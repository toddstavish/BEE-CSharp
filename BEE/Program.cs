using System;
using GeoAPI.Geometries;
using NetTopologySuite.Geometries;

namespace BEE
{
    class Program
    {
        public static double calculateJaccard(Polygon poly1, Polygon poly2)
        {
            double intersection = poly1.Intersection(poly2).Area;
            double union = poly2.Union(poly2).Area;
            return intersection / union;
        }

        static void Main(string[] args)
        {
            // Factory for Cartesion Coordinates
            GeometryFactory cartFactory = new GeometryFactory();

            // Factory for projections to support lat/longs
            GeometryFactory projfactory = new GeometryFactory(new PrecisionModel(), 4326);

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
        }
    }
}
