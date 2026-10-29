"""Round-trip STEP solids, check binary STL closed-edge incidence and 3MF archives."""
from collections import Counter
import json
from pathlib import Path
import struct
import zipfile
import build123d as bd
from stationary import PRINT_PARTS,bezel_soft,bezel_trim

HERE=Path(__file__).resolve().parent


def closed_stl(path):
    data=path.read_bytes(); count=struct.unpack_from('<I',data,80)[0]
    assert len(data)==84+50*count, path
    edges=Counter()
    for i in range(count):
        values=struct.unpack_from('<12fH',data,84+50*i)
        verts=[tuple(round(v,5) for v in values[3+j*3:6+j*3]) for j in range(3)]
        assert len(set(verts))==3, path
        for a,b in zip(verts,verts[1:]+verts[:1]):
            edges[tuple(sorted((a,b)))]+=1
    assert edges and all(n==2 for n in edges.values()), (path,'non-watertight STL')
    return count


if __name__=='__main__':
    report={}
    for function in PRINT_PARTS+(bezel_soft,bezel_trim):
        name=function.__name__
        source=function().shape
        reopened=bd.import_step(str(HERE/'STEP'/(name+'.step')))
        assert reopened.is_valid and len(reopened.solids())==1, name
        assert abs(reopened.volume-source.volume)<0.05, (name,reopened.volume,source.volume)
        triangles=closed_stl(HERE/'STL'/(name+'.stl'))
        with zipfile.ZipFile(HERE/'3MF'/(name+'.3mf')) as archive:
            assert archive.testzip() is None
            assert any(n.endswith('.model') for n in archive.namelist())
        report[name]={'step_round_trip':True,'stl_watertight':True,'triangles':triangles,'3mf_archive_valid':True}
    (HERE/'review'/'exports.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
