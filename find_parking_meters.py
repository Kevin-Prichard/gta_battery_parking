#!/usr/bin/env python3.10
import logging
from collections import defaultdict
from decimal import Decimal, InvalidOperation

import matplotlib.pyplot as plt
from polycircles import polycircles
import simplekml
from shapely.geometry import Point, Polygon

from utils import rotate2d, load_tsv, make_stylemap, load_boundary_file, wkt_to_kml, print_dict

logger = logging.getLogger(__name__)
K = simplekml

# Based upon https://www.usna.edu/Users/oceano/pguth/md_help/html/approx_equivalents.htm
# 0.00001 deg = 1.11 m
# 0.000001 deg = 0.11 m (7 decimals, cm accuracy)
meter_bb_size = 0.000025  # parking meter bounding box size
blue_zone_width = 0.000025
blue_zone_length = 0.00006
dtsf_grid_rotation = 11.5  # 9.800


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


meter_colors = {
    "Yellow": make_stylemap({"ncol": "5013F0FF", "nwidth": 4, "hcol": "5000FFFF", "hwidth": 16}),
    "Black": make_stylemap({"ncol": "50000000", "nwidth": 4, "hcol": "50585858", "hwidth": 16}),
    "Grey": make_stylemap({"ncol": "508C8C8C", "nwidth": 4, "hcol": "50D0D0D0", "hwidth": 16}),
    "-": make_stylemap({"ncol": "501478FF", "nwidth": 4, "hcol": "501478FF", "hwidth": 16}),
    "Red": make_stylemap({"ncol": "501400F0", "nwidth": 4, "hcol": "501437FD", "hwidth": 16}),
    "Green": make_stylemap({"ncol": "5014F028", "nwidth": 4, "hcol": "5014F0A9", "hwidth": 16}),
    "Blue": make_stylemap({"ncol": "50F03714", "nwidth": 4, "hcol": "50F09A14", "hwidth": 16}),
}
meter_desc = {
    "Yellow": "Commercial Only",
    "Black": "Motorcycle",
    "Grey": "Residential",
    "-": "Eliminated",
    "Red": "Commercial Trucks Only",
    "Green": "15-30 Min Limit",
    "Blue": "Accessible Parking",
}
meter_types = {
    "-": "UNKNOWN",
    "MS": "MOTORCYCLE",
    "SS": "NORMAL"
}


boundaries = {
    "cbd_fidi": {
        "b": load_boundary_file("data/downtownsf_cbd_fidi.json.poly"),
        "n": "Downtown SF CBD Financial District",
        "c": make_stylemap({"ncol": "448F9185", "nwidth": 4, "hcol": "44999B8F", "hwidth": 16}),
    },
    "cbd_jackson": {
        "b": load_boundary_file("data/downtownsf_cbd_jackson_sq.json.poly"),
        "n": "Downtown SF CBD Jackson Square",
        "c": make_stylemap({"ncol": "448F9185", "nwidth": 4, "hcol": "44999B8F", "hwidth": 16}),
    },
    "battery": {
        "b": load_boundary_file("data/battery_qb.json.poly"),
        "n": "Battery Street Quick Build Area",
        "c": make_stylemap({"ncol": "305078F0", "nwidth": 4, "hcol": "305078F0", "hwidth": 16}),
    },
    "battery_adjacent": {
        "b": load_boundary_file("data/battery_adjacent_parking.json.poly"),
        "n": "Battery Street Adjacent Parking Area",
        "c": make_stylemap({"ncol": "5014F0F0", "nwidth": 4, "hcol": "5014F0F0", "hwidth": 16}),
    },
    "sansome": {
        "b": load_boundary_file("data/sansome_qb.json.poly"),
        "n": "Sansome Street Quick Build Area",
        "c": make_stylemap({"ncol": "305078F0", "nwidth": 4, "hcol": "305078F0", "hwidth": 16}),
    },
    "contractors": {
        "b": load_boundary_file("data/contractor_spaces_zone.json.poly"),
        "n": "Area within which we'll search for contractor spaces: yellow and red caps",
        "c": make_stylemap({"ncol": "2514F0F0", "nwidth": 4, "hcol": "2514F0F0", "hwidth": 16}),
    },
    "contractors2": {
        "b": load_boundary_file("data/contractor_tighter.json.poly"),
        "n": "Area #2 within which we'll search for contractor spaces: yellow and red caps",
        "c": make_stylemap({"ncol": "2514F0F0", "nwidth": 4, "hcol": "2514F0F0", "hwidth": 16}),
    },
}


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


def add_blue_zones(doc, battery_bounds):
    zone_count = 0
    for bz in load_tsv("data/Accessible_Curb__Blue_Zone_.tsv"):
        if not bz["shape"]:
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


def add_meters(doc):
    battery = boundaries["battery"]["b"]
    battery_adj = boundaries["battery_adjacent"]["b"]
    # sansome = boundaries["sansome"]["b"]
    cbd_fidi = boundaries["cbd_fidi"]["b"]
    cbd_jackson = boundaries["cbd_jackson"]["b"]
    inside_battery_count = 0
    inside_dtsf_cbd_count = 0
    inside_battery_adj_count = 0
    mtype_batadj = defaultdict(int)
    mtype_cbd = defaultdict(int)
    mtypes_battery_east = defaultdict(int)
    mtypes_battery_west = defaultdict(int)
    post_ids = defaultdict(int)
    for pm in load_tsv("data/Parking_Meters.tsv"):
        p = Point(Decimal(pm["LONGITUDE"]), Decimal(pm["LATITUDE"]))
        pm_battery = battery.contains(p) and pm["STREET_NAME"] == "BATTERY ST"
        # pm_sansome = sansome.contains(p) and pm["STREET_NAME"] == "SANSOME ST"
        pm_dtsf_cbd = cbd_fidi.contains(p) or cbd_jackson.contains(p)
        pm_battery_adj = battery_adj.contains(p)
        if pm_battery:  # or pm_sansome:
            if pm["CAP_COLOR"].lower() in ("red", "yellow"):
                post_ids[pm["POST_ID"]] += 1
            street_num = int(pm['STREET_NUM'])
            if street_num / 2 == int(street_num / 2):
                mtypes_battery_east[f'{pm["CAP_COLOR"]}'] += 1
            else:
                mtypes_battery_west[f'{pm["CAP_COLOR"]}'] += 1
            inside_battery_count += 1
            pmp = doc.newpolygon(name=f"{pm['STREET_NUM']} {pm['STREET_NAME']}\n" +
                                      f"Post ID: {pm['POST_ID']}, Space ID: {pm['PARKING_SPACE_ID']}\n" +
                                      f"[Type: {meter_desc[pm['CAP_COLOR']]}]\n" +
                                      f"(District {pm['Current Supervisor Districts']}, SFPD Central)")
            pmp.outerboundaryis = make_meter(p.x, p.y)
            pmp.placemark.geometry.outerboundaryis.gxaltitudeoffset = 10
            pmp.stylemap = meter_colors[pm["CAP_COLOR"]]
        if pm_dtsf_cbd:
            inside_dtsf_cbd_count += 1
            mtype_cbd[pm["CAP_COLOR"]] += 1
        if pm_battery_adj:
            inside_battery_adj_count += 1
            mtype_batadj[pm["CAP_COLOR"]] += 1

    print("\nBattery East Side Meters")
    for k in sorted(mtypes_battery_east.keys()):
        v = mtypes_battery_east[k]
        print(f"{meter_desc[k]}\t{v}")
    print("\nBattery West Side Meters")
    for k in sorted(mtypes_battery_west.keys()):
        v = mtypes_battery_west[k]
        print(f"{meter_desc[k]}\t{v}")

    print(f"\nInside Battery: {inside_battery_count}")
    print(f"Inside DTSF CBD: {inside_dtsf_cbd_count}")
    print(f"Inside Battery Adjacent: {inside_battery_adj_count}")

    print("\nDTSF CBD Parking Spaces ALL AFFECTED")
    for k in sorted(mtype_cbd.keys()):
        v = mtype_cbd[k]
        both = mtypes_battery_west[k] + mtypes_battery_east[k]
        print(f"{meter_desc[k]}\t{v}\t{both}\t{round(both / mtype_cbd[k] * 100, 2)}%")

    print("\nDTSF CBD Parking Spaces REMOVED")
    for k in sorted(mtype_cbd.keys()):
        v = mtype_cbd[k]
        print(f"{meter_desc[k]}\t{v}\t{mtypes_battery_east[k]}\t" +
              f"{round(mtypes_battery_east[k] / mtype_cbd[k] * 100, 2)}%")

    print("\nBattery Adjacent Spaces\tBattery E+W\tBattery E\tPct E+W\tPct E")
    for k in sorted(mtype_batadj.keys()):
        v = mtype_batadj[k]
        bat_east = mtypes_battery_east[k]
        both = max(1, mtypes_battery_west[k] + bat_east)
        print(f"{meter_desc[k]}\t{v}\t{both}\t{bat_east}\t" +
              f"{round(both / mtype_batadj[k] * 100, 2)}%\t"
              f"{round(bat_east / mtype_batadj[k] * 100, 2)}%")

    with open("post_ids.csv", "w") as fh:
        fh.write("\n".join(sorted(post_ids.keys())))


def make_battery_sansome_qb_map(name):
    doc = K.Kml(name=name)

    for k, b in boundaries.items():
        poly = doc.newpolygon(name=b["n"], description=b["n"])
        poly.outerboundaryis = list(b["b"].exterior.coords)
        poly.placemark.geometry.outerboundaryis.gxaltitudeoffset = 0
        poly.stylemap = b["c"]

    add_meters(doc)
    add_blue_zones(doc, boundaries["battery"]["b"])
    return doc


def add_meters_in_zone(doc, zone_bdy, also_bdy):
    meters_in_color = defaultdict(int)
    meters_out_color = defaultdict(int)
    also_in_color = defaultdict(int)
    also_out_color = defaultdict(int)
    for pm in load_tsv("data/Parking_Meters.tsv"):
        cap = pm["CAP_COLOR"].lower()
        p = Point(Decimal(pm["LONGITUDE"]), Decimal(pm["LATITUDE"]))
        if cap in ("red", "yellow"):
            if zone_bdy.contains(p):
                pmp = doc.newpolygon(name=f"{pm['STREET_NUM']} {pm['STREET_NAME']}\n" +
                                      f"Post ID: {pm['POST_ID']}, Space ID: {pm['PARKING_SPACE_ID']}\n" +
                                      f"[Type: {meter_desc[pm['CAP_COLOR']]}]\n" +
                                      f"(District {pm['Current Supervisor Districts']}, SFPD Central)")
                pmp.outerboundaryis = make_meter(p.x, p.y, width=meter_bb_size*2, length=meter_bb_size*2)
                pmp.placemark.geometry.outerboundaryis.gxaltitudeoffset = 100
                pmp.stylemap = meter_colors[pm["CAP_COLOR"]]
                meters_in_color[cap] += 1
                if also_bdy.contains(p):
                    also_in_color[cap] += 1
                else:
                    also_out_color[cap] += 1
            else:
                meters_out_color[cap] += 1

    print_dict(meters_in_color, "Contractor meters inside zone")
    print_dict(meters_out_color, "Contractor meters outside zone")
    print_dict(also_in_color, "Contractor meters inside zone & on Battery St")
    print_dict(also_out_color, "Contractor meters inside zone, but not on Battery St")


def add_polyline(doc, boundary, altitude):
    poly = doc.newpolygon(name=boundary["n"], description=boundary["n"])
    poly.outerboundaryis = list(boundary["b"].exterior.coords)
    poly.placemark.geometry.outerboundaryis.gxaltitudeoffset = altitude
    poly.stylemap = boundary["c"]


def make_contractor_map(name):
    doc = K.Kml(name=name)

    b = boundaries["battery"]
    add_polyline(doc, b, -10)

    c = boundaries["contractors2"]
    add_polyline(doc, c, -10)

    add_meters_in_zone(doc, c["b"], b["b"])
    doc.save("contractors.kml")


def make_ramp_circle(doc, name, x, y, stylemap, r=meter_bb_size):
    polycircle = polycircles.Polycircle(
        longitude=x, latitude=y, radius=r, number_of_vertices=24)

    circle = doc.newpolygon(
        name=name, outerboundaryis=polycircle.to_kml())
    circle.placemark.geometry.outerboundaryis.gxaltitudeoffset = 5
    circle.stylemap = stylemap


def add_curbs_in_zone(doc, within_bdy):
    ramp_col = make_stylemap({"ncol": "5055F0FF", "nwidth": 16, "hcol": "5055FFFF", "hwidth": 16})
    for c in load_tsv("data/Curb_Ramps.tsv"):
        try:
            p = Point(Decimal(c["Longitude"]), Decimal(c["Latitude"]))
        except InvalidOperation as ioex:
            print(f'Invalid coordinates: Longitude: {c["Longitude"]}, Latitude: {c["Latitude"]}')
        if within_bdy.contains(p):
            name = (f"ocID: {c['ocID']}\n"
                    f'positionOnReturn: {c["positionOnReturn"]}\n'
                    f'conditionScore: {c["conditionScore"]}\n'
                    f'crExist: {c["crExist"]}\n'
                    f'crPossible: {c["crPossible"]}\n'
                    f'curbReturnLoc: {c["curbReturnLoc"]}\n'
                    f'detectableSurf: {c["detectableSurf"]}\n'
                    f'flushToCorner: {c["flushToCorner"]}\n'
                    f'heavyTraffic: {c["heavyTraffic"]}\n'
                    f'insideCrosswalk: {c["insideCrosswalk"]}\n'
                    f'levelLandBottom: {c["levelLandBottom"]}\n'
                    f'levelLandTop: {c["levelLandTop"]}\n'
                    f'lipTooHigh: {c["lipTooHigh"]}')

            make_ramp_circle(doc, name, p.x, p.y, r=5, stylemap=ramp_col)


def make_curb_ramp_map(name):
    doc = K.Kml(name=name)
    b = boundaries["battery"]
    # add_polyline(doc, b, -10)
    add_curbs_in_zone(doc, b["b"])
    doc.save("battery_curb_ramps.kml")


def main_sanity_check():
    p = [(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]
    px, py = zip(*p)
    pol = Polygon(p)
    print(pol.contains(Point(0.5, 0.5)))
    plt.figure()
    plt.plot(px, py)
    plt.show()


if __name__ == "__main__":
    # make_curb_ramp_map("Accessible curb ramps along Battery St in the QB zone")

    make_contractor_map("Contractor parking around Battery, from Sansome & Clay->Front->Market->Sansome.")

    # d = make_battery_sansome_qb_map("Battery Street Parking Spaces")
    # d.save("better.kml")
