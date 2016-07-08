using System;
using System.Linq;
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

        public static double iou(Polygon poly1, Polygon poly2)
        {
            double intersection = poly1.Intersection(poly2).Area;
            double union = poly1.Union(poly2).Area;
            return intersection/union;
        }

        public static int argMax(double[] arr)
        {
            double m = arr.Max();
            int p = Array.IndexOf(arr, m);
            return p;
        }

        public static void loadSortedPolygons(string testJsonFp, string truthJsonFp, out List<Polygon> testPolys, out List<Polygon> truthPolys)
        {
            // Convert geojson files to polygons lista
            System.IO.StreamReader file = new System.IO.StreamReader(testJsonFp);
            var reader = new NetTopologySuite.IO.GeoJsonReader();
            string geoJsonText = file.ReadToEnd();
            var testFeatures = reader.Read<NetTopologySuite.Features.FeatureCollection>(geoJsonText);
            file.Close();
            file = new System.IO.StreamReader(truthJsonFp);
            geoJsonText = file.ReadToEnd();
            var truthFeatures = reader.Read<NetTopologySuite.Features.FeatureCollection>(geoJsonText);
            file.Close();

            testPolys = new List<Polygon>();
            foreach (var testFeature in testFeatures.Features)
            {
                testPolys.Add((Polygon)testFeature.Geometry);
            }
            truthPolys = new List<Polygon>();
            foreach (var truthFeature in truthFeatures.Features)
            {
                truthPolys.Add((Polygon)truthFeature.Geometry);
            }

            // Generate random confidences and sort [these should be user supplied]
            var rand = new Random();
            var randos = new List<float>();
            for (int i = 0; i < testPolys.Count; i++)
            {
                randos.Add((float)rand.NextDouble());
            }
            IEnumerable<Tuple<float, Polygon>> pairs = randos.Zip(testPolys, (a, b) => Tuple.Create(a, b)).OrderByDescending(a => a);
            testPolys = pairs.Select(b => b.Item2).ToList();
        }

        public static void score(List<Polygon> testPolys, List<Polygon> truthPolys, out double precision, out double recall)
        {
            int truePosCount = 0;
            int falsePosCount = 0;

            int B = truthPolys.Count;
            int M = testPolys.Count;
            double threshold = 0.5;

            foreach (var testPoly in testPolys)
            {
                IEnumerable<double> IoUs = truthPolys.Select(i => iou(testPoly, i));
                double maxIoU = IoUs.Max();
                if (maxIoU >= threshold)
                {
                    truePosCount += 1;
                    truthPolys.RemoveAt(argMax(IoUs.ToArray()));
                }
                else
                {
                    falsePosCount += 1;
                }
            }
            int falseNegCount = B - truePosCount;
            System.Diagnostics.Debug.WriteLine("Num truths: " + B);
            System.Diagnostics.Debug.WriteLine("Num proposals: " + M);
            System.Diagnostics.Debug.WriteLine("True pos count: " + truePosCount);
            System.Diagnostics.Debug.WriteLine("False pos count: " + falsePosCount);
            System.Diagnostics.Debug.WriteLine("False neg count:  "+ falseNegCount);
            precision = Convert.ToDouble(truePosCount) / Convert.ToDouble(truePosCount + falsePosCount);
            recall = Convert.ToDouble(truePosCount) / Convert.ToDouble(truePosCount + falseNegCount);
        }

        static void Main(string[] args)
        {

            // Test precsion accross implemenations using UTM Coordinates and Area of Union
            string testJsonFp = "C:\\Users\\todd\\Documents\\Visual Studio 2015\\Projects\\BEE\\Data\\SampleChips\\Chip1\\TestChip1.geojson";
            string truthJsonFp = "C:\\Users\\todd\\Documents\\Visual Studio 2015\\Projects\\BEE\\Data\\SampleChips\\Chip1\\TruthChip1.geojson";
            List<Polygon> testPolys;
            List<Polygon> truthPolys;
            loadSortedPolygons(testJsonFp, truthJsonFp, out testPolys, out truthPolys);
            double precision;
            double recall;
            score(testPolys, truthPolys, out precision, out recall);
            System.Diagnostics.Debug.WriteLine("Precision: " + precision);
            System.Diagnostics.Debug.WriteLine("Recall:  " + recall);
            double F1score = precision * recall / (precision + recall);
            System.Diagnostics.Debug.WriteLine("F1:  " + F1score);
        }
    }
}
