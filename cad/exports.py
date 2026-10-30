"""Export the replacement bezel only; preserve the user's original body/keeper files."""
from pathlib import Path
from stationary import bezel,bezel_print,assembly,exploded
HERE=Path(__file__).resolve().parent
if __name__=='__main__':
    for directory in ('STEP','STL','3MF','review'):(HERE/directory).mkdir(exist_ok=True)
    for part in (bezel,bezel_print):
        doc=part()
        for kind in ('STEP','STL','3MF'):doc.export(str(HERE/kind/(part.__name__+'.'+kind.lower())))
    assembly();exploded()
