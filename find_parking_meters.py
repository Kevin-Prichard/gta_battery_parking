#!/usr/bin/env python3.10

import csv
import typing
from collections import defaultdict
from decimal import Decimal
from functools import partial
from geopy.distance import great_circle
import json
import logging
from math import sin, cos, radians
import matplotlib.pyplot as plt
import pyproj
from pyproj import CRS
import random
import re

from shapely.geometry import Point, Polygon
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


def rotate2d(point, angle, center=(0, 0)):
    # https://stackoverflow.com/questions/20023209/function-for-rotating-2d-objects
    rads = radians(angle % 360)
    new_pt = (point[0] - center[0], point[1] - center[1])
    new_pt = (new_pt[0] * cos(rads) - new_pt[1] * sin(rads),
                 new_pt[0] * sin(rads) + new_pt[1] * cos(rads))
    new_pt = (new_pt[0] + center[0], new_pt[1] + center[1])
    return new_pt


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
        fields = f.readline()[1:]
        fields = fields.split("\t")
        reader = csv.DictReader(f, fields, delimiter="\t")
        rows = []
        for row in reader:
            yield row


def load_boundary_file(fname, pruncate=0):
    with open(fname, "r") as f:
        all = f.read()
    obj = json.loads(all[all.find("{"):])
    pol = Polygon([(p[0], p[1]) for p in obj["coordinates"][0][pruncate:]])
    return pol


# Based upon https://www.usna.edu/Users/oceano/pguth/md_help/html/approx_equivalents.htm
# 0.00001 deg = 1.11 m
# 0.000001 deg = 0.11 m (7 decimals, cm accuracy)
meter_bb_size = 0.000025  # parking meter bounding box size
blue_zone_width = 0.000025
blue_zone_length = 0.00006
dtsf_grid_rotation = 11.5  # 9.800


# Turns the singular x, y point of a SF parking meter into a square
def make_meter(x, y, width=meter_bb_size, length=meter_bb_size):
    rot_cp = (x, y)
    return [
        rot_cp,
        rotate2d((x - width, y), dtsf_grid_rotation, rot_cp),
        rotate2d((x - width, y - length), dtsf_grid_rotation, rot_cp),
        rotate2d((x, y - length), dtsf_grid_rotation, rot_cp),
        rot_cp,
    ]


def make_stylemap(cols_widths: dict):  # norm_col, norm_width, hi_col, hi_width
    k = simplekml
    sm = k.StyleMap()
    norm = k.Style()
    norm.linestyle.color = cols_widths["ncol"]
    norm.linestyle.width = cols_widths["nwidth"]
    norm.polystyle.color = cols_widths["ncol"]
    norm.polystyle.fill = 1
    norm.polystyle.outline = 1
    sm.normalstyle = norm
    hilite = k.Style()
    hilite.linestyle.color = cols_widths["hcol"]
    hilite.linestyle.width = cols_widths["hwidth"]
    hilite.polystyle.color = cols_widths["hcol"]
    hilite.polystyle.fill = 1
    hilite.polystyle.outline = 1
    sm.highlightstyle = hilite
    return sm


blue_zone_color = make_stylemap({"ncol": "50FF7800", "nwidth": 4, "hcol": "50FF7800", "hwidth": 16})


blue_zone_street_side = {
    "w": "west",
    "west": "west",
    "e": "east",
    "east": "east",
    "n": "north",
    "north": "north",
    "ne": "northeast",
    "s": "south",
    "se": "southeast",
    "sw": "southwest",
    "south": "south",
    "unknown": "<unknown>",
    "": "<unknown>",
}


def add_blue_zones(doc, battery_bounds):
    zone_count = 0
    for bz in load_tsv("data/Accessible_Curb__Blue_Zone_.tsv"):
        if not bz["shape"]:
            # print(json.dumps(bz, indent=4, sort_keys=True))
            continue
        pt = wkt_to_kml(bz["shape"], doc, True)
        x, y = pt['coords'][0][0], pt['coords'][0][1]
        if not battery_bounds.contains(Point(x, y)):
            continue
        bz_street_side = blue_zone_street_side[bz['STSIDE'].lower()]

        zone = doc.newpolygon(
            name=f"{bz['ADDRESS']} & {bz['CROSSST']}, {bz['SITEDETAIL']} " +
                 f"on the {bz_street_side} side of the street.\n" +
                 f"Length: {bz['SPACELENG']}")
        zone.outerboundaryis = make_meter(x, y, width=blue_zone_width, length=blue_zone_length)
        zone.stylemap = blue_zone_color
        zone_count += 1


meter_colors = {
    "Yellow": make_stylemap({"ncol": "5013F0FF", "nwidth": 4, "hcol": "5000FFFF", "hwidth": 16}),
    "Black": make_stylemap({"ncol": "50000000", "nwidth": 4, "hcol": "50585858", "hwidth": 16}),
    "Grey": make_stylemap({"ncol": "508C8C8C", "nwidth": 4, "hcol": "50D0D0D0", "hwidth": 16}),
    "-": make_stylemap({"ncol": "501478FF", "nwidth": 4, "hcol": "501478FF", "hwidth": 16}),
    "Red": make_stylemap({"ncol": "501400F0", "nwidth": 4, "hcol": "501437FD", "hwidth": 16}),
    "Green": make_stylemap({"ncol": "5014F028", "nwidth": 4, "hcol": "5014F0A9", "hwidth": 16}),
}
meter_desc = {
    "Yellow": "Commercial Only",
    "Black": "Motorcycle",
    "Grey": "Residential",
    "-": "Eliminated",
    "Red": "Commercial Trucks Only",
    "Green": "15-30 Min Limit",
}
meter_types = {
    "-": "UNKNOWN",
    "MS": "MOTORCYCLE",
    "SS": "NORMAL"
}


def add_meters(doc):
    battery = boundaries["battery"]["b"]
    cbd_fidi = boundaries["cbd_fidi"]["b"]
    cbd_jackson = boundaries["cbd_jackson"]["b"]
    inside_battery_count = 0
    inside_fidi_cbd_count = 0
    outside_battery_count = 0
    mtype_cbd_fidi = defaultdict(int)
    mtypes_battery_east = defaultdict(int)
    mtypes_battery_west = defaultdict(int)
    for m in load_tsv("data/Parking_Meters.tsv"):
        p = Point(Decimal(m["LONGITUDE"]), Decimal(m["LATITUDE"]))
        if battery.contains(p) and m["STREET_NAME"] == "BATTERY ST":
            street_num = int(m['STREET_NUM'])
            if street_num / 2 == int(street_num / 2):
                mtypes_battery_east[f'{m["CAP_COLOR"]}'] += 1
            else:
                mtypes_battery_west[f'{m["CAP_COLOR"]}'] += 1
            inside_battery_count += 1
            pm = doc.newpolygon(name=f"{m['STREET_NUM']} {m['STREET_NAME']}\n" +
                                     f"Post ID: {m['POST_ID']}, Space ID: {m['PARKING_SPACE_ID']}\n" +
                                     f"[Type: {meter_desc[m['CAP_COLOR']]}]\n" +
                                     f"(District {m['Current Supervisor Districts']}, SFPD Central)"
                                )
            pm.outerboundaryis = make_meter(p.x, p.y)
            pm.placemark.geometry.outerboundaryis.gxaltitudeoffset = 10
            pm.stylemap = meter_colors[m["CAP_COLOR"]]
        elif cbd_fidi.contains(p):
            inside_fidi_cbd_count += 1
            mtype_cbd_fidi[m["CAP_COLOR"]] += 1
        else:
            outside_battery_count += 1
    for k, v in mtypes_battery_east.items():
        print(f"{k}\t{v}")
    print(f"Inside Battery: {inside_battery_count}")
    print(f"Outside Battery: {outside_battery_count}")
    print(f"Inside DTSF CBD: {inside_fidi_cbd_count}")
    print("DTSF CBD Parking Spaces ALL")
    for k, v in mtype_cbd_fidi.items():
        both = mtypes_battery_west[k] + mtypes_battery_east[k]
        print(f"{k}\t{v}\t{both}\t{round(both / mtype_cbd_fidi[k] * 100, 2)}%")
    print("DTSF CBD Parking Spaces REMOVED")
    for k, v in mtype_cbd_fidi.items():
        print(f"{k}\t{v}\t{mtypes_battery_east[k]}\t" +
              f"{round(mtypes_battery_east[k] / mtype_cbd_fidi[k] * 100, 2)}%")


def random_color():
    r = lambda: random.randint(0, 255)
    return '#FF{:02X}{:02X}{:02X}'.format(r(), r(), r())


def wkt_to_kml(wkt, doc, dry=False):
    if not wkt:
        return {"type": "", "coords": ""}

    parts = re.match(r"(\w+) \(+([^)]*)\)+", wkt)
    splitted = re.findall(r"[^ ,]+", parts.group(2))
    spl = [float(i) for i in splitted]
    coords = list(zip(spl[::2], spl[1::2]))

    if not dry:
        k = doc.newlinestring(name="abc")
        k.coords = coords
        k.style.linestyle.color = random_color()
        k.style.linestyle.width = 12
    return {"type": parts.group(1), "coords": coords}


boundaries = {
    "cbd_fidi": {
        "b": load_boundary_file("data/downtownsf_cbd_fidi_boundaries.json"),
        "n": "Downtown SF CBD Financial District",
        "c": make_stylemap({"ncol": "448F9185", "nwidth": 4, "hcol": "44999B8F", "hwidth": 16}),

    },
    "cbd_jackson": {
        "b": load_boundary_file("data/downtownsf_cbd_jackson_sq_boundaries.json"),
        "n": "Downtown SF CBD Jackson Square",
        "c": make_stylemap({"ncol": "448F9185", "nwidth": 4, "hcol": "44999B8F", "hwidth": 16}),
    },
    "battery": {
        "b": load_boundary_file("data/battery_boundaries.json"),
        "n": "Battery Street",
        "c": make_stylemap({"ncol": "305078F0", "nwidth": 4, "hcol": "305078F0", "hwidth": 16}),
    },
    # the areas around battery south of Embarcadero Center
    # return MultiPolygon(boundaries), boundaries
}


def make_battery_street(name):
    k = simplekml
    doc = k.Kml(name=name)
    # doc.stylemaps.append(sm)

    for k, b in boundaries.items():
        poly = doc.newpolygon(name=b["n"], description=b["n"])
        poly.outerboundaryis = list(b["b"].exterior.coords)
        poly.stylemap = b["c"]

    add_meters(doc)
    add_blue_zones(doc, boundaries["battery"]["b"])
    return doc


def main_sanity_check():
    p = [(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]
    px, py = zip(*p)
    pol = Polygon(p)
    print(pol.contains(Point(0.5, 0.5)))
    plt.figure()
    plt.plot(px, py)
    plt.show()


if __name__ == "__main__":
    d = make_battery_street("Battery Street Features")
    d.save("better.kml")
