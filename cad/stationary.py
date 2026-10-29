"""V1 stationary snapfit enclosure. No motors, servo cavities, pins or screw joints."""
import build123d as bd
from cadgen import model


def rounded(w,d,h,r):
    return bd.Pos(0,0,-h/2)*bd.extrude(bd.RectangleRounded(w,d,r),amount=h)


def front(w,h,d,r):
    return bd.Rot(90,0,0)*rounded(w,h,d,r)


def named(part,name,colour):
    part.label=name; part.color=colour; return part


@model
def body():
    shell=bd.Pos(0,1,25)*front(40,38,28,6)
    shell-=bd.Pos(0,-2.2,25)*front(35.2,33.2,29.6,3.6)
    foot=bd.Pos(0,1,3)*rounded(48,38,6,8)
    shell+=foot
    for side in (-1,1):
        for z in (16,34):
            shell-=bd.Pos(side*19,0.3,z)*bd.Box(6,4.4,6)
    shell-=bd.Pos(0,-6.5,42)*bd.Box(14,12,12)
    # Speaker grille leaves room for the user's integrated speaker; exact opening
    # alignment remains a fit check for the board's actual variant.
    for x in (-6,-3,0,3,6):
        shell-=bd.Pos(x,14,25)*bd.Box(1.2,6,10)
    assert shell.is_valid and len(shell.solids())==1
    return named(shell,'body','#252b30')


def bezel_shape(width=40,height=38,radius=6):
    part=bd.Pos(0,-14.5,25)*front(width,height,3,radius)
    part-=bd.Pos(0,-14.5,26)*bd.Box(24.6,8,24.6)
    for side in (-1,1):
        for z in (16,34):
            part+=bd.Pos(side*16.7,-5.9,z)*bd.Box(1.2,14.6,4)
            part+=bd.Pos(side*17.7,-0.1,z)*bd.Box(0.8,1.5,4)
    cage=bd.Pos(0,-8,26)*front(28.2,28.2,13.6,2)
    cage-=bd.Pos(0,-8,26)*bd.Box(24.6,18,24.6)
    part+=cage
    part-=bd.Pos(0,-6.5,39.5)*bd.Box(14,12,5)
    for side in (-1,1):
        part-=bd.Pos(side*12.8,-1.6,26)*bd.Box(1.4,3.4,6.4)
    return named(part,'bezel','#e87a29')


@model
def bezel():
    return bezel_shape()


@model
def bezel_soft():
    return bezel_shape(40,38,9)


@model
def bezel_trim():
    return bezel_shape(38,36,5)


@model
def keeper():
    part=bd.Pos(0,-0.4,26)*bd.Box(25,1.5,4)
    for side in (-1,1):
        part+=bd.Pos(side*12.8,-1.3,26)*bd.Box(1,3,6)
    return named(part,'keeper','#252b30')


PRINT_PARTS=(body,bezel,keeper)


def hardware():
    atom=bd.Pos(0,-8,26)*bd.Box(24,13,24)
    screen=bd.Pos(0,-14.65,26)*bd.Box(21.8,0.2,21.8)
    parts=[named(atom,'Atom_ENVELOPE_NOT_PRINTED','#30383d'),named(screen,'screen_NOT_PRINTED','#101b22')]
    for i,x in enumerate((-4.5,4.5)):
        parts.append(named(bd.Pos(x,-14.8,26)*front(4,8,0.15,1.9),'eye_NOT_PRINTED_'+str(i),'#a3f6d5'))
    return parts


@model
def assembly():
    return bd.Compound(children=[f().shape for f in PRINT_PARTS]+hardware(),label='V1_stationary_snapfit_PROTOTYPE')


@model
def soft_face():
    return bd.Compound(children=[body().shape,bezel_soft().shape,keeper().shape]+hardware(),label='V1_soft_face_PROTOTYPE')


@model
def slim_face():
    return bd.Compound(children=[body().shape,bezel_trim().shape,keeper().shape]+hardware(),label='V1_slim_face_PROTOTYPE')


@model
def exploded():
    parts=[body().shape,bd.Pos(0,-35,0)*bezel().shape,bd.Pos(0,18,0)*keeper().shape]
    return bd.Compound(children=parts,label='V1_three_printed_parts')


@model
def fit_coupons():
    parts=[]
    for i,gap in enumerate((0.2,0.4,0.6)):
        ring=rounded(29,29,4,2)-bd.Box(24+gap,24+gap,8)
        parts.append(named(bd.Pos(i*33,0,2)*ring,'Atom_total_clearance_'+str(gap),'#252b30'))
    return bd.Compound(children=parts,label='V1_fit_coupons_PLA_ABS')


if __name__=='__main__':
    assembly(); exploded(); fit_coupons()
