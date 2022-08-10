#!/usr/bin/env python3.10

import json
import sys

import simplekml
from shapely.geometry import Point

from utils import load_tsv, load_boundary_file, wkt_to_kml

K = simplekml


def main(geo_poly):
    """
    Find all businesses by lon/lat within geo_poly, record them to list in_battery, and count.
    :param geo_poly:
    :return: write in_battery to stdout for caller's disposition
    """
    doc = K.Kml(name="test")
    battery_inclusive = load_boundary_file(geo_poly)
    c = 0
    e = 0
    in_battery = []
    x = 0
    for r in load_tsv("data/Registered_Business_Locations_-_San_Francisco.tsv.gz", show_count_every=100):
        try:
            pt = wkt_to_kml(r["Business Location"], doc)
            if not pt['coords']:
                e += 1
            if "battery" in r["Street Address"].lower() or (
                pt['coords'] and battery_inclusive.contains(
                    Point(pt['coords'][0][0], pt['coords'][0][1]))):
                print(r["Street Address"])
                in_battery.append(r)
                c += 1
            x += 1
            if x / 1000 == int(x / 1000):
                print(c, x, e)
        except Exception as ee:
            e += 1
            print(ee)

    print(c, x, e)
    sys.stdout.write(json.dumps(in_battery, indent=4, sort_keys=True))
    print(c)


if __name__ == "__main__":
    # main("data/battery_qb.json.poly")
    main("data/battery_adjacent_parking_wider.json.poly")
