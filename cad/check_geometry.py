"""Measure built solids and reject accidental print-part collisions."""
import json
from pathlib import Path
import build123d as bd
from stationary import PRINT_PARTS, assembly, fit_coupons, POCKET, WINDOW


def world_parts(node, parent=None):
    here = (bd.Location() if parent is None else parent) * node.location
    if node.children:
        for child in node.children:
            yield from world_parts(child, here)
    else:
        yield node.located(here)


def main():
    result = {}
    for model in PRINT_PARTS:
        shape = model().shape
        assert shape.is_valid, model.__name__
        assert len(shape.solids()) == 1, (model.__name__, len(shape.solids()))
        assert shape.volume > 10, (model.__name__, shape.volume)
        result[model.__name__] = dict(volume_mm3=round(shape.volume, 2),
            bounds_mm=[round(v, 3) for v in shape.bounding_box().size])
    collisions = []
    for variant in (assembly,):
        parts=list(world_parts(variant().shape))
        printed=[p for p in parts if p.label in ('body','bezel','keeper')]
        assert len(printed)==3
        assert all(p.is_valid and len(p.solids())==1 for p in printed)
        hardware=[p for p in parts if p.label in ('Atom_ENVELOPE_NOT_PRINTED','USB_TOP_NOT_PRINTED')]
        for i,a in enumerate(printed):
            for b in printed[i+1:]+hardware:
                overlap=a.intersect(b)
                volume=sum(s.volume for s in overlap.solids()) if overlap else 0
                if volume>0.05:
                    collisions.append([variant.__name__,a.label,b.label,round(volume,3)])
    assert not collisions, collisions
    assert fit_coupons().shape.is_valid
    shell=PRINT_PARTS[1]().shape
    face=shell
    def overlap_volume(a,b):
        common=a.intersect(b)
        return sum(s.volume for s in common.solids()) if common else 0
    # Measured probes, not simply assertions on dimension constants.
    gauge=bd.Pos(0,0,26)*bd.Box(24.2,20,24)
    tight=bd.Pos(0,0,26)*bd.Box(24.4,20,24)
    assert overlap_volume(shell,gauge)<.001
    assert overlap_volume(shell,tight)>1
    aperture=bd.Pos(0,-14.5,26)*bd.Box(15.8,1,14.8)
    oversized=bd.Pos(0,-14.5,26)*bd.Box(16.0,1,14.8)
    assert overlap_volume(face,aperture)<.001
    assert overlap_volume(face,oversized)>1
    result['measured_probe_checks']={'24.2_gauge_clears':True,'24.4_gauge_rejected':True,'15.8_window_clears':True,'16.0_window_rejected':True}
    result['pocket_mm']=POCKET
    result['screen_window_mm']=WINDOW
    result['neutral_print_part_collisions'] = collisions
    result['limitations'] = ['Nominal component sizes; physical fit not verified',
                            'USB clearance, acoustic openings and snap forces require physical checks',
                            'V1 is stationary; no motors or motion mechanism']
    out = Path(__file__).parent / 'review' / 'geometry.json'
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
