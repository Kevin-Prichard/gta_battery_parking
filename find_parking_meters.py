#!/usr/bin/env python3.10

import csv
import typing
from decimal import Decimal
from geopy.distance import great_circle
import json
import logging
import pyproj
from pyproj import CRS
from shapely.geometry import Point, Polygon
from shapely.validation import make_valid
import shapely.ops as ops
from typing import List
from shapely.geometry.polygon import Polygon
from functools import partial


logger = logging.getLogger(__name__)
earth = CRS("ESRI:54009")


def conv_null(sqm):
    return sqm


def conv_sqmi(sqm):
    return sqm / 2.59e+6


def conv_sqkm(sqm):
    return sqm / 1e+6


class PointMiles(Point):
    def distance_mi(self, other_point):
        return great_circle(
            (self.xy[0][0], self.xy[1][0]),
            (other_point.xy[0][0], other_point.xy[1][0])
        ).miles


def polygon_area(poly, fn_conv: typing.Callable):
    geom_area = ops.transform(
        partial(
            pyproj.transform,
            pyproj.Proj(earth),
            pyproj.Proj(
                proj='aea',
                lat_1=poly.bounds[1],
                lat_2=poly.bounds[3]
            )
        ),
        poly)
    return fn_conv(geom_area.area)


def load_meters(fname):
    with open(fname, "r") as f:
        fields = f.readline()[3:]
        fields = fields.split("\t")
        meters = csv.DictReader(f, fields, delimiter="\t")
        all = []
        for meter in meters:
            # print("\n".join(f"{k}:\t{v}" for k, v in meter.items()))
            all.append(meter)
    return all


def load_boundary_file(fname):
    with open(fname, "r") as f:
        all = f.read()
    obj = json.loads(all[all.find("{"):])
    # coords = []
    # for p in obj["coordinates"][0]:
    #     coords.append((p[1], p[0]))
    # import pudb; pu.db
    # pol = Polygon(coords)
    pol = Polygon([(p[1], p[0]) for p in sorted(obj["coordinates"][0])])
    if not pol.is_valid:
        return make_valid(pol)
    return pol


def boundaries_union(boundaries:List[Polygon]):
    poly = Polygon()
    for boundaryset in boundaries:
        poly = poly.union(boundaryset)
    return poly


def find_pm(meters, within_boundaries):
    pass


def main_union_bdy():
    bdys = [
        load_boundary_file("data/downtownsf_cbd_fidi_boundaries.json"),
        load_boundary_file("data/downtownsf_cbd_jackson_sq_boundaries.json"),
        the areas around battery south of Embarcadero Center
    ]
    uno = boundaries_union(bdys)
    # print(polygon_area(uno, conv_sqmi))
    return uno


def main_meters():
    cbd = main_union_bdy()
    battery = load_boundary_file("data/battery_boundaries.json")
    meters = []
    c = 0
    for m in load_meters("data/Parking_Meters.tsv"):
        p = Point(Decimal(m["LATITUDE"]), abs(Decimal(m["LONGITUDE"])))

        if battery.contains(p):
            c += 1
    print(c)
    #     if bdys[0].contains(p):
    #         meters.append(p)
    # print(len(meters))


def main_sanity_check():
    pol = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    print(pol.contains(Point(0.5, 0.5)))


if __name__ == "__main__":
    main_meters()
