﻿using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using ClipperLib;

namespace BEE_Clipper
{
    class Program
    {
        public static double Intersection(List<IntPoint> polygonA, List<IntPoint> polygonB)
        {
            var sol = new List<List<IntPoint>>();

            Clipper c = new Clipper();
            c.AddPath(polygonB, PolyType.ptSubject, true);
            c.AddPath(polygonA, PolyType.ptClip, true);
            c.Execute(ClipType.ctIntersection, sol, PolyFillType.pftEvenOdd, PolyFillType.pftEvenOdd);

            if (sol.Count != 0)
            {
                return Clipper.Area(sol[0]);
            }
            else
            {
                return 0.0;
            }
        }

        public static double Union(List<IntPoint> polygonA, List<IntPoint> polygonB)
        {
            var sol = new List<List<IntPoint>>();

            Clipper c = new Clipper();
            c.AddPath(polygonB, PolyType.ptSubject, true);
            c.AddPath(polygonA, PolyType.ptClip, true);
            c.Execute(ClipType.ctUnion, sol, PolyFillType.pftEvenOdd, PolyFillType.pftEvenOdd);

            if (sol.Count != 0)
            {
                return Clipper.Area(sol[0]);
            }
            else
            {
                return 0.0;
            }
        }

        public static double Jaccard(List<IntPoint> polygonA, List<IntPoint> polygonB)
        {
            var intersection = Intersection(polygonA, polygonB);
            var union = Union(polygonA, polygonB);
            return 1 - (intersection / union);

        }

        static void Main(string[] args)
        {
        }
    }
}
