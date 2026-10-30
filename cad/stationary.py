"""Bezel-only revision 2: fits the original printed body and keeper unchanged."""
import build123d as bd
from cadgen import model

STACK_DEPTH=12.9+14.14
EXTRA_DEPTH=STACK_DEPTH-13.0
SHELL_EXTENSION=4.0
FRONT_CLEARANCE=1.8
POCKET=24.2  # User confirmed the 24.2 mm coupon fits best.
WINDOW=15.8  # Nominal 0.85-inch square display plus a small visual margin.

def rounded(w,d,h,r):
    return bd.Pos(0,0,-h/2)*bd.extrude(bd.RectangleRounded(w,d,r),amount=h)

def front(w,h,d,r):
    return bd.Rot(90,0,0)*rounded(w,h,d,r)

def named(part,name,colour):
    part.label=name; part.color=colour; return part

@model
def body():
    shell=bd.Pos(0,1+SHELL_EXTENSION/2,25)*front(40,38,28+SHELL_EXTENSION,6)
    shell-=bd.Pos(0,-2.2+SHELL_EXTENSION/2,25)*front(35.2,33.2,29.6+SHELL_EXTENSION,3.6)
    foot=bd.Pos(0,1+SHELL_EXTENSION/2,3)*rounded(48,38+SHELL_EXTENSION,6,8)
    shell+=foot
    for side in (-1,1):
        for z in (16,34):
            shell-=bd.Pos(side*19,0.3,z)*bd.Box(6,4.4,6)
    shell-=bd.Pos(0,-6.5,42)*bd.Box(14,12,12)
    # Rear grille and side vents give the Echo Base an open acoustic path.
    # Exact speaker/microphone port alignment still requires a physical fit check.
    for x in (-6,-3,0,3,6):
        shell-=bd.Pos(x,14+SHELL_EXTENSION,25)*bd.Box(1.2,6,10)
    for side in (-1,1):
        shell-=bd.Pos(side*19,7,26)*bd.Box(6,8,4)
    assert shell.is_valid and len(shell.solids())==1
    return named(shell,'body','#252b30')

def bezel_shape():
    part=bd.Pos(0,-14.5,25)*front(40,38,3,6)
    part-=bd.Pos(0,-14.5,26)*front(WINDOW,WINDOW,8,.5)
    # Match all FOUR original body windows, centred at z=16 and z=34.
    # Reinforced roots overlap the face by 1 mm (old roots overlapped by 0.2 mm).
    for side in (-1,1):
        for z in (16,34):
            beam=bd.Pos(side*16.7,-6,z)*bd.Box(1.4,16,4.8)
            root=bd.extrude(bd.Polygon((14.4,-14),(17.4,-14),(17.4,-9.8),(16,-9.8),align=None),amount=4.8)
            hook=bd.extrude(bd.Polygon((17.4,-.8),(17.95,-.8),(17.95,-.2),(17.4,1.8),align=None),amount=4.8)
            if side<0:
                root=bd.mirror(root,about=bd.Plane.YZ)
                hook=bd.mirror(hook,about=bd.Plane.YZ)
            part+=beam+bd.Pos(0,0,z-2.4)*root+bd.Pos(0,0,z-2.4)*hook
    # Retain the original bezel-mounted cage and keeper sockets.
    cage=bd.Pos(0,-8+(EXTRA_DEPTH+FRONT_CLEARANCE)/2,26)*front(28.2,28.2,13.6+EXTRA_DEPTH+FRONT_CLEARANCE,2)
    cage-=bd.Pos(0,-8+(EXTRA_DEPTH+FRONT_CLEARANCE)/2,26)*bd.Box(POCKET,18+EXTRA_DEPTH+FRONT_CLEARANCE,POCKET)
    part+=cage
    part-=bd.Pos(0,-6.5,39.5)*bd.Box(14,12,5)
    for side in (-1,1):
        part-=bd.Pos(side*12.8,-1.6+EXTRA_DEPTH+FRONT_CLEARANCE,21)*bd.Box(1.4,3.4,16.4)
    assert part.is_valid and len(part.solids())==1
    return named(part,'bezel','#e87a29')

@model
def bezel():
    return bezel_shape()

@model
def keeper():
    # Keep the centre of the base clear for its speaker instead of crossing it.
    part=bd.Pos(0,-0.4+EXTRA_DEPTH+FRONT_CLEARANCE,16)*bd.Box(25,1.5,4)
    for side in (-1,1):
        part+=bd.Pos(side*12.8,-1.3+EXTRA_DEPTH+FRONT_CLEARANCE,21)*bd.Box(1,3,14)
    return named(part,'keeper','#252b30')

PRINT_PARTS=(body,bezel,keeper)


def hardware():
    face=-14.5+FRONT_CLEARANCE
    atom=bd.Pos(0,-8+EXTRA_DEPTH/2+FRONT_CLEARANCE,26)*bd.Box(24,STACK_DEPTH,24)
    housing=bd.Pos(0,face+.04,26)*bd.Box(22,.16,22)
    screen=bd.Pos(0,face-.02,26)*front(15.27,15.27,.08,.2)
    parts=[named(atom,'Atom_ENVELOPE_NOT_PRINTED','#30383d'),named(housing,'front_housing_NOT_PRINTED','#deded6'),named(screen,'screen_NOT_PRINTED','#101b22'),named(bd.Pos(0,-7.5,42)*bd.Box(11,7,8),'USB_TOP_NOT_PRINTED','#b8b9b1')]
    for i,x in enumerate((-3.1,3.1)):
        parts.append(named(bd.Pos(x,face-.09,26)*front(2.5,4,.06,1.1),'eye_NOT_PRINTED_'+str(i),'#ed8b35'))
    return parts

@model
def assembly():
    return bd.Compound(children=[f().shape for f in PRINT_PARTS]+hardware(),label='BEZEL_ONLY_REV2_ORIGINAL_BODY_AND_KEEPER')

@model
def exploded():
    return bd.Compound(children=[bd.Pos(0,50,0)*body().shape,bd.Pos(0,-35,0)*bezel().shape,bd.Pos(0,12,0)*keeper().shape]+hardware(),label='REPRINT_ORANGE_BEZEL_ONLY_REUSE_BLACK_PARTS')

@model
def fit_coupons():
    parts=[]
    for i,gap in enumerate((0.2,0.4,0.6)):
        ring=rounded(29,29,4,2)-bd.Box(24+gap,24+gap,8)
        parts.append(named(bd.Pos(i*33,0,2)*ring,'Atom_total_clearance_'+str(gap),'#252b30'))
    return bd.Compound(children=parts,label='V1_fit_coupons_PLA_ABS')

@model
def bezel_print():
    # Side down: beam length lies in the layer plane. Supports are required.
    return bd.Pos(0,0,20)*bd.Rot(0,90,0)*bezel().shape

if __name__=='__main__':
    assembly();exploded();bezel_print()
