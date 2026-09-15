import { Children, Fragment, cloneElement, isValidElement } from 'react'
import { testpoints } from './testpoints'
import Module, { nodePorts } from './module.circuit'

/** Routing study only; analog control remains incomplete. Values, MPNs and exposed nets come from the schematic.
 * U1/U2 are reserved areas until a physical controller exists; GM1 is a body envelope.
 * DNP clips retain PCB holes here. Assembly population comes from parts.ts/review BOM.
 */
export const placement: Record<string, [number, number, number?]> = {
  SJ_LED: [-47,16], D_LED: [-53,9,90], R_LED: [-51,14,90],
  Q_LED: [-31,15], R_LB: [-27,15,90], R_LPD: [-23,15,90],
  J1: [-43,-13], J2: [52.5,0,0], J3: [-52.5,0,0],
  R_EN: [-36,-13], R_A1: [45,10], R_A2: [51,10],
  R5: [-8,-15,90], C9: [-12,-15,90], R_OVBOT: [-8,15,90], C_OV: [-12,15,90],
  R_K: [-44,0,90], R_PROTECT: [-43,6], Q1: [-38,6],
  D_NEG: [-44,-5], R_COL: [-38,0,90], R_OUT: [-38,-6],
}
for (let i=0;i<4;i++) {
  const x=-8+12*i
  placement[`C${2*i+1}`]=[x,4]
  placement[`C${2*i+2}`]=[x,-4]
  placement[`D${2*i+1}`]=[x-3,0,90]
  placement[`D${2*i+2}`]=[x+3,0,90]
  placement[`R${i+1}`]=[28-12*i,-10]
  placement[`R_OV${i+1}`]=[28-12*i,10]
  placement[`R_BL${i+1}`]=[40,12-8*i,90]
}

for (const [ref,,x,y] of testpoints) placement[ref]=[x,y]

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
  return <board width={120} height={40} thickness={1.6} autorouter={{local:true, traceClearance:0.25}} minTraceWidth={0.25} minViaHoleDiameter={0.3} minViaPadDiameter={0.6} pcbStyle={{silkscreenFontSize:0.9}}
    outline={[{x:-58,y:-20},{x:58,y:-20},{x:60,y:-18},{x:60,y:18},{x:58,y:20},{x:-58,y:20},{x:-60,y:18},{x:-60,y:-18}]}>
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
    {[-56,56].flatMap(x=>[-16,16].map(y=><hole key={`${x}:${y}`} name={`M_${x}_${y}`} pcbX={x} pcbY={y} diameter={3.2} />))}
    <keepout shape="rect" pcbX={-24} pcbY={0} width={20} height={24} layers={["top","bottom"]} />
    {testpoints.map(([ref,net,x,y])=><silkscreentext key={`label-${ref}`} pcbX={x} pcbY={y+(y>0?-2:2)} text={`${ref} ${net}`} fontSize={0.55} />)}
    <silkscreentext pcbX={12} pcbY={0} layer="bottom" text="DANGER 400V - DISCHARGE AND VERIFY" fontSize={1.2} />
    {/* Local clip access only; no blanket copper/component keepout under tube. */}
    <silkscreenrect pcbX={0} pcbY={0} width={110} height={12} stroke="dashed" strokeWidth={0.15} />
    <silkscreentext pcbX={0} pcbY={19} text="DANGER 400V - DISCHARGE BEFORE TOUCH" fontSize={0.95} />
    <silkscreentext pcbX={-52} pcbY={7} text="PULSE LED" fontSize={0.65} />
    <silkscreentext pcbX={-47} pcbY={18.5} text="CUT = LED OFF" fontSize={0.65} />
    <silkscreentext pcbX={52} pcbY={6} text="HV ANODE" fontSize={0.8} />
    <silkscreenrect pcbX={-24} pcbY={0} width={20} height={24} stroke="dashed" strokeWidth={0.15} />
    <silkscreentext pcbX={-24} pcbY={4} text="U1/U2 RESERVE" fontSize={0.85} />
    <silkscreentext pcbX={-24} pcbY={0} text="ANALOG - NO MCU" fontSize={0.8} />
    <silkscreentext pcbX={-24} pcbY={-4} text="HEIGHT TBD" fontSize={0.8} />
    <silkscreentext pcbX={-43} pcbY={-18} text="3V3 GND PULSE EN" fontSize={0.7} />
    <silkscreentext pcbX={15} pcbY={-19} text="HV MAY REMAIN AFTER POWER OFF" fontSize={0.8} />
  </board>
}
