#!/usr/bin/env python3
"""Export cad/models/tube.stl to pcb/models/tube.step via FreeCADCmd.

Run:
  /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd scripts/export_tube_step.py
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STL = ROOT / "cad/models/tube.stl"
OUT = ROOT / "pcb/models/tube.step"

import FreeCAD as App
import Mesh
import Part

doc = App.newDocument("tube_export")
mesh = Mesh.Mesh(str(STL))
shape = Part.Shape()
shape.makeShapeFromMesh(mesh.Topology, 0.1)
shape = shape.removeSplitter()
if shape.Solids:
    body = shape.Solids[0] if len(shape.Solids) == 1 else Part.Compound(shape.Solids)
elif shape.Shells:
    body = shape.Shells[0] if len(shape.Shells) == 1 else Part.Compound(shape.Shells)
else:
    body = shape
obj = doc.addObject("Part::Feature", "Tube")
obj.Shape = body
doc.recompute()
OUT.parent.mkdir(parents=True, exist_ok=True)
Part.export([obj], str(OUT))
bb = obj.Shape.BoundBox
print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")
print(f"bbox_mm X={bb.XLength:.3f} Y={bb.YLength:.3f} Z={bb.ZLength:.3f}")
App.closeDocument(doc.Name)
