# Test 1 ->

Notes: Ground truth compared to itself.

[Truth Polygon Map](https://github.com/toddstavish/BEE-CSharp/blob/master/data/Rio/rio_test_aoi1.geojson)

[Test Polygon Map](https://github.com/toddstavish/BEE-CSharp/blob/master/data/Rio_Submission_Testing/Rio_sample_challenge_submission1.geojson)

Precision =  1.0

Recall =  1.0

# Test 2 ->

Notes: Proposal footprints are slightly shifted/translated.

[Truth Polygon Map](https://github.com/toddstavish/BEE-CSharp/blob/master/data/Rio/rio_test_aoi2.geojson)

[Test Polygon Map](https://github.com/toddstavish/BEE-CSharp/blob/master/data/Rio_Submission_Testing/Rio_sample_challenge_submission2.geojson)

Precision =  0.2

Recall =  0.266666666667

# Test 3 ->

Notes: Reduced the number of buildings for the proposal. **Small number of proposals.**

[Truth Polygon Map](https://github.com/toddstavish/BEE-CSharp/blob/master/data/Rio/rio_test_aoi3.geojson)

[Test Polygon Map](https://github.com/toddstavish/BEE-CSharp/blob/master/data/Rio_Submission_Testing/Rio_sample_challenge_submission3.geojson)

Precision =  1.0

Recall =  0.4

# Test 4 ->

Notes: Smaller buildings are removed for the proposal. **Small number of proposals.**

[Truth Polygon Map](https://github.com/toddstavish/BEE-CSharp/blob/master/data/Rio/rio_test_aoi4.geojson)

[Test Polygon Map](https://github.com/toddstavish/BEE-CSharp/blob/master/data/Rio_Submission_Testing/Rio_sample_challenge_submission4.geojson)

Precision =  1.0

Recall =  0.428571428571

# Test 5 ->

Notes: Building are removed from truth for the proposal. **Small number of proposals.**

[Truth Polygon Map](https://github.com/toddstavish/BEE-CSharp/blob/master/data/Rio/rio_test_aoi5.geojson)

[Test Polygon Map](https://github.com/toddstavish/BEE-CSharp/blob/master/data/Rio_Submission_Testing/Rio_sample_challenge_submission5.geojson)

Precision =  1.0

Recall =  0.521739130435

# Test 6 ->

Notes: Root's handtruth vs DG's handtruth. **Small number of proposals.**

[Truth Polygon Map](https://github.com/toddstavish/BEE-CSharp/blob/master/data/Rio/rio_test_aoi1.geojson)

[Test Polygon Map](https://github.com/toddstavish/BEE-CSharp/blob/master/data/Rio_Hand_Truth_AOI1/AOI1_Hand1.geojson)

Precision =  1.0

Recall =  1.13793103448

# Test 7 ->

Notes: 10m buffer (proposed polygons are expanded truth polygons)

[Truth Polygon Map](https://github.com/toddstavish/BEE-CSharp/blob/master/data/Rio/rio_test_aoi1.geojson)

[Test Polygon Map](https://github.com/toddstavish/BEE-CSharp/blob/master/data/Rio_Hand_Truth_AOI1/Rio_test_aoi1_WGS84_10mbuffer.geojson)

Precision =  0.0

Recall =  0.0

# Test 8 ->

Notes: Notes: 2.5m buffer (proposed polygons are expanded truth polygons)

[Truth Polygon Map](https://github.com/toddstavish/BEE-CSharp/blob/master/data/Rio/rio_test_aoi1.geojson)

[Test Poloygon Map](https://github.com/toddstavish/BEE-CSharp/blob/master/data/Rio_Hand_Truth_AOI1/Rio_test_aoi1_WGS84_2p5mbuffer.geojson)

Precision =  0.0235294117647

Recall =  0.0689655172414

# Test 9 ->

Notes: Notes: 4.5m buffer (proposed polygons are expanded truth polygons)

[Truth Polygon Map](https://github.com/toddstavish/BEE-CSharp/blob/master/data/Rio/rio_test_aoi1.geojson)

[Test Polygon Map](https://github.com/toddstavish/BEE-CSharp/blob/master/data/Rio_Hand_Truth_AOI1/Rio_test_aoi1_WGS84_5mbuffer.geojson)

Precision =  0.0

Recall =  0.0

# Test 10 ->

Notes: 7.5m buffer (proposed polygons are expanded truth polygons)

[Truth Polygon Map](https://github.com/toddstavish/BEE-CSharp/blob/master/data/Rio/rio_test_aoi1.geojson)

[Test Polygon Map](https://github.com/toddstavish/BEE-CSharp/blob/master/data/Rio_Hand_Truth_AOI1/Rio_test_aoi1_WGS84_7p5mbuffer.geojson)

Precision =  0.0

Recall =  0.0

# Test 11 ->

Notes: Negative 2.5 buffer (proposed polygons are shrunken truth polygons). **Small number of proposals.**

[Truth Polygon Map](https://github.com/toddstavish/BEE-CSharp/blob/master/data/Rio/rio_test_aoi1.geojson)

[Test Polygon Map](https://github.com/toddstavish/BEE-CSharp/blob/master/data/Rio_Hand_Truth_AOI1/Rio_test_aoi1_WGS84_Neg2p5mbuffer.geojson)

Precision =  1.0

Recall =  0.793103448276
