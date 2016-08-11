using System;
using System.Linq;
using System.Collections.Generic;
using NetTopologySuite.IO;
using NetTopologySuite.Geometries;
using Deedle;

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

        public static void score(List<Polygon> testPolys, List<Polygon> truthPolys, out int truePosCount, out int falsePosCount, out int falseNegCount)
        {

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
            System.Diagnostics.Debug.WriteLine("False neg count:  "+ falseNegCount);;
        }

        static void Main(string[] args)
        {
            string testFP;
            string truthFP;
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
            var imageIDs = getImageIDs(truthFP);

            foreach (var imageID in imageIDs)
            {
                System.Diagnostics.Debug.WriteLine("image id: " + imageID);
                IEnumerable<Tuple<int, int, Polygon>> testImages = testPolys.Where(t => t.Item1 == imageID); // This could be done in the dataframe slicing and a better data structure
                IEnumerable<Tuple<int, int, Polygon>> truthImages = truthPolys.Where(t => t.Item1 == imageID); // This could be done in the dataframe slicing and a better data structure
                if (testImages.ToList()[0].Item2 == -1)
                {
                    falsePosCount = 0;
                    truePosCount = 0;
                }
                else
                {
                    if (truthImages.ToList()[0].Item2 == -1)
                    {
                        truePosCount = 0;
                        falsePosCount = testImages.Count();
                    }
                    score(testImages.Select(t => t.Item3).ToList(), truthImages.Select(t => t.Item3).ToList(), out truePosCount, out falsePosCount, out falseNegCount);
                }
                System.Diagnostics.Debug.WriteLine("Building id: " + truthImages.ToList()[0].Item2);
                System.Diagnostics.Debug.WriteLine("truth count: " + truthImages.Count());
                truePosCounts.Add(truePosCount);
                falsePosCounts.Add(falsePosCount);
                falseNegCounts.Add(falseNegCount);
            }
            double precisionAll;
            double recallAll;
            double F1score;
            if (falsePosCounts.Sum() == 0 && truePosCounts.Sum() == 0)
            {
                precisionAll = 1.0;
                recallAll = 0.0;
                F1score = 0.0;
            }
            else
            {
                precisionAll = Convert.ToDouble(truePosCounts.Sum()) / Convert.ToDouble(truePosCounts.Sum() + falsePosCounts.Sum());
                //recallAll = Convert.ToDouble(truePosCounts.Sum()) / Convert.ToDouble(truthPolys.Count());
                recallAll = Convert.ToDouble(truePosCounts.Sum()) / Convert.ToDouble(truePosCounts.Sum() + falseNegCounts.Sum());
                F1score = 2.0 * precisionAll * recallAll / (precisionAll + recallAll);
            }
            System.Diagnostics.Debug.WriteLine("Overall Precision: " + precisionAll);
            System.Diagnostics.Debug.WriteLine("Overall Recall:  " + recallAll);
            System.Diagnostics.Debug.WriteLine("Overall F1:  " + F1score);
        }
    }
}
