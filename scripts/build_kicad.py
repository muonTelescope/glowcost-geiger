"""Rebuild the native KiCad prototype and review reports; gate PCB exports on DRC."""
from pathlib import Path
import subprocess,json,os,sys
ROOT=Path(__file__).resolve().parents[1]
CLI=os.environ.get('KICAD_CLI','/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli')
PY=os.environ.get('KICAD_PYTHON','/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3')
def run(*args):subprocess.run(args,cwd=ROOT,check=True)
run('npm','run','build')
# Preserve the checked-in routed geometry, rather than rerunning the autorouter.
run('npx','tsci','build','docs/layout/circuit.json','--kicad-project','--disable-parts-engine')
run('bun','-e','import {nodePorts} from "./board/module.circuit"; await Bun.write("build/kicad-node-ports.json", JSON.stringify(nodePorts,null,2))')
run(sys.executable,'scripts/generate_kicad_schematic.py')
run(sys.executable,'scripts/prepare_kicad_pcb.py')
run(sys.executable,'scripts/export_tube_vrml.py')
run(PY,'scripts/finalize_kicad_libraries.py')
fcpy=os.environ.get('FREECAD_PYTHON','/Applications/FreeCAD.app/Contents/Resources/bin/python')
fclib=os.environ.get('FREECAD_LIB','/Applications/FreeCAD.app/Contents/Resources/lib')
subprocess.run([fcpy,'scripts/audit_kicad_models.py'],cwd=ROOT,env={**os.environ,'PYTHONPATH':fclib},check=True)
board='kicad/glowcost-geiger.kicad_pcb';sch='kicad/glowcost-geiger.kicad_sch'
run(CLI,'sch','erc','--format','json','--output','docs/kicad/erc.json',sch)
erc=json.loads((ROOT/'docs/kicad/erc.json').read_text())
if any(v['severity']=='error' for s in erc['sheets'] for v in s['violations']):raise SystemExit('FAILURE: ERC errors; schematic export stopped.')
run(CLI,'sch','export','netlist','--format','kicadxml','--output','docs/kicad/netlist.xml',sch)
run(CLI,'sch','export','svg','--output','docs/kicad',sch)
run(CLI,'sch','export','pdf','--output','docs/kicad/schematic.pdf',sch)
run('rsvg-convert','-w','3000','docs/kicad/glowcost-geiger.svg','-o','docs/kicad/schematic.png')
run(CLI,'pcb','drc','--schematic-parity','--format','json','--output','docs/kicad/drc.json',board)
run(PY,'scripts/check_kicad_conversion.py')
drc=json.loads((ROOT/'docs/kicad/drc.json').read_text())
if any(v['severity']=='error' for key in ['violations','unconnected_items','schematic_parity'] for v in drc[key]):
 raise SystemExit('FAILURE: preserved prototype has DRC errors. Native files and reports are saved; PCB/3D/fabrication exports are blocked.')
run(CLI,'pcb','export','svg','--output','docs/kicad/layers','--layers','F.Cu,B.Cu,F.Silkscreen,B.Silkscreen,Edge.Cuts',board)
run(CLI,'pcb','export','step','--output','docs/kicad/assembly.step','--force',board)
