using System;
using System.Collections.Generic;
using System.Linq;
using MoreLinq;
using Kaggle.DataFrames;
using NetTopologySuite.Geometries;
using GeoAPI.Geometries;



namespace Kaggle.Metrics.Custom
{
	[PublishedEvaluationAlgorithm("F1DigitalGlobe", Name = "F1DigitalGlobe",
		Description = "Calculates the similarity of building footprints",
		IsPublic = false, IsMax = true)]

	public class F1DigitalGlobe : DataFrameEvaluationAlgorithm<F1DigitalGlobe.Solution, F1DigitalGlobe.Submission, F1DigitalGlobe.Parameters>
	{
		public class Solution : TypedDataFrame
		{
			public Series<int> ImageId { get; set; }
			public Series<int> ContainsBuildings { get; set; }
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

		public class Parameters : EvaluationAlgorithmParameters
		{
			public int MaxNumBuildingPerImage { get; set; }

		}


		// solution and submission don't have to have the same number of rows
		public override bool RequiresSameRowCountInSubmissionAndSolution
		{
			get { return false; }
		}

		protected override Submission GetSubmissionSubset(Submission fullSubmission, Solution fullSolution, int[] solutionSubsetRowOffsets)
		{
			return fullSubmission;
		}

		public override double EvaluateSubmissionSubset(Solution solution, Submission submission, Parameters parameters)
		{

			var SubmissionBuildings = submission.GroupBy(s => s.ImageId)
												.ToDictionary(g => g.Key, g => new List<int>(g.Value.BuildingId.Distinct()));
			// check 1. check that the max # of submitted buildings in each image is not too many 
			foreach (var imgGrp in SubmissionBuildings)
			{
				if (imgGrp.Value.Count > parameters.MaxNumBuildingPerImage)
				{
					throw new Exception(String.Format("For image {0}, you predicted {1} buildings, which exceeds the prediction limit of {2}.", imgGrp.Key, imgGrp.Value, parameters.MaxNumBuildingPerImage));
				}
			}

			// filter solution 
			IList<int> filteredImgId = new List<int>();
			IList<int> filteredBldgId = new List<int>();
			IList<int> filteredX = new List<int>();
			IList<int> filteredY = new List<int>();

            for (int i = 0; i < solution.RowCount; i++)
			{
                if (solution.ContainsBuildings[i] == 1) {
                    filteredImgId.Add (solution.ImageId[i]);
                    filteredBldgId.Add (solution.BuildingId[i]);
                    filteredX.Add (solution.X[i]);
                    filteredY.Add(solution.Y[i]);
                }
			}

			Dictionary<int, Dictionary<int, Polygon>> _submission = readInputTable(submission.ImageId, submission.BuildingId, submission.X, submission.Y);

            Dictionary<int, Dictionary<int, Polygon>> _solution = readInputTable(filteredImgId.ToSeries(), filteredBldgId.ToSeries(), filteredX.ToSeries(), filteredY.ToSeries());

			var solutionGroups = solution.GroupBy(s => s.ImageId)
									 .ToDictionary(g => g.Key, g => new List<int>(g.Value.BuildingId.Distinct()));

			var imgAverageScoresList = new List<double>();

			foreach (var imageGroup in solutionGroups)
			{ 
				// for each image in the solution
				// solution should have all the image ids

				if (!_submission.ContainsKey(imageGroup.Key) && _solution.ContainsKey(imageGroup.Key))
					imgAverageScoresList.Add(0.0);
				else if (_submission.ContainsKey(imageGroup.Key) && _solution.ContainsKey(imageGroup.Key)) {
					var subBuildings = _submission[imageGroup.Key].Values.ToList();
					var solBuildings = _solution[imageGroup.Key].Values.ToList();

					imgAverageScoresList.Add(F1score(subBuildings, solBuildings));

				}
			}

			return imgAverageScoresList.Average();
		}


		public static double F1score(List<Polygon> testPolys, List<Polygon> truthPolys)
		{
			double precision;
			double recall;

			int truePosCount = 0;
			int falsePosCount = 0;

			int B = truthPolys.Count;
			int M = testPolys.Count;
			double threshold = 0.5;

			foreach (var testPoly in testPolys)
			{
                IEnumerable<double> IoUs = truthPolys.Select(i => calculateJaccard (testPoly, i));
				double maxIoU = IoUs.Max();
				if (maxIoU >= threshold)
				{
					truePosCount += 1;
					truthPolys.RemoveAt(argMax(IoUs.ToArray()));
				}
				else {
					falsePosCount += 1;
				}
			}
			int falseNegCount = B - truePosCount;
			precision = Convert.ToDouble(truePosCount) / Convert.ToDouble(truePosCount + falsePosCount);
			recall = Convert.ToDouble(truePosCount) / Convert.ToDouble(truePosCount + falseNegCount);

			return 2 * precision * recall / (precision + recall);
		}


        // reading inputs into dictionary of dictionaries 
        private Dictionary<int, Dictionary<int, Polygon>> readInputTable(Series<int> ImageId, Series<int> BuildingId, Series<int> X, Series<int> Y)
		{
			var _DF = new Dictionary<int, Dictionary<int, List<Coordinate>>>();
			var DFwithPolygon = new Dictionary<int, Dictionary<int, Polygon>>();

			for (var ix = 0; ix < ImageId.Count; ix++)
			{
				int imageId = ImageId[ix];
				int buildingId = BuildingId[ix];
				var coordsList = new List<Coordinate>();

				Dictionary<int, List<Coordinate>> buildingDict;

				if (!_DF.TryGetValue(imageId, out buildingDict))
				{ // if this image id doesn't exist in the dict
				  // new image
					coordsList = new List<Coordinate>();
				}
				else if (!_DF[imageId].TryGetValue(buildingId, out coordsList))
				{ // if this image exists, but it's a new building
				  // new building
					coordsList = new List<Coordinate>();
					buildingDict.Add(buildingId, coordsList);
				}
				else { // this is actually unnecessary, but keeping it here just in case
					coordsList = _DF[imageId][buildingId];
				}

				coordsList.Add(new Coordinate(X[ix], Y[ix]));

				if (_DF.ContainsKey(imageId))
				{
					_DF[imageId][buildingId] = coordsList;
				}
				else {
					var tmp_dict = new Dictionary<int, List<Coordinate>>();
					tmp_dict.Add(buildingId, coordsList);
					_DF.Add(imageId, tmp_dict);
				}
			}

			GeometryFactory cartFactory = new GeometryFactory();

			// after reading in all the points, try to build the polygons
			foreach (var imageGroup in _DF)
			{
				var iId = imageGroup.Key;
				var buildingDict = imageGroup.Value;

				// sort the buildings by building id
				foreach (var building in buildingDict.OrderBy(key => key.Key))
				{
					var bId = building.Key;
					var coordList = building.Value;
					Polygon polygon;

					try
					{
						polygon = (Polygon)cartFactory.CreatePolygon(new LinearRing(coordList.ToArray()));
					}
					catch (Exception e)
					{
						throw new Exception(String.Format("For image {0}, building {1}, there's an exception in building your polygon: {2}", iId, bId, e));
					}

					// save the polygon to dict
					if (DFwithPolygon.ContainsKey(iId))
					{
						DFwithPolygon[iId][bId] = polygon;
					}
					else {
						var tmp_dict = new Dictionary<int, Polygon>();
						tmp_dict.Add(bId, polygon);
						DFwithPolygon.Add(iId, tmp_dict);
					}
				}
			}
			return DFwithPolygon;
		}

		public static double calculateJaccard(Polygon poly1, Polygon poly2)
		{
            double intersection, union;
            try {
                intersection = poly1.Intersection (poly2).Area;
                union = poly1.Union (poly2).Area;
            } catch (Exception) {
                return 0.0;
            }
			return intersection / union;
		}


		public static int argMax(double[] arr)
		{
			double m = arr.Max();
			int p = Array.IndexOf(arr, m);
			return p;
		}
	}
}
