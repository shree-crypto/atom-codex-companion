"""Export the actual CAD tessellation for CPU image rendering; no invented geometry."""
import json
from pathlib import Path
from stationary import assembly, exploded, soft_face, slim_face
from check_geometry import world_parts

HERE = Path(__file__).resolve().parent
if __name__ == '__main__':
    out=HERE/'review'; out.mkdir(exist_ok=True)
    for name, function in [('assembled', assembly), ('exploded', exploded), ('soft',soft_face),('slim',slim_face)]:
        meshes=[]
        for shape in world_parts(function().shape):
            vertices, faces=shape.tessellate(0.18)
            colour=tuple(shape.color)[:3] if shape.color else (0.2,0.2,0.2)
            meshes.append(dict(name=shape.label, vertices=[list(v) for v in vertices],
                               faces=[list(f) for f in faces], colour=colour))
        (out/(name+'-mesh.json')).write_text(json.dumps(meshes), encoding='utf-8')
        print(name, 'actual CAD meshes:', len(meshes))
