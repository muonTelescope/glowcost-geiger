import { hvModel } from './model'
/** Exploratory closed-loop HV model. Footprint is a simulation symbol only. */
export default () => (
  <board routingDisabled>
    <voltagesource name="VBAT" voltage="3.3V" schX={-6} schY={0} />
    <voltagesource name="VEN" voltage="3.3V" schX={-6} schY={-5} />
    <chip name="HV" footprint="soic8" schX={0} schY={0}
      pinLabels={{pin1:"battery", pin2:"GND", pin3:"hv",pin4:"sw",pin5:"sense",pin6:"en",pin7:"ttl"}}
      spiceModel={<spicemodel source={hvModel} />} />
    <trace from=".VBAT > .pin1" to=".HV > .battery" />
    <trace from=".VBAT > .pin2" to=".HV > .GND" />
    <trace from=".VEN > .pin1" to=".HV > .en" />
    <trace from=".VEN > .pin2" to=".HV > .GND" />
    <voltageprobe name="TTL" connectsTo=".HV > .ttl" />
    <voltageprobe name="HV_OUT" connectsTo=".HV > .hv" />
    <voltageprobe name="SWITCH" connectsTo=".HV > .sw" />
    <voltageprobe name="HV_SENSE" connectsTo=".HV > .sense" />
    <analogsimulation duration="120ms" timePerStep="2us" spiceEngine="ngspice" />
  </board>
)
