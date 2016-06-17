using System;
using System.Collections.Generic;
using System.Linq;
using Kaggle.DataFrames;
using Kaggle.Metrics.Utilities;
using ClipperLib;


namespace Kaggle.Metrics.Custom
{
    [PublishedEvaluationAlgorithm ("JaccardDigitalGlobe", Name = "Jaccard",
        Description = "Calculates the similarity of building footprints",
        IsPublic = false, IsMax = true)]

    public class JaccardDigitalGlobe : DataFrameEvaluationAlgorithm<JaccardDigitalGlobe.Solution, JaccardDigitalGlobe.Submission>
    {
        public class Solution : TypedDataFrame
        {
            public Series<int> ImageId { get; set; }
            public Series<int> BuildingId { get; set; }
            public Series<int> X { get; set; }
            public Series<int> Y { get; set; }
        }

        public class Submission : TypedDataFrame
        {
            public Series<int> ImageId { get; set; }
            public Series<int> BuildingId { get; set; }
            public Series<int> X { get; set; }
            public Series<int> Y { get; set; }
        }

        // solution and submission don't have to have the same number of rows
        public override bool RequiresSameRowCountInSubmissionAndSolution {
            get { return false; }
        }

        protected override Submission GetSubmissionSubset (Submission fullSubmission, Solution fullSolution, int [] solutionSubsetRowOffsets)
        {
            return fullSubmission;
        }





        public override double EvaluateSubmissionSubset (Solution solution, Submission submission)
        {
            var _submission = new Dictionary<int, Dictionary<int, List<IntPoint>>> ();
            var _solution = new Dictionary<int, Dictionary<int, List<IntPoint>>> ();

            int imageId;
            int buildingId;
            List<IntPoint> polygon;

            for (var ix = 0; ix < submission.RowCount; ix++) {
                imageId = submission.ImageId [ix];
                buildingId = submission.BuildingId [ix];

                Dictionary<int, List<IntPoint>> buildingDict;

                if (!_submission.TryGetValue (imageId, out buildingDict)) {
                    // new image
                    polygon = new List<IntPoint> ();
                } else if (!_submission [imageId].TryGetValue (buildingId, out polygon)) {
                    // new building
                    polygon = new List<IntPoint> ();
                }

                polygon.Add (new IntPoint(submission.X [ix], submission.Y [ix]));

                // add the polygon back
                if (_submission.ContainsKey (imageId)) {
                    _submission [imageId] [buildingId] = polygon;
                } else {
                    var tmp_dict = new Dictionary<int, List<IntPoint>> ();
                    tmp_dict.Add (buildingId, polygon);
                    _submission.Add (imageId, tmp_dict);
                }
            }

            for (var ix = 0; ix < solution.RowCount; ix++) {
                imageId = solution.ImageId [ix];
                buildingId = solution.BuildingId [ix];
                Dictionary<int, List<IntPoint>> buildingDict;

                if (!_solution.TryGetValue (imageId, out buildingDict)) {
                    // new image
                    polygon = new List<IntPoint> ();
                } else if (!_solution [imageId].TryGetValue (buildingId, out polygon)) {
                    // new building
                    polygon = new List<IntPoint> ();
                }

                polygon.Add (new IntPoint(solution.X [ix], solution.Y [ix]));
                // add the polygon back
                if (_solution.ContainsKey (imageId)) {
                    _solution [imageId] [buildingId] = polygon;
                } else {
                    var tmp_dict = new Dictionary<int, List<IntPoint>> ();
                    tmp_dict.Add (buildingId, polygon);
                    _solution.Add (imageId, tmp_dict);
                }
            }

            var querySub = submission.GroupBy (s => s.ImageId)
                                     .ToDictionary (g => g.Key, g => new List<int> (g.Value.BuildingId.Distinct ()));

            var imgAverageScoresList = new List<double> ();

            foreach (var imageGroup in querySub) { // for each image

                var allBuildingScoresPerImg = new List<Tuple<int, int, double>> ();

                foreach (int buildingIdSub in imageGroup.Value) { // for each building

                    var subBuilding = _submission [imageGroup.Key] [buildingIdSub];

                    foreach (int buildingIdSol in querySub [imageGroup.Key]) {

                        var solBuilding = _solution [imageGroup.Key] [buildingIdSol];


                        double jaccard = PolygonUtil.Jaccard (subBuilding, solBuilding);

                        allBuildingScoresPerImg.Add (Tuple.Create (buildingIdSub, buildingIdSol, jaccard));

                    }
                }

                // sort scores desc 
                allBuildingScoresPerImg = allBuildingScoresPerImg.OrderByDescending (i => i.Item3).ToList ();

                // start a list of buildings from solution
                var SolBuildingList = allBuildingScoresPerImg.Select (t => t.Item2).Distinct().ToList ();

                var HitScores = new List<double> ();

                // go down the list of scores and assign the matches
                foreach (Tuple<int, int, double> tup in allBuildingScoresPerImg) {
                    if (SolBuildingList.Contains (tup.Item2)) {
                        // found a match for the building
                        HitScores.Add (tup.Item3);
                        SolBuildingList.Remove (tup.Item2);
                    }
                    // when all the buildings are matched, just quit - no need to go further
                    if (SolBuildingList.Count == 0)
                        break;
                }

                if (HitScores.Count >= 0)
                    // score of an image = the highest score of aligned matches for each building, divided by the number of buildings in submission (per image)
                    imgAverageScoresList.Add (HitScores.Sum () / _submission[imageGroup.Key].Count);
                else
                    imgAverageScoresList.Add (0.0);
            }

            return imgAverageScoresList.Average ();
        }

        public class Building
        {
            public int ImageId { get; set; }
            public int BuildingId { get; set; }
            public List<IntPoint> Polygon { get; set; }

            public Building (int iId, int bId)
            {
                ImageId = iId;
                BuildingId = bId;
            }

            public Building AddPoint (int X, int Y)
            {
                Polygon.Add (new IntPoint (X, Y));
                return this;
            }
        }
    }
}


