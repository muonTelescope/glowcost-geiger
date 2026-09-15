import { Fragment } from "react"
import { parts } from "./parts"
/** Review schematic of the simulated CW ladder. Not a fabrication board. */
export const nodePorts: Record<string, string[]> = {
 SW:['.U1 > .SW','.C1 > .pin1'],
 V3V3:['.J1 > .V3V3','.U1 > .V3V3','.U2 > .V3V3','.R_COL > .pin1'],
 EN:['.J1 > .EN','.U1 > .EN','.U2 > .EN','.R_EN > .pin1'],
 TTL:['.J1 > .TTL','.R_OUT > .pin2'],
 DRIVE:['.U2 > .OUT','.R_OUT > .pin1'],
 ANODE_MID:['.R_A1 > .pin2','.R_A2 > .pin1'],
 ANODE:['.R_A2 > .pin2','.GM1 > .A','.J2 > .pin1','.J2 > .pin2'],
 CATHODE:['.J3 > .pin1','.J3 > .pin2','.GM1 > .K','.R_K > .pin1','.R_PROTECT > .pin1'],
 BASE:['.R_PROTECT > .pin2','.Q1 > .B','.D_NEG > .cathode'],
 COLLECTOR:['.Q1 > .C','.R_COL > .pin2','.U2 > .IN'],
 OVP:['.R_OV4 > .pin2','.R_OVBOT > .pin1','.C_OV > .pin1','.U1 > .OVP','.U2 > .OVP'],
 OV1:['.R_OV1 > .pin2','.R_OV2 > .pin1'],
 OV2:['.R_OV2 > .pin2','.R_OV3 > .pin1'],
 OV3:['.R_OV3 > .pin2','.R_OV4 > .pin1'],
 BL1:['.R_BL1 > .pin2','.R_BL2 > .pin1'],
 BL2:['.R_BL2 > .pin2','.R_BL3 > .pin1'],
 BL3:['.R_BL3 > .pin2','.R_BL4 > .pin1'],
 GND:['.Q1 > .E','.D_NEG > .anode','.R_OVBOT > .pin2','.C_OV > .pin2','.R_BL4 > .pin2','.J1 > .GND','.U2 > .GND','.R_EN > .pin2','.R_K > .pin2','.U1 > .GND','.D1 > .anode','.C2 > .pin1','.R5 > .pin2','.C9 > .pin2'],
 P1:['.C1 > .pin2','.D1 > .cathode','.D2 > .anode','.C3 > .pin1'],
 S1:['.D2 > .cathode','.C2 > .pin2','.D3 > .anode','.C4 > .pin1'],
 P2:['.C3 > .pin2','.D3 > .cathode','.D4 > .anode','.C5 > .pin1'],
 S2:['.D4 > .cathode','.C4 > .pin2','.D5 > .anode','.C6 > .pin1'],
 P3:['.C5 > .pin2','.D5 > .cathode','.D6 > .anode','.C7 > .pin1'],
 S3:['.D6 > .cathode','.C6 > .pin2','.D7 > .anode','.C8 > .pin1'],
 P4:['.C7 > .pin2','.D7 > .cathode','.D8 > .anode'],
 S4:['.D8 > .cathode','.C8 > .pin2','.R1 > .pin1','.R_A1 > .pin1','.U2 > .HV_READY','.R_OV1 > .pin1','.R_BL1 > .pin1'],
 DIV1:['.R1 > .pin2','.R2 > .pin1'],
 DIV2:['.R2 > .pin2','.R3 > .pin1'],
 DIV3:['.R3 > .pin2','.R4 > .pin1'],
 SENSE:['.R4 > .pin2','.R5 > .pin1','.C9 > .pin1','.U1 > .FB'],
}

/** All cross-panel connections use electrical net labels; local wires stay local. */
const panelOf = (port: string) => {
  const name = port.split(" > ")[0].slice(1)
  if (["J1", "U1", "R_EN"].includes(name)) return "input"
  if (/^[CD][1-8]$/.test(name)) return "ladder"
  if (/^R[1-5]$/.test(name) || name === "C9") return "feedback"
  if (name.startsWith("R_OV") || name === "C_OV") return "ovp"
  if (name.startsWith("R_BL")) return "bleed"
  return "pulse"
}
const notes = [
  [0, 30, "GLOWCOST GEIGER  |  3.3 V / CTC-5 / FOUR-WIRE PI INTERFACE", 0.85],
  [0, 28, "Functional schematic: U1 and U2 remain behavioral blocks. Not a fabrication release.", 0.5],
  [0, 25, "01  POWER + ENABLE", 0.7],
  [0, 23.5, "J1: JST GH 4-pin SMT latch. 1=3V3, 2=GND, 3=PULSE, 4=EN.", 0.43],
  [0, 13, "U1: L=1 mH, DCR=9.5 ohm; 10 kHz, 20 us ON; peak IL ~59 mA.", 0.43],
  [0, 11.5, "Input bypass in model: 22 uF. EN pulldown: 100k, ~33 uA when high.", 0.43],
  [0, 10, "Main FB = 1.242 V; separate OVP reference inhibits the driver.", 0.43],
  [31, 25, "02  FOUR-STAGE COCKCROFT-WALTON MULTIPLIER", 0.7],
  [31, 23.5, "C1-C8: 10 nF C0G, 630 V, 1206. D1-D8: BAV21W-7-F candidate.", 0.43],
  [31, 13, "SW peak ~106 V nominal; HV ~399 V. Stage labels are electrical nets.", 0.43],
  [31, 11.5, "Diode DC rating 200 V: verify individual reverse stress and hot leakage.", 0.43],
  [0, 7, "03  MAIN HV FEEDBACK", 0.7],
  [0, 5.5, "Four 33M / 2512 / 1% legs share HV stress. Each leg ~100 V / 0.30 mW.", 0.43],
  [0, -3.5, "Vset = 1.242 x (132M + 412k) / 412k = 399.16 V.", 0.46],
  [0, -5, "Divider 3.02 uA at 400 V; C9 time constant ~41 us. Keep sense clean.", 0.43],
  [31, 7, "04  INDEPENDENT OVERVOLTAGE CUTOFF", 0.7],
  [31, 5.5, "Separate divider AND reference; do not share the main-loop reference.", 0.43],
  [31, -3.5, "Vtrip = 1.242 x (132M + 402k) / 402k = 409.06 V.", 0.46],
  [31, -5, "Open-feedback peak 412.67 V; 1% adverse corner 425.29 V (modeled).", 0.43],
  [0, -9, "05  TUBE + CURRENT-LIMITED PULSE INPUT", 0.7],
  [0, -10.5, "R_A1/R_A2: EACH >=500 V working rating; mount close to the anode.", 0.43],
  [0, -25, "4.98M anode limit: <=88.4 uA at 440 V; Q1 emitter returns to GND.", 0.43],
  [0, -26.5, "D_NEG limits reverse VBE. U2: invert + EN / HV-ready / OVP blanking.", 0.43],
  [0, -29.5, "J2/J3: C142864, DNP at JLC; two pads of each clip share one electrode net.", 0.43],
  [0, -28, "Assume tube dead time ~190 us; plan 250 us pending tube/pulse tests.", 0.43],
  [43, -9, "06  PASSIVE HV DISCHARGE", 0.7],
  [43, -10.5, "Four 10M legs: ~100 V / 1 mW each.", 0.43],
  [43, -20, "40M total: 10 uA, 4 mW at 400 V.", 0.43],
  [43, -21.5, "Connected even with EN low / power absent.", 0.43],
  [43, -23, "~158 V remains 100 ms after disable.", 0.43],
  [43, -24.5, "EN LOW IS NOT PROOF OF DISCHARGE.", 0.48],
  [0, -32, "DESIGN NOTES: shared ground, no galvanic isolation. Keep HV physically separated from Pi wiring.", 0.48],
  [0, -33.5, "Plan 10 mA continuous / 20 mA average startup. INPUT INRUSH NOT LIMITED: add soft-start before Pi use.", 0.45],
  [0, -35, "See docs/performance.md for dead-time, conditional dose-rate conversion, power budget and calibration limits.", 0.45],
] as const
export default () => (
  <board routingDisabled schTraceAutoLabelEnabled={true} schMaxTraceDistance={8}>
    {notes.map(([x,y,text,size],i)=><schematictext key={i} text={text} schX={x} schY={y} fontSize={size} anchor="left" color="#16324f" />)}
    <chip {...parts.connector} name="J1" schSectionName={panelOf(".J1 > pin1")} schX={3} schY={18} pinLabels={{pin1:'V3V3',pin2:'GND',pin3:'TTL',pin4:'EN'}} schPinArrangement={{rightSide:['V3V3','GND','TTL','EN']}} />
    <chip name="U1" schSectionName={panelOf(".U1 > pin1")} schX={17} schY={18} pinLabels={{pin1:'SW',pin2:'GND',pin3:'V3V3',pin4:'EN',pin5:'FB',pin6:'OVP'}} schPinArrangement={{leftSide:['V3V3','EN','FB','OVP','GND'],rightSide:['SW']}} />
    <resistor {...parts.r100k} name="R_EN" schSectionName={panelOf(".R_EN > pin1")} resistance="100k" footprint="0603" schX={9} schY={16} schRotation={270} />
    {Array.from({length:4},(_,i)=>{
      const n=i+1, x=34+i*6
      return <Fragment key={n}>
        <capacitor {...parts.ladderCap} name={`C${2*n-1}`} schSectionName={panelOf("." + `C${2*n-1}` + " > pin1")} capacitance="10nF" footprint="1206" schX={x} schY={21} />
        <diode {...parts.ladderDiode} name={`D${2*n-1}`} schSectionName={panelOf("." + `D${2*n-1}` + " > pin1")} footprint="sod123" schX={x-1.5} schY={18.5} schRotation={90} />
        <diode {...parts.ladderDiode} name={`D${2*n}`} schSectionName={panelOf("." + `D${2*n}` + " > pin1")} footprint="sod123" schX={x+1.5} schY={18.5} schRotation={270} />
        <capacitor {...parts.ladderCap} name={`C${2*n}`} schSectionName={panelOf("." + `C${2*n}` + " > pin1")} capacitance="10nF" footprint="1206" schX={x} schY={16} />
      </Fragment>
    })}
    {Array.from({length:4},(_,i)=><Fragment key={`div-${i}`}>
      <resistor {...parts.dividerTop} name={`R${i+1}`} schSectionName={panelOf("." + `R${i+1}` + " > pin1")} resistance="33M" footprint="2512" schX={3+i*5} schY={2} />
      <resistor {...parts.dividerTop} name={`R_OV${i+1}`} schSectionName={panelOf("." + `R_OV${i+1}` + " > pin1")} resistance="33M" footprint="2512" schX={34+i*5} schY={2} />
      <resistor {...parts.bleeder} footprint="1206" name={`R_BL${i+1}`} schSectionName={panelOf("." + `R_BL${i+1}` + " > pin1")} resistance="10M" schX={45+i*3.5} schY={-15} />
    </Fragment>)}
    <resistor {...parts.senseBottom} name="R5" schSectionName={panelOf(".R5 > pin1")} resistance="412k" footprint="0603" schX={23} schY={0} schRotation={270} />
    <capacitor {...parts.senseCap} name="C9" schSectionName={panelOf(".C9 > pin1")} capacitance="100pF" footprint="0603" schX={27} schY={0} schRotation={270} />
    <resistor {...parts.ovpBottom} name="R_OVBOT" schSectionName={panelOf(".R_OVBOT > pin1")} resistance="402k" footprint="0603" schX={54} schY={0} schRotation={270} />
    <capacitor {...parts.ovpCap} name="C_OV" schSectionName={panelOf(".C_OV > pin1")} capacitance="10pF" footprint="0603" schX={58} schY={0} schRotation={270} />
    <resistor {...parts.anode} name="R_A1" schSectionName={panelOf(".R_A1 > pin1")} resistance="2.49M" footprint="1206" schX={3} schY={-14} />
    <resistor {...parts.anode} name="R_A2" schSectionName={panelOf(".R_A2 > pin1")} resistance="2.49M" footprint="1206" schX={8} schY={-14} />
    {['J2','J3'].map((name,i)=><chip {...parts.tubeClip} key={name} name={name} displayName={`${name} DNP`} schSectionName="tube-clips" schX={8+i*14} schY={-23} pinLabels={{pin1:'CONTACT1',pin2:'CONTACT2'}} schPinArrangement={{leftSide:['CONTACT1'],rightSide:['CONTACT2']}} footprint={<footprint>
      <platedhole name="pad1" portHints={['pin1']} pcbX={-3.8} pcbY={0} shape="circle" holeDiameter={2.1} outerDiameter={3.5} />
      <platedhole name="pad2" portHints={['pin2']} pcbX={3.8} pcbY={0} shape="circle" holeDiameter={2.1} outerDiameter={3.5} />
    </footprint>} />)}
    <chip name="GM1" schSectionName={panelOf(".GM1 > pin1")} schX={13} schY={-14} pinLabels={{pin1:'A',pin2:'K'}} schPinArrangement={{leftSide:['A'],rightSide:['K']}} />
    <resistor {...parts.r100k} name="R_K" schSectionName={panelOf(".R_K > pin1")} resistance="100k" footprint="0603" schX={17} schY={-17} schRotation={270} />
    <resistor {...parts.r100k} name="R_PROTECT" schSectionName={panelOf(".R_PROTECT > pin1")} resistance="100k" footprint="0603" schX={21} schY={-14} />
    <chip {...parts.pulseTransistor} footprint="sot23" name="Q1" schSectionName={panelOf(".Q1 > pin1")} schX={26} schY={-14} pinLabels={{pin1:'B',pin2:'E',pin3:'C'}} schPinArrangement={{leftSide:['B'],topSide:['C'],bottomSide:['E']}} />
    <diode {...parts.reverseClamp} footprint="sod123" name="D_NEG" schSectionName={panelOf(".D_NEG > pin1")} schX={22} schY={-19} />
    <resistor {...parts.r47k} name="R_COL" schSectionName={panelOf(".R_COL > pin1")} resistance="47k" footprint="0603" schX={29} schY={-13} schRotation={270} />
    <chip name="U2" schSectionName={panelOf(".U2 > pin1")} schX={32} schY={-19} pinLabels={{pin1:'IN',pin2:'OUT',pin3:'V3V3',pin4:'GND',pin5:'EN',pin6:'HV_READY',pin7:'OVP'}} schPinArrangement={{leftSide:['IN','V3V3','GND','EN','HV_READY','OVP'],rightSide:['OUT']}} />
    <resistor {...parts.r1k} name="R_OUT" schSectionName={panelOf(".R_OUT > pin1")} resistance="1k" footprint="0603" schX={37} schY={-19} />
    {Object.entries(nodePorts).flatMap(([node,ports])=>{
      const groups = Object.groupBy(ports,panelOf)
      if (Object.keys(groups).length === 1) return ports.slice(1).map(port =>
        <trace key={`${node}-${port}`} from={ports[0]} to={port} />)

      const localGroups = Object.values(groups)
      return [

        ...localGroups.flatMap((local)=>[
        <netlabel key={`${node}-${local![0]}`} net={node} connectsTo={[local![0]]} inline />,
        ...local!.slice(1).map((port,i)=><trace key={`${node}-${port}`} from={local![0]} to={port} />),
      ])]
    })}
  </board>
)
