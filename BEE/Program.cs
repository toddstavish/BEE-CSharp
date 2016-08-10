using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using GeoAPI.Geometries;
using NetTopologySuite.IO;
using NetTopologySuite.Geometries;
using NetTopologySuite.Features;
using Deedle;
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

        public static void loadGeoJson(string testJsonFp, string truthJsonFp, out List<Polygon> testPolys, out List<Polygon> truthPolys)
        {
            // Convert geojson files to polygon lists
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

        public static HashSet<int> getImageIDs(string csvFp)
        {
            var imageDF = Frame.ReadCsv(csvFp);
            var imageIDs = new HashSet<int>();
            foreach (var row in imageDF.Rows.ObservationsAll)
            {
                imageIDs.Add((int)row.Value.Value["ImageId"]);
            }
            return imageIDs;
        }

        public static List<Tuple<int, int, Polygon>> loadWktCsv(string csvFp)
        {
            var imageDF = Frame.ReadCsv(csvFp);

            var imageList = new List<Tuple<int, int, Polygon>>();

            // Change this to slicing and a better data structure
            foreach (var row in imageDF.Rows.ObservationsAll)
            {
                System.Diagnostics.Debug.WriteLine(row.ToString());
                int imageID = (int)row.Value.Value["ImageId"];
                int buildingID = (int)row.Value.Value["BuildingId"];
                WKTReader rdr = new WKTReader();
                Polygon poly = (Polygon)rdr.Read((string)row.Value.Value["PolygonWKT"]);
                imageList.Add(Tuple.Create(imageID, buildingID, poly));
            }
            return imageList;
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
                double maxIoU = IoUs.DefaultIfEmpty(0).Max();
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
            List<int> truePosCounts = new List<int>();
            List<int> falsePosCounts = new List<int>();
            List<int> falseNegCounts = new List<int>();

            string baseDir = "C:\\Users\\todd\\Documents\\Visual Studio 2015\\Projects\\BEE\\data\\";

            truthFP = baseDir + "wktSubmission-small.csv";
            testFP = baseDir + "wktSubmission-small.csv";
            System.Diagnostics.Debug.WriteLine("truthFP: " + truthFP);
            System.Diagnostics.Debug.WriteLine("testFP: " + testFP);
            var truthPolys = loadWktCsv(truthFP);
            var testPolys = loadWktCsv(testFP);
            var imageIDs = getImageIDs(testFP);

            foreach (var imageID in imageIDs)
            {
                IEnumerable<Tuple<int, int, Polygon>> testImages = testPolys.Where(t => t.Item1 == imageID); // This could be done in the dataframe slicing
                IEnumerable<Tuple<int, int, Polygon>> truthImages = truthPolys.Where(t => t.Item1 == imageID); // This could be done in the dataframe slicing
                score(testPolys.Select(t => t.Item3).ToList(), truthPolys.Select(t => t.Item3).ToList(), out precision, out recall, out truePosCount, out falsePosCount, out falseNegCount);
                System.Diagnostics.Debug.WriteLine("Precision: " + precision);
                System.Diagnostics.Debug.WriteLine("Recall:  " + recall);
                truePosCounts.Add(truePosCount);
                falsePosCounts.Add(falsePosCount);
                falseNegCounts.Add(falseNegCount);
            }
            double precisionAll = Convert.ToDouble(truePosCounts.Sum()) / Convert.ToDouble(truePosCounts.Sum() + falsePosCounts.Sum());
            double recallAll = Convert.ToDouble(truePosCounts.Sum()) / Convert.ToDouble(truePosCounts.Sum() + falseNegCounts.Sum());
            double F1score = 2.0 * precisionAll * recallAll / (precisionAll + recallAll);
            System.Diagnostics.Debug.WriteLine("Overall Precision: " + precisionAll);
            System.Diagnostics.Debug.WriteLine("Overall Recall:  " + recallAll);
            System.Diagnostics.Debug.WriteLine("Overall F1:  " + F1score);
        }
    }
}
