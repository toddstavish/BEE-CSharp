using System;
using GeoAPI.Geometries;
using NetTopologySuite.Geometries;

namespace BEE
{
    class Program
    {
        static void Main(string[] args)
        {
            // Factory using projections to support lat/longs
            // GeometryFactory factory = new GeometryFactory(new PrecisionModel(), 4326);
            GeometryFactory factory = new GeometryFactory();

            // Around Central Park
            Coordinate[] coords = new Coordinate[]{
                new Coordinate(-73.957986,40.800566),
                new Coordinate(-73.949575,40.797187),
                new Coordinate(-73.972921,40.764951),
                new Coordinate(-73.981676,40.768071),
                new Coordinate(-73.957986,40.800566) // Close this polygon!
			};

            Polygon poly = (Polygon)factory.CreatePolygon(new LinearRing(coords));
            System.Diagnostics.Debug.WriteLine("Central Park Area: " + poly.Area);
        }
    }
}
