using System;
using System.IO;
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

        public static void score(List<Polygon> testPolys, List<Polygon> truthPolys, out double precision, out double recall, out int truePosCount, out int falsePosCount, out int falseNegCount)
        {
            recall = 0.0;
            precision = 0.0;
            truePosCount = 0;
            falsePosCount = 0;
            falseNegCount = 0;

            int B = truthPolys.Count;
            int M = testPolys.Count;
            double threshold = 0.5;

            foreach (var testPoly in testPolys)
            {
                IEnumerable<double> IoUs = truthPolys.Select(i => iou(testPoly, i));
                double maxIoU = IoUs.DefaultIfEmpty(0).Max(); // DefaultIfEmpty is for dupes -
                if (maxIoU >= threshold)                      // see rio_test_aoi2_Duplicates_Last3Features.geojson
                {
                    truePosCount += 1;
                    truthPolys.RemoveAt(argMax(IoUs.ToArray()));
                }
                else
                {
                    falsePosCount += 1;
                }
            }
            falseNegCount = B - truePosCount;
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
            string testFP;
            string truthFP;
            double recall = 0;
            double precision = 0;
            int truePosCount = 0;
            int falsePosCount = 0;
            int falseNegCount = 0;
            List<Polygon> testPolys;
            List<Polygon> truthPolys;
            List<int> truePosCounts = new List<int>();
            List<int> falsePosCounts = new List<int>();
            List<int> falseNegCounts = new List<int>();
            string baseDir = "C:\\Users\\todd\\Documents\\Visual Studio 2015\\Projects\\BEE\\Data\\";
            foreach (var imageID in Enumerable.Range(1, 5))
            {
                truthFP = baseDir + "Rio\\rio_test_aoi" + imageID.ToString() + ".geojson";
                testFP = baseDir + "Rio_Submission_Testing\\Rio_sample_challenge_submission" + imageID.ToString() + ".geojson";
                System.Diagnostics.Debug.WriteLine("truthFP: " + truthFP);
                System.Diagnostics.Debug.WriteLine("testFP: " + testFP);
                loadSortedPolygons(testFP, truthFP, out testPolys, out truthPolys);
                score(testPolys, truthPolys, out precision, out recall, out truePosCount, out falsePosCount, out falseNegCount);
                System.Diagnostics.Debug.WriteLine("Precision: " + precision);
                System.Diagnostics.Debug.WriteLine("Recall:  " + recall);
                truePosCounts.Add(truePosCount);
                falsePosCounts.Add(falsePosCount);
                falseNegCounts.Add(falseNegCount);
            }


            truthFP = baseDir + "Rio\\rio_test_aoi1.geojson";
            testFP = baseDir + "Rio_Hand_Truth_AOI1\\";
            foreach (var testFile in Directory.GetFiles(testFP, "*.geojson"))
            {
                System.Diagnostics.Debug.WriteLine("truthFP: " + truthFP);
                System.Diagnostics.Debug.WriteLine("testFP: " + testFile);
                loadSortedPolygons(testFile, truthFP, out testPolys, out truthPolys);
                score(testPolys, truthPolys, out precision, out recall, out truePosCount, out falsePosCount, out falseNegCount);
                System.Diagnostics.Debug.WriteLine("Precision: " + precision);
                System.Diagnostics.Debug.WriteLine("Recall:  " + recall);
                truePosCounts.Add(truePosCount);
                falsePosCounts.Add(falsePosCount);
                falseNegCounts.Add(falseNegCount);
            }

            truthFP = baseDir + "Rio\\rio_test_aoi2.geojson";
            testFP = baseDir + "Rio_Submission_Testing_CQWUnit\\";
            foreach (var testFile in Directory.GetFiles(testFP, "*.geojson"))
            {
                System.Diagnostics.Debug.WriteLine("truthFP: " + truthFP);
                System.Diagnostics.Debug.WriteLine("testFP: " + testFile);
                loadSortedPolygons(testFile, truthFP, out testPolys, out truthPolys);
                score(testPolys, truthPolys, out precision, out recall, out truePosCount, out falsePosCount, out falseNegCount);
                System.Diagnostics.Debug.WriteLine("Precision: " + precision);
                System.Diagnostics.Debug.WriteLine("Recall:  " + recall);
                truePosCounts.Add(truePosCount);
                falsePosCounts.Add(falsePosCount);
                falseNegCounts.Add(falseNegCount);
            }
            double precisionAll = Convert.ToDouble(truePosCounts.Sum()) / Convert.ToDouble(truePosCounts.Sum() + falsePosCounts.Sum());
            double recallAll = Convert.ToDouble(truePosCounts.Sum()) / Convert.ToDouble(truePosCounts.Sum() + falseNegCounts.Sum());
            double F1score = precisionAll * recallAll / (precisionAll + recallAll);
            System.Diagnostics.Debug.WriteLine("Overall Precision: " + precisionAll);
            System.Diagnostics.Debug.WriteLine("Overall Recall:  " + recallAll);
            System.Diagnostics.Debug.WriteLine("Overall F1:  " + F1score);
        }
    }
}
