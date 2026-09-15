import { Children, Fragment, cloneElement, isValidElement } from 'react'
import Module, { nodePorts } from './module.circuit'

/** Placement study only. Values, MPNs and exposed nets come from the schematic.
 * U1/U2 are reserved areas until a physical controller exists; GM1 is a body envelope.
 * DNP clips retain PCB holes here. Assembly population comes from parts.ts/review BOM.
 */
export const placement: Record<string, [number, number, number?]> = {
  J1: [-60,-17], J2: [52.5,18,90], J3: [-52.5,18,90],
  R_EN: [-53,-17], R_A1: [47,8], R_A2: [53,8],
  R5: [8,-15,90], C9: [3,-15,90], R_OVBOT: [8,-23,90], C_OV: [3,-23,90],
  R_K: [-53,8,90], R_PROTECT: [-46,9], Q1: [-45,3],
  D_NEG: [-51,2,90], R_COL: [-39,3,90], R_OUT: [-53,-9],
}
for (let i=0;i<4;i++) {
  const x=1+12*i
  placement[`C${2*i+1}`]=[x,1]
  placement[`C${2*i+2}`]=[x,-7]
  placement[`D${2*i+1}`]=[x-3,-3,90]
  placement[`D${2*i+2}`]=[x+3,-3,90]
  placement[`R${i+1}`]=[48-10*i,-15]
  placement[`R_OV${i+1}`]=[48-10*i,-23]
  placement[`R_BL${i+1}`]=[61,3-7*i,90]
}

// JST GH vertical land pattern dimensions from the KiCad library/JST drawing.
const jstFootprint = <footprint>
  {[1,2,3,4].map(n=><smtpad key={n} portHints={[`pin${n}`]} pcbX={(n-2.5)*1.25} pcbY={-1.95} width={0.6} height={1.7} shape="rect" />)}
  {[-1,1].map(side=><smtpad key={side} name={`MP${side}`} pcbX={side*3.725} pcbY={1.4} width={1} height={2.8} shape="rect" />)}
  <courtyardrect pcbX={0} pcbY={0} width={9.44} height={6.6} />
  <silkscreenrect pcbX={0} pcbY={0.375} width={8.25} height={4.25} strokeWidth={0.12} />
</footprint>

function flatten(children: any): any[] {
  return Children.toArray(children).flatMap((child:any)=>
    isValidElement(child) && child.type===Fragment ? flatten(child.props.children) : [child])
}
export default () => {
  const components=flatten(Module().props.children).filter((e:any)=>isValidElement(e) && placement[e.props.name])
  return <board width={140} height={60} thickness={1.6} routingDisabled pcbStyle={{silkscreenFontSize:0.9}}
    outline={[{x:-68,y:-30},{x:68,y:-30},{x:70,y:-28},{x:70,y:28},{x:68,y:30},{x:-68,y:30},{x:-70,y:28},{x:-70,y:-28}]}>
    {components.map((e:any)=>{
      const [pcbX,pcbY,pcbRotation=0]=placement[e.props.name]
      return cloneElement(e,{key:e.props.name,pcbX,pcbY,pcbRotation,doNotPlace:false,
        ...(e.props.name==='J1'?{footprint:jstFootprint}:{}),
        ...(['J2','J3'].includes(e.props.name)?{footprint:cloneElement(e.props.footprint,{},e.props.footprint.props.children,<courtyardrect pcbX={0} pcbY={0} width={12} height={9} />)}:{}),
        pcbStyle:{silkscreenFontSize:0.8}})
    })}
    {Object.entries(nodePorts).flatMap(([net,ports])=>ports
      .filter(port=>placement[port.split(' > ')[0].slice(1)])
      .map(port=><trace key={`${net}-${port}`} from={port} to={`net.${net}`} />))}
    {[-64,64].flatMap(x=>[-24,24].map(y=><hole key={`${x}:${y}`} name={`M_${x}_${y}`} pcbX={x} pcbY={y} diameter={3.2} />))}
    <keepout shape="rect" pcbX={0} pcbY={18} width={96} height={16} layers={["top","bottom"]} />
    <silkscreenrect pcbX={0} pcbY={18} width={110} height={12} stroke="dashed" strokeWidth={0.15} />
    <silkscreentext pcbX={0} pcbY={18} text="CTC-5 / STS-5 BODY ENVELOPE - NO COPPER UNDER TUBE" fontSize={1.2} />
    <silkscreentext pcbX={0} pcbY={27} text="PLACEMENT STUDY / UNROUTED / 140 x 60 mm" fontSize={1.2} />
    <silkscreentext pcbX={-52.5} pcbY={25} text="J3 CATHODE - DNP" fontSize={0.9} />
    <silkscreentext pcbX={52.5} pcbY={25} text="J2 ANODE - DNP" fontSize={0.9} />
    <silkscreenrect pcbX={-22} pcbY={-11} width={30} height={26} stroke="dashed" strokeWidth={0.15} />
    <silkscreentext pcbX={-22} pcbY={-7} text="U1/U2 RESERVED" fontSize={1.2} />
    <silkscreentext pcbX={-22} pcbY={-11} text="CONTROLLER + SOFT START" fontSize={0.85} />
    <silkscreentext pcbX={-22} pcbY={-15} text="PHYSICAL CIRCUIT PENDING" fontSize={0.85} />
    <silkscreentext pcbX={-60} pcbY={-11} text="3V3 GND PULSE EN" fontSize={0.8} />
    <silkscreentext pcbX={20} pcbY={6} text="MULTIPLIER - HV" fontSize={1} />
    <silkscreentext pcbX={34} pcbY={-11} text="MAIN FEEDBACK" fontSize={0.8} />
    <silkscreentext pcbX={34} pcbY={-19} text="INDEPENDENT OVP" fontSize={0.8} />
    <silkscreentext pcbX={0} pcbY={-28} text="NOT FOR FABRICATION - DNP CLIP PADS RETAINED - NO ROUTES OR PLANES" fontSize={1} />
  </board>
}
