/** Review inventory only. A functional schematic is not a production BOM. */
import { parts } from '../board/parts'
import { writeFileSync, readFileSync } from 'node:fs'
const rows = JSON.parse(readFileSync('dist/board/module/circuit.json', 'utf8'))
const byMpn = new Map(Object.values(parts).map(p => [p.manufacturerPartNumber, p]))
const quote = (x: unknown) => '"' + String(x ?? '').replaceAll('"', '""') + '"'
const out = [['Reference','MPN','LCSC','DNP','Status']]
for (const c of rows.filter((r: any) => r.type === 'source_component')) {
  const p = byMpn.get(c.manufacturer_part_number)
  if (!['U1','U2','GM1'].includes(c.name) && !p) throw new Error(`${c.name}: no selected part`)
  const dnp = p && 'doNotPlace' in p && p.doNotPlace
  const status = ['U1','U2'].includes(c.name) ? 'BEHAVIORAL; NOT ORDERABLE' : c.name === 'GM1' ? 'OWNED TUBE; SIMULATION REPRESENTATION' : dnp ? 'DNP AT JLC' : !c.supplier_part_numbers?.jlcpcb ? 'EXTERNAL SOURCING; QUOTE REQUIRED' : 'SELECTED; QUALIFICATION PENDING'
  out.push([c.name,c.manufacturer_part_number ?? '',c.supplier_part_numbers?.jlcpcb?.[0] ?? '',dnp ? 'Yes' : 'No',status])
}
for (const ref of ['J2','J3']) {
  const r = out.find(r => r[0] === ref)
  if (!r || r[2] !== 'C142864' || r[3] !== 'Yes') throw new Error(`${ref}: missing DNP clip`)
}
writeFileSync('docs/review-bom.csv',out.map(r => r.map(quote).join(',')).join('\n')+'\n')
console.log('Review BOM generated; J2/J3 are C142864, DNP. Not a production BOM.')
