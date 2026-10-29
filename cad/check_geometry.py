"""Measure built solids and reject accidental print-part collisions."""
import json
from pathlib import Path
import build123d as bd
from stationary import PRINT_PARTS, assembly, fit_coupons, soft_face, slim_face


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
    for variant in (assembly,soft_face,slim_face):
        parts=list(world_parts(variant().shape))
        printed=[p for p in parts if p.label in ('body','bezel','keeper')]
        assert len(printed)==3
        assert all(p.is_valid and len(p.solids())==1 for p in printed)
        hardware=[p for p in parts if p.label=='Atom_ENVELOPE_NOT_PRINTED']
        for i,a in enumerate(printed):
            for b in printed[i+1:]+hardware:
                overlap=a.intersect(b)
                volume=sum(s.volume for s in overlap.solids()) if overlap else 0
                if volume>0.05:
                    collisions.append([variant.__name__,a.label,b.label,round(volume,3)])
    assert not collisions, collisions
    assert fit_coupons().shape.is_valid
    result['neutral_print_part_collisions'] = collisions
    result['limitations'] = ['Nominal component sizes; physical fit not verified',
                            'Cable harness and fasteners require physical checks',
                            'V1 is stationary; no motors or motion mechanism']
    out = Path(__file__).parent / 'review' / 'geometry.json'
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
