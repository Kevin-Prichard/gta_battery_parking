

### Installation and use
```shell
# Install dependencies
$ pip install -r requirements

# Run the script, which outputs an analysis to stdout, and also generates `better.kml`, which is meant to be added as overlay to a Google Map
$ ./find_parking_meters.py
```

### Definitions of geographic boundaries
Definitions are drawn using this polyline tool website, which allows one to draw polyline definitions on a Google Maps-like map-
    https://www.keene.edu/campus/maps/tool/

It produces two things: a list of lat/lon coordinates, and a JSON containing those coordinates.

That format is preserved when storing those definitions in this project, because: the JSON is imported by find_parking_meters.py (via `load_boundary_file()` from utils.py, which retrieves only the JSON.) The lat/lon list super-useful whenever the boundaries need adjusting.  The list can be copy-pasted directly to the import box of the [Keene State Polyline tool](https://www.keene.edu/campus/maps/tool/).

### Incorporating SF Data
Much of San Francisco's data regime is provided as single tables that can be exported as TSV.  Those files are downloaded to ./data, and imported using `load_tsv()`.

SF Data files of physical objects and boundaries typically contain the columns LATITUDE & LONGITUDE.  Some contain [WKT definitions of points](https://en.wikipedia.org/wiki/Well-known_text_representation_of_geometry), polylines, or polygons. Those are imported using wkt_to_kml(), which generates a simplekml LineString whether or not the original called for a polygon or linestring. Seems to work fine, but the only use-case so far is parking meter Point locations. I suppose this may call for a cascading if/elif to produce specific kml objects, in the future.
