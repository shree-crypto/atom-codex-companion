"""Evaluate the production gesture state machine with the ESP C++ compiler.
The temporary test copy adds only constexpr to enable compile-time evaluation.
"""
import argparse,subprocess,tempfile
from pathlib import Path
root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--compiler',required=True);args=parser.parse_args()
header=(root/'firmware/include/button_gesture.h').read_text()
assert header.count('ButtonAction update(')==1
fixture=r"""
#include "button_gesture.h"
constexpr bool tap(){ButtonGesture b;return b.update(true,true,false,100)==ButtonAction::None&&b.update(false,false,true,250)==ButtonAction::ToggleMute&&b.update(false,false,true,251)==ButtonAction::None;}
constexpr bool hold(){ButtonGesture b;b.update(true,true,false,100);return b.update(false,true,false,1099)==ButtonAction::None&&b.update(false,true,false,1100)==ButtonAction::NextTheme&&b.update(false,true,false,3000)==ButtonAction::None&&b.update(false,false,true,3100)==ButtonAction::None;}
constexpr bool nextTap(){ButtonGesture b;b.update(true,true,false,0);b.update(false,true,false,1000);b.update(false,false,true,1100);b.update(true,true,false,1200);return b.update(false,false,true,1300)==ButtonAction::ToggleMute;}
constexpr bool lateRelease(){ButtonGesture b;b.update(true,true,false,0);return b.update(false,false,true,1001)==ButtonAction::NextTheme;}
constexpr bool wrap(){ButtonGesture b;b.update(true,true,false,0xffffff00u);return b.update(false,true,false,744)==ButtonAction::NextTheme;}
static_assert(tap(),"tap toggles once on release");
static_assert(hold(),"hold changes theme once and never toggles mute");
static_assert(nextTap(),"tap remains usable after a hold");
static_assert(lateRelease(),"long release is still a hold");
static_assert(wrap(),"millis overflow remains correct");
"""
(root/'.runtime').mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(dir=root/'.runtime') as temp:
 d=Path(temp);(d/'button_gesture.h').write_text(header.replace('ButtonAction update(','constexpr ButtonAction update('));(d/'check.cpp').write_text(fixture)
 subprocess.run([args.compiler,'-std=c++17','-c',str(d/'check.cpp'),'-o',str(d/'check.o')],check=True)
print('Five compile-time gesture checks passed: tap, hold, hold-to-tap, late release, clock wrap')
