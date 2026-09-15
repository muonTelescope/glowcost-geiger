import { Fragment } from "react"
import { parts } from "./parts"
/** Review schematic of the simulated CW ladder. Not a fabrication board. */
const nodePorts: Record<string, string[]> = {
 SW:['.U1 > .SW','.C1 > .pin1'],
 V3V3:['.J1 > .V3V3','.U1 > .V3V3','.U2 > .V3V3','.R_COL > .pin1'],
 EN:['.J1 > .EN','.U1 > .EN','.U2 > .EN','.R_EN > .pin1'],
 TTL:['.J1 > .TTL','.R_OUT > .pin2'],
 DRIVE:['.U2 > .OUT','.R_OUT > .pin1'],
 ANODE_MID:['.R_A1 > .pin2','.R_A2 > .pin1'],
 ANODE:['.R_A2 > .pin2','.GM1 > .A'],
 CATHODE:['.GM1 > .K','.R_K > .pin1','.R_PROTECT > .pin1'],
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
export default () => (
  <board routingDisabled schTraceAutoLabelEnabled={false}>
    <chip name="J1" schX={-13} schY={0}
      pinLabels={{pin1:'V3V3',pin2:'GND',pin3:'TTL',pin4:'EN'}}
      schPinArrangement={{rightSide:['V3V3','GND','TTL','EN']}} />
    <chip name="U1" schX={-6} schY={2}
      pinLabels={{pin1:'SW',pin2:'GND',pin3:'V3V3',pin4:'EN',pin5:'FB',pin6:'OVP'}}
      schPinArrangement={{leftSide:['V3V3','EN','FB','OVP','GND'],rightSide:['SW']}} />
    <resistor name="R_EN" resistance="100k" schX={-12} schY={-5} />
    <resistor name="R_A1" resistance="2.49M" schX={25} schY={2} />
    <resistor name="R_A2" resistance="2.49M" schX={30} schY={2} />
    <chip name="GM1" schX={35} schY={2} pinLabels={{pin1:'A',pin2:'K'}}
      schPinArrangement={{leftSide:['A'],rightSide:['K']}} />
    <resistor name="R_K" resistance="100k" schX={40} schY={-1} schRotation={270} />
    <resistor name="R_PROTECT" resistance="100k" schX={35} schY={-5} />
    <chip name="U2" schX={29} schY={-9}
      pinLabels={{pin1:'IN',pin2:'OUT',pin3:'V3V3',pin4:'GND',pin5:'EN',pin6:'HV_READY',pin7:'OVP'}}
      schPinArrangement={{leftSide:['IN','V3V3','GND','EN','HV_READY','OVP'],rightSide:['OUT']}} />
    <resistor name="R_OUT" resistance="1k" schX={35} schY={-9} />
    <schematictext text="J1: ONLY EXTERNAL INTERFACE" schX={-11} schY={5} fontSize={0.25} />
    <schematictext text="U1: BEHAVIORAL HV DRIVER (1mH / 9.5 ohm / 10kHz / 20us)" schX={0} schY={9} fontSize={0.25} />
    <schematictext text="GM1: CTC-5 / STS-5" schX={35} schY={5} fontSize={0.3} />
    <schematictext text="U2: 3.3V CONDITIONING + ENABLE/HV/OVP BLANKING, BEHAVIORAL" schX={28} schY={-30} fontSize={0.25} />
    <chip {...parts.pulseTransistor} footprint="sot23" name="Q1" schX={40} schY={-9} pinLabels={{pin1:'B',pin2:'E',pin3:'C'}} />
    <diode name="D_NEG" schX={45} schY={-7} />
    <resistor name="R_COL" resistance="47k" schX={45} schY={-11} />
    {Array.from({length:4},(_,i)=><Fragment key={`protect-${i}`}>
      <resistor name={`R_OV${i+1}`} resistance="33M" schX={i*5} schY={-17} />
      <resistor name={`R_BL${i+1}`} resistance="10M" schX={i*5} schY={-24} />
    </Fragment>)}
    <resistor name="R_OVBOT" resistance="402k" schX={20} schY={-17} />
    <capacitor name="C_OV" capacitance="10pF" schX={24} schY={-20} />
    <schematictext text="INDEPENDENT OVP DIVIDER / 409.0 V NOMINAL TRIP" schX={10} schY={-14} fontSize={0.3} />
    <schematictext text="40 MOhm PASSIVE BLEEDER / PRESENT WHEN DISABLED" schX={10} schY={-27} fontSize={0.3} />
    {Array.from({length:4},(_,i)=>{
      const n=i+1, x=i*6
      return <Fragment key={n}>
        <capacitor {...parts.ladderCap} name={`C${2*n-1}`} capacitance="10nF" footprint="1206" schX={x} schY={4} />
        <diode {...parts.ladderDiode} name={`D${2*n-1}`} footprint="sod123" schX={x-1.5} schY={2} schRotation={90} />
        <diode {...parts.ladderDiode} name={`D${2*n}`} footprint="sod123" schX={x+1.5} schY={2} schRotation={270} />
        <capacitor {...parts.ladderCap} name={`C${2*n}`} capacitance="10nF" footprint="1206" schX={x} schY={0} />
      </Fragment>
    })}

    <resistor name="R1" resistance="33M" footprint="1206" schX={3} schY={-5} />
    <resistor name="R2" resistance="33M" footprint="1206" schX={7} schY={-5} />
    <resistor name="R3" resistance="33M" footprint="1206" schX={11} schY={-5} />
    <resistor name="R4" resistance="33M" footprint="1206" schX={15} schY={-5} />
    <resistor name="R5" resistance="412k" footprint="0603" schX={18} schY={-7} schRotation={270} />
    <capacitor name="C9" capacitance="100pF" footprint="0603" schX={22} schY={-7} schRotation={270} />
    {Object.entries(nodePorts).flatMap(([node,ports])=>ports.slice(1).map((port,i)=>(
      <trace key={`${node}-${i}`} from={ports[0]} to={port} schDisplayLabel={node} />
    )))}
    <schematictext text="FOUR-STAGE CW / EIGHT DIODES / EIGHT 10 nF CAPACITORS" schX={9} schY={6} fontSize={0.32} />
    <schematictext text="FUNCTIONAL SCHEMATIC ONLY - U1/U2 ARE NOT ORDERABLE PARTS" schX={9} schY={-11} fontSize={0.28} />
  </board>
)
