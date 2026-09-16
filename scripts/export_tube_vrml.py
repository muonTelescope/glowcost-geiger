"""Convert the recovered, user-matched tube STL to portable KiCad VRML."""
from pathlib import Path
import struct,json
root=Path(__file__).resolve().parents[1];data=(root/'cad/models/tube.stl').read_bytes()
count=struct.unpack_from('<I',data,80)[0];assert len(data)==84+50*count
verts=[];faces=[];lookup={}
for i in range(count):
 tri=struct.unpack_from('<12fH',data,84+50*i)[3:12];idx=[]
 for j in range(0,9,3):
  v=tuple(round(c/2.54,7) for c in tri[j:j+3])
  if v not in lookup:lookup[v]=len(verts);verts.append(v)
  idx.append(lookup[v])
 faces.append(idx)
out=root/'kicad/models/tube.wrl'
out.write_text('#VRML V2.0 utf8\n# Derived from recovered tube.stl; KiCad uses 2.54 mm per VRML unit.\nShape { appearance Appearance { material Material { diffuseColor 0.65 0.49 0.23 specularColor 0.7 0.7 0.7 shininess 0.65 } } geometry IndexedFaceSet { solid FALSE coord Coordinate { point [\n'+',\n'.join(' '.join(map(str,v)) for v in verts)+'\n] } coordIndex [\n'+',\n'.join(' '.join(map(str,f))+ ' -1' for f in faces)+'\n] } }\n')
print(count,'tube triangles exported')
