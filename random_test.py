#!/usr/bin/env python
# coding=utf-8

import sys
import re
import simplekml
import argparse
import random


def split_lines(wkt):
    return re.findall(r"LINESTRING\(([^)]*)", wkt)


def random_color():
    r = lambda: random.randint(0, 255)
    r()
    return '#FF{:02X}{:02X}{:02X}'.format(r(), r(), r())


def create_lines(lines, colors):
    kml = simplekml.Kml()
    for idx, l in enumerate(lines):
        splitted = re.findall(r"[^ ,]+", l)
        spl = [float(i) for i in splitted]
        coords = zip(splitted[::2], splitted[1::2])

        ls = kml.newlinestring(name='Line ' + str(idx))
        ls.coords = coords

        if colors:
            ls.style.linestyle.color = random_color()
            ls.style.linestyle.width = 4

    return kml


# Argument Parser
parser = argparse.ArgumentParser(description='Converter of WKT\'s linestrings to KML')
parser.add_argument('infile', nargs='?', type=argparse.FileType('r'), default=sys.stdin)
parser.add_argument('outfile', nargs='?', type=argparse.FileType('w'), default=sys.stdout)
parser.add_argument('-c', '--colors', action='store_true', help='add random colors to the lines for easy differentiation')

args = parser.parse_args()

wkt = args.infile.read()

lines = split_lines(wkt)

kml = create_lines(lines, args.colors)
args.outfile.write(kml.kml())
