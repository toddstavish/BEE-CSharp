# Building Extraction Evaluation (BEE) in C#/.NET

A C# console application that performs polygon comparison for building extraction evaluation using [Intersection over Union (IoU)](https://en.wikipedia.org/wiki/Jaccard_index). 

## Development steps
1. git clone https://github.com/toddstavish/BEE-CSharp.git
2. Install [NuGet](https://www.nuget.org/)
3. Install NetTopologySuite - PM> Install-Package NetTopologySuite
4. Install GeoJSON IO Library - PM> Install-Package NetTopologySuite.IO.GeoJSON
5. Install GDAL - PM> Install-Package GDAL
6. Install Clipper - PM> Install-Package Clipper

## To-do
1. Test over robust lat/long dataset
2. Compare against GEOS 
3. Test if there is intersection before calculating Jaccard

## License
See [LICENSE](./LICENSE).
