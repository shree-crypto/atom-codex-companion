"""Orthographic CPU render of actual CAD triangles, with a per-pixel depth buffer."""
import os
from pathlib import Path
import json
import argparse

HERE=Path(__file__).resolve().parent
os.environ.setdefault('MPLCONFIGDIR', str(HERE.parent/'.runtime'/'mpl'))
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def render(name, iteration, single=False, accent='green'):
    meshes=json.loads((HERE/'review'/(('assembled' if name=='front' else name)+'-mesh.json')).read_text(encoding='utf-8'))
    if not any(m['name']=='body' for m in meshes):
        raise RuntimeError('Stationary V1 mesh export is not ready; refusing old motorized model')
    width=height=1400
    pixels=np.full((height,width,3),[244,242,237],dtype=np.uint8)
    depth=np.full((height,width),-np.inf,dtype=np.float32)
    points=[]; triangles_list=[]; colours_list=[]
    light=np.array([-0.5,-0.8,1.4]); light/=np.linalg.norm(light)
    for mesh in meshes:
        vertices=np.asarray(mesh['vertices']); faces=np.asarray(mesh['faces'])
        triangles=vertices[faces]; points.extend(vertices.tolist())
        normal=np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0])
        length=np.linalg.norm(normal,axis=1); normal/=np.maximum(length[:,None],1e-10)
        intensity=0.58+0.42*np.maximum(0,normal@light)
        colour=np.asarray(mesh['colour'])
        if mesh['name']=='bezel':
            colour=np.array([0.91,0.48,0.16]) if accent=='orange' else np.array([0.506,0.78,0.416])
        if single and mesh['name'] in ('body','bezel','keeper'):
            colour=np.array([0.15,0.18,0.20])
        colours=np.clip(colour[None,:]*intensity[:,None]+0.04,0,1)
        triangles_list.append(triangles); colours_list.append(colours)
    triangles=np.concatenate(triangles_list); colours=np.concatenate(colours_list)
    az,el=np.radians([-90,0] if name=='front' else [-58,18])
    toward=np.array([np.cos(el)*np.cos(az),np.cos(el)*np.sin(az),np.sin(el)])
    right=np.array([-np.sin(az),np.cos(az),0]); up=np.cross(toward,right)
    center=(np.asarray(points).min(0)+np.asarray(points).max(0))/2
    relative=triangles-center
    projected=np.stack((relative@right,relative@up,relative@toward),axis=-1)
    xy=projected[:,:,:2]; low=xy.min((0,1)); high=xy.max((0,1)); span=high-low
    scale=min(1120/span[0],900/span[1])
    projected[:,:,0]=(projected[:,:,0]-(low[0]+high[0])/2)*scale+width/2
    projected[:,:,1]=-(projected[:,:,1]-(low[1]+high[1])/2)*scale+760
    for tri, colour in zip(projected,colours):
        x0,y0,z0=tri[0]; x1,y1,z1=tri[1]; x2,y2,z2=tri[2]
        denominator=(y1-y2)*(x0-x2)+(x2-x1)*(y0-y2)
        if abs(denominator)<1e-8: continue
        left=max(0,int(np.floor(tri[:,0].min()))); top=max(0,int(np.floor(tri[:,1].min())))
        right_edge=min(width-1,int(np.ceil(tri[:,0].max()))); bottom=min(height-1,int(np.ceil(tri[:,1].max())))
        if left>right_edge or top>bottom: continue
        yy,xx=np.mgrid[top:bottom+1,left:right_edge+1]; xx=xx+.5; yy=yy+.5
        a=((y1-y2)*(xx-x2)+(x2-x1)*(yy-y2))/denominator
        b=((y2-y0)*(xx-x2)+(x0-x2)*(yy-y2))/denominator; c=1-a-b
        z=a*z0+b*z1+c*z2
        window=depth[top:bottom+1,left:right_edge+1]
        visible=(a>=-1e-6)&(b>=-1e-6)&(c>=-1e-6)&(z>window)
        window[visible]=z[visible]
        pixels[top:bottom+1,left:right_edge+1][visible]=(colour*255).astype(np.uint8)
    picture=Image.fromarray(pixels); draw=ImageDraw.Draw(picture)
    def font(size,bold=False):
        path=Path('C:/Windows/Fonts')/('segoeuib.ttf' if bold else 'segoeui.ttf')
        return ImageFont.truetype(str(path),size) if path.exists() else ImageFont.load_default()
    title={'front':'SCREEN-ONLY OPENING','assembled':'USB-UP CLASSIC FACE','soft':'SOFTER FACE','slim':'SLIMMER BEZEL','exploded':'REPLACE FACE ONLY / REUSE BODY + KEEPER'}[name]
    draw.text((95,70),f'ITERATION {iteration:02d} / {title}',font=font(34,True),fill='#202a31')
    draw.text((95,130),'Single colour' if single else f'Black + {accent} · two separately printable tones',font=font(24),fill='#50616a')
    draw.text((95,1315),'Actual CAD geometry · prototype · physical fit and snap retention unverified',font=font(20),fill='#66737a')
    suffix='-single' if single else '-'+accent
    output=HERE/'review'/f'iteration-{iteration:02d}-{name}{suffix}.png'
    picture.save(output)
    print(output)


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--iteration',type=int,default=1)
    parser.add_argument('--single',action='store_true')
    parser.add_argument('--accent',choices=('green','orange'),default='green')
    parser.add_argument('--design',choices=('assembled','exploded','front'),default='assembled')
    args=parser.parse_args()
    names=(args.design,)
    for name in names: render(name,args.iteration,args.single,args.accent)
