#ifndef GLOWCOST_REGS_H
#define GLOWCOST_REGS_H

/*
 * I2C register map, little-endian. The first byte of a write sets the
 * pointer. Further writes store and increment. A read returns the byte
 * at the pointer and increments. Snapshot is taken at each SLA+R.
 *
 * Open address straps: 0x2F. A bridge to ground on A0, A1, or both
 * selects 0x30, 0x31, or 0x32.
 */

#define REG_ID      0x00u /* 0x47 */
#define REG_FW      0x01u /* firmware revision */
#define REG_STATUS  0x02u
#define REG_CTRL    0x03u /* bit 0: 1 runs the boost, 0 stops it */
#define REG_COUNT   0x04u /* uint32 cumulative pulses */
#define REG_CPS     0x08u /* uint16 pulses in the previous second */
#define REG_HV_ADC  0x0Au /* uint16 latest PA6 code */
#define REG_DUTY    0x0Cu /* uint16 TCA0 CMP2 */
#define REG_TARGET  0x0Eu /* uint16 writable PA6 setpoint */
#define REG_TUBE    0x10u /* 0 either, 1 CTC-5/STS-5, 2 SBM-20 */
#define REG_CMD     0x11u /* write 0xA5 to clear the cumulative count */
#define REG_MAP_LEN 0x12u

#define REG_ID_VALUE 0x47u
#define REG_FW_VALUE 0x01u
#define REG_CMD_CLEAR 0xA5u

#define ST_HV_EN 0x01u
#define ST_OVP   0x02u
#define ST_REG   0x04u
#define ST_FAIL  0x08u

#define CTRL_HV_EN 0x01u

#define TUBE_EITHER 0u
#define TUBE_STS5   1u /* CTC-5 / STS-5 */
#define TUBE_SBM20  2u

#endif
