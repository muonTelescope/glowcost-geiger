#ifndef GLOWCOST_PINS_H
#define GLOWCOST_PINS_H

#include <avr/io.h>

/*
 * ATtiny1616-MNR pin map (schematic U1, VQFN-20).
 * USART0 TX uses alternate mux on PA1 — default TX is PB2 (= HV_PWM).
 */
#define PULSE_IN_bm       PIN2_bm   /* PA2 COLLECTOR */
#define SDA_bm            PIN4_bm   /* PA4 */
#define SCL_bm            PIN5_bm   /* PA5 */
#define HV_SENSE_ADC      6u        /* PA6 SENSE */
#define V3V3_SENSE_ADC    7u        /* PA7 V3V3_SENSE */
#define ADDR_A0_bm        PIN0_bm   /* PB0 */
#define ADDR_A1_bm        PIN1_bm   /* PB1 */
#define HV_PWM_bm         PIN2_bm   /* PB2 boost gate via R25 */
#define HV_ENABLE_bm      PIN3_bm   /* PB3 EN */
#define UART_TX_bm        PIN1_bm   /* PA1 alternate USART0 TX */
#define UPDI_bm           PIN0_bm   /* PA0 */

#endif
