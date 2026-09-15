"""Export readable full and detail views of the tscircuit SVG, without editing wires."""
from pathlib import Path
import re, subprocess, xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[1]; src=R/'dist/board/module/schematic.svg'
ET.register_namespace('','http://www.w3.org/2000/svg')
root=ET.fromstring(src.read_text());a,b,c,d,tx,ty=map(float,re.search(r'matrix\(([^)]+)\)',root.attrib['data-real-to-screen-transform'])[1].split(','))
views={'schematic':(-2,-37,108,32),'schematic-test':(68,-29,108,29),'schematic-power':(-2,9,63,27),'schematic-feedback':(-2,-7,63,9),'schematic-pulse':(-2,-30,41,-8),'schematic-discharge':(41,-27,63,-8)}
for name,(x0,y0,x1,y1) in views.items():
    out=ET.fromstring(ET.tostring(root));left=a*x0+tx;top=d*y1+ty;w=a*(x1-x0);h=-d*(y1-y0)
    canvas=out.find('{http://www.w3.org/2000/svg}rect')
    assert canvas is not None and canvas.get('class')=='boundary'
    canvas.set('x',str(left));canvas.set('y',str(top));canvas.set('width',str(w));canvas.set('height',str(h))
    out.set('viewBox',f'{left} {top} {w} {h}');out.set('width','1800');out.set('height',str(round(1800*h/w)))
    # White canvas for printing, original circuit artwork is retained.
    out.set('style','background-color: rgb(245, 241, 237)')
    path=R/f'docs/{name}.svg';path.write_text('\n'.join(l.rstrip() for l in ET.tostring(out,encoding='unicode').splitlines())+'\n')
    subprocess.run(['rsvg-convert','-w','2400',str(path),'-o',str(R/f'docs/{name}.png')],check=True)
print('Rendered full schematic and five readable detail views')
