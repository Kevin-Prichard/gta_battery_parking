#!/usr/bin/env python3.10
from collections import defaultdict
from decimal import Decimal, InvalidOperation
import logging
from functools import partial
from itertools import permutations
from typing import List

import matplotlib.pyplot as plt
from polycircles import polycircles
from pyproj import Geod
import simplekml
from shapely.geometry import Point, Polygon

from defs.boundaries import Boundary, boundaries
from defs.meters import (meter_bb_size, blue_zone_width, blue_zone_length,
                         dtsf_grid_rotation, sqkm2sqmi, blue_zone_color,
                         blue_zone_street_side, meter_colors, meter_desc)
from utils import rotate2d, load_tsv, make_stylemap, wkt_to_kml, print_cap_dict


logger = logging.getLogger(__name__)
K = simplekml
geod = Geod(ellps="WGS84")


def make_meter(x, y, width=meter_bb_size, length=meter_bb_size):
    """
    Turns the singular lon, latpoint of an SF parking meter into a square
    :param x: latitude
    :param y: longitude
    :param width: width of pkg meter plot
    :param length: height of pkg meter plot
    :return:
    """
    rot_cp = (x, y)
    return [
        rot_cp,
        rotate2d((x - width, y), dtsf_grid_rotation, rot_cp),
        rotate2d((x - width, y - length), dtsf_grid_rotation, rot_cp),
        rotate2d((x, y - length), dtsf_grid_rotation, rot_cp),
        rot_cp,
    ]


def add_blue_zones(doc, bounds):
    """
    Plots blue zones within :bounds: to :doc:, from https://catalog.data.gov/dataset/accessible-curb-blue-zone
    :param doc: a simplekml.Kml obj
    :param bounds: a shapely polygon
    :return: None
    """
    zone_count = 0
    for bz in load_tsv("data/Accessible_Curb__Blue_Zone_.tsv"):
        if not bz["shape"]:
            continue
        pt = wkt_to_kml(bz["shape"], doc, True)
        x, y = pt['coords'][0][0], pt['coords'][0][1]
        if not bounds.contains(Point(x, y)):
            continue
        bz_street_side = blue_zone_street_side[bz['STSIDE'].lower()]

        zone = doc.newpolygon(
            name=f"{bz['ADDRESS']} & {bz['CROSSST']}, {bz['SITEDETAIL']} " +
                 f"on the {bz_street_side} side of the street.\n" +
                 f"Length: {bz['SPACELENG']}")
        zone.outerboundaryis = make_meter(x, y, width=blue_zone_width, length=blue_zone_length)
        zone.stylemap = blue_zone_color
        zone_count += 1


def add_meters_to_sansome_qb_map(doc):
    battery = boundaries["battery_qb"].b
    battery_adj = boundaries["battery_adjacent"].b
    cbd_fidi = boundaries["cbd_fidi"].b
    cbd_jackson = boundaries["cbd_jackson"].b
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
        poly = doc.newpolygon(name=b.n, description=b.n)
        poly.outerboundaryis = list(b.b.exterior.coords)
        poly.placemark.geometry.outerboundaryis.gxaltitudeoffset = 0
        poly.stylemap = b.c

    add_meters_to_sansome_qb_map(doc)
    add_blue_zones(doc, boundaries["battery_qb"].b)
    return doc


def add_meters_in_zone(doc, zone_bdy, also_bdy, make_polys=True, addl_inclusion_fn=None,
                       wanted_caps=None, show_outside=True, wanted_caps_name="Contractor meters"):
    meters_in_color = defaultdict(int)
    meters_out_color = defaultdict(int)
    also_in_color = defaultdict(int)
    also_out_color = defaultdict(int)
    for pm in load_tsv("data/Parking_Meters.tsv"):
        cap = pm["CAP_COLOR"]
        p = Point(Decimal(pm["LONGITUDE"]), Decimal(pm["LATITUDE"]))
        if not wanted_caps or cap in wanted_caps:
            if zone_bdy.contains(p):
                if not addl_inclusion_fn or addl_inclusion_fn(pm, p):
                    # print(f"Included: {pm['POST_ID']}")
                    if make_polys:
                        pmp = doc.newpolygon(
                            name=f"{pm['STREET_NUM']}"
                                 f"{pm['STREET_NAME']}\n"
                                 f"Post ID: {pm['POST_ID']}, "
                                 f"Space ID: {pm['PARKING_SPACE_ID']}\n"
                                 f"[Type: {meter_desc[pm['CAP_COLOR']]}]\n"
                                 f"(District {pm['Current Supervisor Districts']}, SFPD Central)")
                        pmp.outerboundaryis = make_meter(p.x, p.y, width=meter_bb_size * 2, length=meter_bb_size * 2)
                        pmp.placemark.geometry.outerboundaryis.gxaltitudeoffset = 100
                        pmp.stylemap = meter_colors[pm["CAP_COLOR"]]
                    meters_in_color[cap] += 1
                    if also_bdy:
                        if also_bdy.contains(p):
                            also_in_color[cap] += 1
                        else:
                            also_out_color[cap] += 1
                # else:
                #     print(f"Excluded: {pm['POST_ID']}")
            else:
                meters_out_color[cap] += 1

    skip_rem = ["-"]
    dolabs = False
    print_cap_dict(meters_in_color, f"{wanted_caps_name} inside zone" if dolabs else "", meter_desc, skip_rem)
    if show_outside:
        print_cap_dict(meters_out_color, f"{wanted_caps_name} outside zone" if dolabs else "", meter_desc, skip_rem)
    if also_bdy:
        print_cap_dict(also_in_color, f"{wanted_caps_name} inside main zone & additional zone" if dolabs else "", meter_desc, skip_rem)
        if show_outside:
            print_cap_dict(also_out_color, f"{wanted_caps_name} inside main zone, but not in additional zone" if dolabs else "", meter_desc, skip_rem)


def add_polyline(doc, boundary, altitude: float = None):
    poly = doc.newpolygon(name=boundary.n, description=boundary.n)
    poly.outerboundaryis = list(boundary.b.exterior.coords)
    poly.placemark.geometry.outerboundaryis.gxaltitudeoffset = boundary.a or altitude
    poly.stylemap = boundary.c


def make_contractor_map(name):
    doc = K.Kml(name=name)

    b = boundaries["battery_qb"]
    add_polyline(doc, b, -10)

    c = boundaries["contractors2"]
    add_polyline(doc, c, -10)

    add_meters_in_zone(doc, c.b, b.b)
    doc.save("kml/contractors.kml")


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
    b = boundaries["battery_qb"]
    add_curbs_in_zone(doc, b.b)
    doc.save("kml/battery_curb_ramps.kml")


def main_sanity_check():
    p = [(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]
    px, py = zip(*p)
    pol = Polygon(p)
    print(pol.contains(Point(0.5, 0.5)))
    plt.figure()
    plt.plot(px, py)
    plt.show()


def get_area2(poly):
    # https://stackoverflow.com/a/64165076/604811
    return abs(geod.geometry_area_perimeter(poly)[0])


def paired_areas(b1: Boundary, b2: Boundary):
    bdy1: Polygon = b1.b
    bdy2: Polygon = b2.b
    precish = 3

    area1, area2 = get_area2(bdy1) / 1e6, get_area2(bdy2) / 1e6
    print(f"\nAreas <{b1.n}> vs <{b2.n}>")
    print(f"{b1.n}: {round(area1, precish):,} sqkm ({round(area1 * sqkm2sqmi, precish):,} sqmi)")
    print(f"{b2.n}: {round(area2, precish):,} sqkm ({round(area2 * sqkm2sqmi, precish):,} sqmi)")
    min_area, max_area = min(area1, area2), max(area1, area2)
    print(f"Difference: {round(max_area - min_area, precish):,} sqkm ({round((max_area - min_area) * sqkm2sqmi, precish)} sqmi)")
    print(f"Ratio sqkm: {round(max_area, precish)}  / {round(min_area, 1)} = {round(max_area / min_area, precish)} to 1")
    print(f"Ratio sqmi: {round(max_area * sqkm2sqmi, precish)}  / {round(min_area * sqkm2sqmi, precish)} = {round((max_area * sqkm2sqmi) / (min_area * sqkm2sqmi), precish)} to 1")


def paired_areas_all(areas: List[str]):
    for permu in permutations(areas):
        paired_areas(boundaries[permu[0]], boundaries[permu[1]])


def is_east_or_west_meter(odd_or_even_wanted: bool, meter, point):
    """
    :param odd_or_even_wanted: bool, False==odd, True==even
    :param meter: for meter["STREET_NUM"]
    :param point: not used yet
    :return: bool

    Odd STREET_NUM and even wanted
    >>> bool(3 % 2 ^ True)
    False

    Odd STREET_NUM and odd wanted
    >>> bool(3 % 2 ^ False)
    True

    Even STREET_NUM and even wanted
    >>> bool(4 % 2 ^ True)
    True

    Odd STREET_NUM and odd wanted
    >>> bool(4 % 2 ^ False)
    False
    """
    return bool(int(meter["STREET_NUM"]) % 2 ^ odd_or_even_wanted)


def meter_counts_by_areas_east_vs_west(areas):
    doc = K.Kml(name=f"Areas: {', '.join(areas)}")
    for area in areas:
        for odd_or_even_wanted in (True, False):
            east_or_west_label = "East" if odd_or_even_wanted else "West"
            incl_fn = partial(is_east_or_west_meter, odd_or_even_wanted)
            print(f"\n{boundaries[area].n} {east_or_west_label}")
            add_meters_in_zone(doc, boundaries[area].b, None, make_polys=True,
                               addl_inclusion_fn=incl_fn, show_outside=False)
    return doc


def meter_counts_by_areas(areas):
    doc = K.Kml(name=f"Areas: {', '.join(areas)}")
    for area in areas:
        print(f"\n{boundaries[area].n}")
        add_meters_in_zone(
            doc, boundaries[area].b, also_bdy=None, make_polys=True, show_outside=False)
    return doc


def make_boundary_maps(boundaryset: List[Boundary], kml_pathname: str):
    doc = K.Kml()
    for boundary in boundaryset:
        add_polyline(doc, boundary)
    doc.save(kml_pathname)


if __name__ == "__main__":
    # make_boundary_maps(
    #     [boundaries.district_3, boundaries.battery_embarcadero_market],
    #     "district_3-battery.kml")

    doc = meter_counts_by_areas_east_vs_west(["battery_all_parking"])
    # add_blue_zones(doc, boundaries["battery_adjacent"].b)
    # doc.save("saturday3.kml")

    # test_area()
    # paired_areas_all(["bcna_below_bway", "battery_westward", "battery_bway_inversion"])

    # make_curb_ramp_map("Accessible curb ramps along Battery St in the QB zone")

    # make_contractor_map("Contractor parking around Battery, from Sansome & Clay->Front->Market->Sansome.")

    # d = make_battery_sansome_qb_map("Battery Street Parking Spaces")
    # d.save("better.kml")
