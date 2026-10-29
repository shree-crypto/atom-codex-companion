"""Screw-free nominal Atom/SG90 prototype. Units mm; +Z up, front is -Y.

These are prototype dimensions, not measured fits. All printed joints use
snap tabs, slide seats or captive pins. Stock servo horns remain vendor parts.
"""
import json
from pathlib import Path
import build123d as bd
from cadgen import model

HERE = Path(__file__).resolve().parent


def dims():
    return json.loads((HERE / 'dimensions.json').read_text(encoding='utf-8'))


def rounded(w, d, h, r):
    return bd.Pos(0, 0, -h/2) * bd.extrude(bd.RectangleRounded(w, d, r), amount=h)


def front(w, h, depth, radius):
    return bd.Rot(90, 0, 0) * rounded(w, h, depth, radius)


def label(shape, name, colour):
    shape.label = name
    shape.color = colour
    return shape


def x_bore(radius, length, x, y, z):
    return bd.Pos(x, y, z) * bd.Rot(0, 90, 0) * bd.Cylinder(radius, length)


def ramp_x(width=6):
    # A two-mm lead-in; flat underside holds behind the receiving window.
    sketch = bd.Plane.XZ * bd.Polygon((0, 0), (0.8, 0), (0.8, 0.6), (0, 2), align=None)
    return bd.Pos(0, width/2, 0) * bd.extrude(sketch, amount=width)


@model
def base_shell():
    d = dims(); w, dep, h = d['base_width'], d['base_depth'], d['base_height']
    wall = d['shell_wall']
    body = rounded(w, dep, h, 8) - bd.Pos(0, 0, -wall) * rounded(w-2*wall, dep-2*wall, h, 5.6)
    body -= bd.Pos(0, 0, h/2) * bd.Box(12.9, 23.4, 8)
    # Snap-in SG90 seat; the supplied ears rest beneath the ceiling.
    for sign in (-1, 1):
        ear = bd.Pos(0, sign*14, 11) * bd.Box(16, 5, 4)
        body += ear
        body -= bd.Pos(0, sign*13.5, 11.5) * bd.Box(9, 3.2, 3)
        for y in (-16, 16):
            body -= bd.Pos(sign*(w/2-1), y, -3) * bd.Box(5, 8, 4)
    body -= bd.Pos(0, dep/2, -3) * bd.Box(13, 8, 8)
    # Separate low-current piezo vent; no unspecified speaker mounting assumed.
    for x in (-8, -4, 0, 4, 8):
        body -= bd.Pos(x, -dep/2, 0) * bd.Box(1.5, 8, 8)
    body = bd.Pos(0, 0, 17.2) * body
    assert abs(body.bounding_box().size.X - 70) < 0.01
    return label(body, 'base_shell', '#20252a')


@model
def base_lid():
    d = dims(); body = bd.Pos(0, 0, 1) * rounded(70, 60, 2, 8)
    for sign in (-1, 1):
        for y in (-16, 16):
            beam = bd.Pos(sign*31.7, y, 7.8) * bd.Box(1.2, 6, 12)
            hook = bd.Pos(32.3, y, 12.4) * ramp_x(6)
            if sign < 0:
                hook = bd.mirror(hook, about=bd.Plane.YZ)
            body = body + beam + hook
    # Slots accept a reusable hook-and-loop power-module strap.
    for x in (-20, 20):
        body -= bd.Pos(x, 14, 1) * bd.Box(3, 15, 5)
    return label(body, 'base_lid', '#20252a')


@model
def cradle():
    d = dims(); py, pz = d['pivot_y'], d['pivot_height']
    body = bd.Pos(0, 0, 40.2) * bd.Cylinder(24, 4)
    body -= bd.Pos(0, 0, 38.8) * bd.Box(26.6, 8.6, 2)
    # Captive stock pan horn: slide-in entry and snap gate, no printed spline.
    body -= bd.Pos(0, 0, 40) * bd.Cylinder(2, 8)
    body -= bd.Pos(0, -23, 38.8) * bd.Box(8.6, 40, 2)
    for sign in (-1, 1):
        arm = bd.Pos(sign*25, py, 61.7) * bd.Box(4, 20, 39)
        body += arm
        body -= x_bore(1.7, 8, sign*25, py, pz)
    # Horn capture recess at the left stationary cheek, accessed from outside.
    body -= bd.Pos(-26, py, pz) * bd.Box(2, 8.6, 26.6)
    return label(body, 'cradle', '#20252a')


@model
def head_shell():
    d = dims(); py = d['pivot_y']; w = d['head_width']; h = d['head_height']
    body = bd.Pos(0, 1, 76) * front(w, h, 30, 6)
    body -= bd.Pos(0, -1.5, 76) * front(w-4.8, h-4.8, 31, 3.6)
    # Windows release the four long bezel latches with a fingertip/tool.
    for sign in (-1, 1):
        for z in (66, 86):
            body -= bd.Pos(sign*19, -0.7, z) * bd.Box(6, 4.4, 6)
    body -= x_bore(4.2, 8, -20, py, 76)
    body -= x_bore(1.7, 8, 20, py, 76)
    # Tilt servo shelf and two retaining-strap slots; retain with an orange
    # reusable clip/strap only after the real case and horn are checked.
    body += bd.Pos(-3.5, 7.5, 57.2) * bd.Box(31, 15, 2)
    for x in (-12, 7):
        body -= bd.Pos(x, 15, 70) * bd.Box(3, 6, 12)
    # USB cable and reset access are real openings.
    body -= bd.Pos(0, 15, 88) * bd.Box(14, 8, 8)
    return label(body, 'head_shell', '#20252a')


@model
def bezel():
    d = dims(); body = bd.Pos(0, -16.5, 76) * front(40, 40, 3, 6)
    body -= bd.Pos(0, -16.5, 76) * bd.Box(24.6, 8, 24.6)
    for sign in (-1, 1):
        for z in (66, 86):
            beam = bd.Pos(sign*16.7, -7.6, z) * bd.Box(1.2, 15.2, 4)
            # Hook is a ramp rotated so the lead-in faces rearward.
            hook = bd.Pos(17.3, -1.3, z) * bd.Box(0.8, 1.5, 4)
            if sign < 0:
                hook = bd.mirror(hook, about=bd.Plane.YZ)
            body = body + beam + hook
    # Board cage locates the original Atom enclosure, leaving its face accessible.
    cage = bd.Pos(0, -9.7, 76) * front(28.2, 28.2, 13.6, 2)
    cage -= bd.Pos(0, -9.7, 76) * bd.Box(24.6, 18, 24.6)
    body += cage
    body -= bd.Pos(0, -7.5, 90) * bd.Box(14, 8, 5)
    for sign in (-1, 1):
        body -= bd.Pos(sign*12.8, -3.4, 76) * bd.Box(1.4, 3.4, 6.4)
    return label(body, 'bezel', '#81c76a')


@model
def atom_keeper():
    # Rear press-in crossbar. Test foam/preload before inserting the real board.
    body = bd.Pos(0, -2.1, 76) * bd.Box(25, 1.5, 4)
    for sign in (-1, 1):
        body += bd.Pos(sign*12.8, -3, 76) * bd.Box(1, 3, 6)
    return label(body, 'atom_keeper', '#20252a')


@model
def pivot_pin():
    # Captive split pin for the passive right pivot, printed separately.
    body = x_bore(1.45, 11, 22.5, dims()['pivot_y'], 76)
    body += x_bore(3.2, 1.2, 28.2, dims()['pivot_y'], 76)
    body += x_bore(1.95, 1.2, 16.9, dims()['pivot_y'], 76)
    body -= bd.Pos(19, dims()['pivot_y'], 76) * bd.Box(5, 0.7, 5)
    return label(body, 'pivot_pin', '#20252a')


PRINT_PARTS = (base_shell, base_lid, cradle, head_shell, bezel, atom_keeper, pivot_pin)


def hardware():
    # Clearly labelled nonprinting envelope models, not vendor CAD.
    pan = bd.Pos(0, 0, 17) * bd.Box(12.2, 22.7, 27)
    tilt = bd.Pos(-4.5, dims()['pivot_y'], 70) * bd.Box(27, 12.2, 22.7)
    atom = bd.Pos(0, -9.7, 76) * bd.Box(24, 13, 24)
    screen = bd.Pos(0, -16.3, 76) * bd.Box(21.8, 0.2, 21.8)
    eyes = [label(bd.Pos(x, -16.5, 76)*front(4, 8, 0.2, 1.9),
                  'eye_NOT_PRINTED_'+str(i), '#a3f6d5') for i, x in enumerate((-4.5, 4.5))]
    return [label(pan, 'SG90_pan_ENVELOPE', '#487bc7'),
            label(tilt, 'SG90_tilt_ENVELOPE', '#487bc7'),
            label(atom, 'AtomS3_ENVELOPE', '#393d40'),
            label(screen, 'display_NOT_PRINTED', '#101b22')] + eyes


@model
def assembly():
    return bd.Compound(children=[f().shape for f in PRINT_PARTS] + hardware(), label='Atom_snapfit_PROTOTYPE')


@model
def exploded():
    offsets = ((0, 0, 0), (0, 0, -22), (0, 0, 18), (0, 0, 43),
               (0, -38, 43), (0, -25, 43), (20, 0, 43))
    parts = [bd.Pos(*p) * f().shape for f, p in zip(PRINT_PARTS, offsets)]
    return bd.Compound(children=parts, label='Snapfit_parts_exploded_PROTOTYPE')


@model
def fit_coupons():
    d = dims(); parts = []
    for i, clearance in enumerate((0.2, 0.4, 0.6)):
        w = d['servo']['case_width'] + clearance
        length = d['servo']['case_length'] + clearance
        ring = rounded(w+5, length+5, 5, 2) - bd.Box(w, length, 8)
        ring = bd.Pos(i*25, 0, 2.5) * ring
        parts.append(label(ring, 'SG90_total_clearance_'+str(clearance), '#ec8d34'))
    board = rounded(29.4, 29.4, 5, 2) - bd.Box(24.6, 24.6, 8)
    parts.append(label(bd.Pos(25, 37, 2.5)*board, 'Atom_24p6_pocket', '#81c76a'))
    return bd.Compound(children=parts, label='Fit_coupons_PLA_ABS')


if __name__ == '__main__':
    assembly()
    fit_coupons()
    exploded()
