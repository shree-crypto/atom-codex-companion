from pathlib import Path
from stationary import PRINT_PARTS, assembly, exploded, fit_coupons, bezel_soft, bezel_trim

HERE = Path(__file__).resolve().parent

if __name__ == '__main__':
    for directory in ('STEP', 'STL', '3MF', 'review'):
        (HERE/directory).mkdir(exist_ok=True)
    for part in PRINT_PARTS+(bezel_soft,bezel_trim):
        doc = part()
        doc.export(str(HERE/'STEP'/(part.__name__+'.step')))
        doc.export(str(HERE/'STL'/(part.__name__+'.stl')))
        doc.export(str(HERE/'3MF'/(part.__name__+'.3mf')))
    assembly()
    fit_coupons().export(str(HERE/'STL'/'fit_coupons.stl'))
    exploded()
