import csv
import json
import re
from math import radians, cos, sin
import random

import simplekml
from shapely.geometry import Polygon


K = simplekml

def rotate2d(point, angle, center=(0, 0)):
    rads = radians(angle % 360)
    new_pt = (point[0] - center[0], point[1] - center[1])
    new_pt = (new_pt[0] * cos(rads) - new_pt[1] * sin(rads),
              new_pt[0] * sin(rads) + new_pt[1] * cos(rads))
    new_pt = (new_pt[0] + center[0], new_pt[1] + center[1])
    return new_pt


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


def make_stylemap(cols_widths: dict):  # norm_col, norm_width, hi_col, hi_width
    sm = K.StyleMap()
    norm = K.Style()
    norm.linestyle.color = cols_widths["ncol"]
    norm.linestyle.width = cols_widths["nwidth"]
    norm.polystyle.color = cols_widths["ncol"]
    norm.polystyle.fill = 1
    norm.polystyle.outline = 1
    sm.normalstyle = norm
    hilite = K.Style()
    hilite.linestyle.color = cols_widths["hcol"]
    hilite.linestyle.width = cols_widths["hwidth"]
    hilite.polystyle.color = cols_widths["hcol"]
    hilite.polystyle.fill = 1
    hilite.polystyle.outline = 1
    sm.highlightstyle = hilite
    return sm


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
        K = doc.newlinestring(name="abc")
        K.coords = coords
        K.style.linestyle.color = random_color()
        K.style.linestyle.width = 12
    return {"type": parts.group(1), "coords": coords}


def print_dict(d, label):
    print(label)
    for k, v in d.items():
        print(f"{k}\t{v}")
