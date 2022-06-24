#!/usr/bin/env python3.10

import csv
import typing
from decimal import Decimal
from functools import partial
from geopy.distance import great_circle
import json
import logging
import matplotlib.pyplot as plt
import pyproj
from pyproj import CRS
import random
import re
from shapely import wkt
from shapely.validation import make_valid
from shapely.geometry import Point, Polygon, MultiPolygon
import shapely.ops as ops
import simplekml


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


def load_tsv(fname):
    with open(fname, "r") as f:
        fields = f.readline()[3:]
        fields = fields.split("\t")
        reader = csv.DictReader(f, fields, delimiter="\t")
        rows = []
        for row in reader:
            rows.append(row)
    return rows


def load_boundary_file(fname):
    with open(fname, "r") as f:
        all = f.read()
    obj = json.loads(all[all.find("{"):])
    pol = Polygon([(p[0], p[1]) for p in obj["coordinates"][0]])
    return pol


def main_union_bdy():
    boundaries = [
        load_boundary_file("data/downtownsf_cbd_fidi_boundaries.json"),
        load_boundary_file("data/downtownsf_cbd_jackson_sq_boundaries.json"),
        # the areas around battery south of Embarcadero Center
    ]
    return MultiPolygon(boundaries), boundaries


def main_meters():
    cbd = main_union_bdy()
    battery = load_boundary_file("data/battery_boundaries.json")
    meters = []
    metersx, metersy = [], []
    c = 0
    for m in load_tsv("data/Parking_Meters.tsv"):
        p = Point(Decimal(m["LATITUDE"]), abs(Decimal(m["LONGITUDE"])))

        if battery.contains(p):
            c += 1
            metersx.append(p.x)
            metersy.append(p.y)
            print(p.x, p.y)
    print(c)

    plt.figure()
    plt.plot(metersx, metersy)
    plt.show()


def random_color():
    r = lambda: random.randint(0, 255)
    return '#FF{:02X}{:02X}{:02X}'.format(r(), r(), r())


def wkt_to_kml(wkt, doc, style):
    parts = re.match(r"(\w+) \(+([^)]*)\)+", wkt)
    splitted = re.findall(r"[^ ,]+", parts.group(2))
    spl = [float(i) for i in splitted]
    coords = list(zip(spl[::2], spl[1::2]))

    k = doc.newlinestring(name="abc")
    k.coords = coords
    k.style.linestyle.color = random_color()
    k.style.linestyle.width = 12
    # k.style.linestyle = style

    # k.linestyle = style
    # k.style.linestyle.color = color
    # k.style.linestyle.width = width


def new_folder(doc, label):
    folder = doc.newfolder(name=label)
    # folder.style = style
    folder.altitudemode = simplekml.AltitudeMode.relativetoground
    return folder


def new_style(color, opacity, width=4):
    # style = simplekml.Style()
    lstyle = simplekml.LineStyle()
    lstyle.color = simplekml.Color.changealpha(color, opacity)
    lstyle.width = width
    # style.linestyle = lstyle
    return lstyle


# KML hex color format: #AABBGGRR
kcols = simplekml.Color
COL_BLACK = new_style(kcols.darkslategray, '80', 4)
COL_BLUE = new_style(kcols.blueviolet, '80', 12)
COL_GRAY = new_style(kcols.lightslategray, '80', 4)
COL_RED = new_style(kcols.indianred, '80', 8)


def draw_downtownsf_cbd(draw_streets: bool):
    cnt = 0
    doc = simplekml.Kml()
    all_b, bs = main_union_bdy()
    all_b = make_valid(all_b)
    folder = new_folder(doc, "Downtown CBD")  # , COL_RED, 8)
    for b in bs:
        wkt_to_kml(str(b), folder, COL_RED)
    if draw_streets:
        folder = new_folder(doc, "SF City Streets")  # , COL_BLUE, 4)
        sf_streets = load_tsv("data/sf_streets_polygons.tsv")
        for s in sf_streets:
            p = wkt.loads(s["_geom"])
            if not p.is_valid:
                p = make_valid(p)
            if p.intersects(all_b):
                wkt_to_kml(s["_geom"], folder, COL_BLUE)
            cnt += 1
            if cnt / 2500 == int(cnt / 2500):
                print(cnt)

    doc.save("temp.kml")
    return doc, all_b


def main_sanity_check():
    p = [(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]
    px, py = zip(*p)
    pol = Polygon(p)
    print(pol.contains(Point(0.5, 0.5)))
    plt.figure()
    plt.plot(px, py)
    plt.show()


if __name__ == "__main__":
    draw_downtownsf_cbd(False)
