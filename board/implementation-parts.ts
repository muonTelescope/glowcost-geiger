/** Selected for the next pin-level implementation; NOT instantiated by module.circuit.tsx.
 * Quantities and timing/drive networks must follow the completed physical circuit.
 */
export const implementationParts = {
  oscillator: { mpn: 'LMC555CMX/NOPB', lcsc: 'C90760', package: 'SOIC-8' },
  referenceComparator: { mpn: 'TLV3012BIDBVR', lcsc: 'C20345924', package: 'SOT-23-6', quantity: 2 },
  hvSwitch: { mpn: 'MMBTA42LT1G', lcsc: 'C94389', package: 'SOT-23' },
  inductor: { mpn: 'B82442T1105K050', lcsc: 'C2041861', value: '1mH', package: '5.6x5mm' },
  schmitt: { mpn: 'SN74LVC1G14DBVR', lcsc: 'C7835', package: 'SOT-23-5' },
  andGate: { mpn: 'SN74LVC1G08DBVR', lcsc: 'C7666', package: 'SOT-23-5' },
  orGate: { mpn: 'SN74LVC1G32DBVR', lcsc: 'C10096', package: 'SOT-23-5' },
  softStart: { mpn: 'TPS22918TDBVRQ1', lcsc: 'C2653760', package: 'SOT-23-6' },
  slewCap: { mpn: 'GRM1885C1H103JA01D', lcsc: 'C85973', value: '10nF', package: '0603' },
  bulkCap: { mpn: 'GRM32ER61C476KE15L', lcsc: 'C77101', value: '47uF', package: '1210' },
  localBypass: { mpn: 'CC0603KRX7R9BB104', lcsc: 'C14663', value: '100nF', package: '0603' },
  inputBypass: { mpn: 'CL10B105KB8NQNC', lcsc: 'C5199872', value: '1uF', package: '0603' },
} as const
