from utils import make_stylemap


# Based upon https://www.usna.edu/Users/oceano/pguth/md_help/html/approx_equivalents.htm
# 0.00001 deg = 1.11 m
# 0.000001 deg = 0.11 m (7 decimals, cm accuracy)
meter_bb_size = 0.000025  # parking meter bounding box size
blue_zone_width = 0.000025
blue_zone_length = 0.00006
dtsf_grid_rotation = 11.5  # 9.800
sqmi2sqkm = 2.58999
sqkm2sqmi = 0.386102

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
    "Yellow": "Contractors Only",
    "Black": "Motorcycle",
    "Grey": "Residential",
    "-": "Eliminated",
    "Red": "Contractors Trucks Only",
    "Green": "15-30 Min Limit",
    "Blue": "Accessible Parking",
}

meter_types = {
    "-": "UNKNOWN",
    "MS": "MOTORCYCLE",
    "SS": "NORMAL"
}