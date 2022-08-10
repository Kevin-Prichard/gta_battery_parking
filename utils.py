import csv
import gzip
from io import TextIOWrapper
import json
import logging
import re
from math import radians, cos, sin
import random

import simplekml
from shapely.geometry import Polygon


logger = logging.getLogger(__name__)

K = simplekml


def rotate2d(point, angle, center=(0, 0)):
    rads = radians(angle % 360)
    new_pt = (point[0] - center[0], point[1] - center[1])
    new_pt = (new_pt[0] * cos(rads) - new_pt[1] * sin(rads),
              new_pt[0] * sin(rads) + new_pt[1] * cos(rads))
    new_pt = (new_pt[0] + center[0], new_pt[1] + center[1])
    return new_pt


def load_tsv(fname: str, show_count_every=0):
    if fname.lower().endswith(".tsv.gz"):
        fh = TextIOWrapper(gzip.open(filename=fname, mode="rb"), encoding="utf-8")
    elif fname.lower().endswith(".tsv"):
        fh = open(fname, "r")
    else:
        raise Exception(f"Don't know what to do with this pathname: {fname}")
    try:
        fields_line = fh.readline()
        p = 0
        while ord(fields_line[p]) >= 128:
            p += 1
        fields = fields_line[p:].split("\t")
        reader = csv.DictReader(fh, fields, delimiter="\t")
        for row in reader:
            # if show_count_every and c / show_count_every == int(c / show_count_every):
            #     print(c)
            yield row
    finally:
        fh.close()


def load_boundary_file(fname, pruncate=0) -> Polygon:
    with open(fname, "r") as f:
        all = f.read()
    obj = json.loads(all[all.find("{"):])
    # return Polygon([(p[0], p[1]) for p in obj["coordinates"][0][pruncate:]])
    return Polygon(shell=[(p[0], p[1]) for p in obj["coordinates"][0][pruncate:]])


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


def print_cap_dict(d, label=None, key_subst=None, skip_keys=None):
    if label:
        print(label)
    tot = 0
    for k in sorted(d.keys(), key=lambda x: key_subst[x] if key_subst else x):
        if not skip_keys or k not in skip_keys:
            print(f"{key_subst[k] if key_subst else k}\t{d[k]}")
            tot += d[k]
    print(f"Total: {tot}")


class DictObj(dict):
    def __init__(self, d=None):
        super().__init__(d)

    def __getattr__(self, item):
        if item in self:
            return self[item]
