from shapely.geometry import Polygon
from simplekml import StyleMap

from utils import load_boundary_file, make_stylemap, DictObj


class Boundary:
    b: Polygon = None
    n: str = None
    c: StyleMap = None
    a: float = None

    def __init__(self, b: Polygon, n: str, c: StyleMap, a: float = 0.0):
        self.b = b
        self.n = n
        self.c = c
        self.a = a


boundaries = DictObj({
    "cbd_fidi": Boundary(
        b=load_boundary_file("data/downtownsf_cbd_fidi.json.poly"),
        n="Downtown SF CBD Financial District",
        c=make_stylemap({"ncol": "448F9185", "nwidth": 4, "hcol": "44999B8F", "hwidth": 16}),
    ),
    "cbd_jackson": Boundary(
        b=load_boundary_file("data/downtownsf_cbd_jackson_sq.json.poly"),
        n="Downtown SF CBD Jackson Square",
        c=make_stylemap({"ncol": "448F9185", "nwidth": 4, "hcol": "44999B8F", "hwidth": 16}),
    ),
    "battery_qb": Boundary(
        b=load_boundary_file("data/battery_qb.json.poly"),
        n="Battery Street Quick Build Area",
        c=make_stylemap({"ncol": "305078F0", "nwidth": 4, "hcol": "305078F0", "hwidth": 16}),
    ),
    "battery_adjacent": Boundary(
        b=load_boundary_file("data/battery_adjacent_parking.json.poly"),
        n="Battery Street Adjacent Parking Area, Green St & Sansome to Front Sts",
        c=make_stylemap({"ncol": "5014F0F0", "nwidth": 4, "hcol": "5014F0F0", "hwidth": 16}),
    ),
    "battery_all_parking": Boundary(
        b=load_boundary_file("data/battery_all_parking.json.poly"),
        n="Battery Street All Parking Area, Vallejo to Market",
        c=make_stylemap({"ncol": "5014F0F0", "nwidth": 4, "hcol": "5014F0F0", "hwidth": 16}),
    ),
    "sansome": Boundary(
        b=load_boundary_file("data/sansome_qb.json.poly"),
        n="Sansome Street Quick Build Area",
        c=make_stylemap({"ncol": "305078F0", "nwidth": 4, "hcol": "305078F0", "hwidth": 16}),
    ),
    "contractors": Boundary(
        b=load_boundary_file("data/contractor_spaces_zone.json.poly"),
        n="Area within which we'll search for contractor spaces: yellow and red caps",
        c=make_stylemap({"ncol": "2514F0F0", "nwidth": 4, "hcol": "2514F0F0", "hwidth": 16}),
    ),
    "contractors2": Boundary(
        b=load_boundary_file("data/contractor_tighter.json.poly"),
        n="Area #2 within which we'll search for contractor spaces: yellow and red caps",
        c=make_stylemap({"ncol": "2514F0F0", "nwidth": 4, "hcol": "2514F0F0", "hwidth": 16}),
    ),
    "bcna_below_bway": Boundary(
        b=load_boundary_file("data/bcna_below_broadway.json.poly"),
        n="BCNA Below Broadway, to Market & Embarcadero",
        c=make_stylemap({"ncol": "50144BF5", "nwidth": 16, "hcol": "50144BF5", "hwidth": 16}),
    ),
    "battery_westward": Boundary(
        b=load_boundary_file("data/battery_west_to_van_ness.json.poly"),
        n="Battery Westward to Van Ness, From Broadway to Market",
        c=make_stylemap({"ncol": "5000C814", "nwidth": 16, "hcol": "5000C814", "hwidth": 16}),
    ),
    "battery_bway_inversion": Boundary(
        b=load_boundary_file("data/bcna_bway_inversion.json.poly"),
        n="The 99% of SF Outside of BCNA below Broadway",
        c=make_stylemap({"ncol": "5000C814", "nwidth": 16, "hcol": "5000C814", "hwidth": 16}),
    ),
    "battery_embarcadero_market": Boundary(
        b=load_boundary_file("data/battery_embarcadero_to_market.json.poly"),
        n="From Battery to Embarcadero down to Market Street",
        c=make_stylemap({"ncol": "FF191D1F", "nwidth": 0, "hcol": "FF191D1F", "hwidth": 0}),
        a=100.0,
    ),
    "district_3": Boundary(
        b=load_boundary_file("data/district_3.json.poly"),
        n="SF Supervisor District 3",
        c=make_stylemap({"ncol": "80B3B1FD", "nwidth": 0, "hcol": "80333333", "hwidth": 32}),
        a=10.0,
    ),
})
