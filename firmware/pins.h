#ifndef GLOWCOST_PINS_H
#define GLOWCOST_PINS_H

#include <avr/io.h>

/*
 * ATtiny1616-MNR pin map (schematic U1, VQFN-20).
 * TWI0 defaults are PB1 SDA and PB0 SCL. PA4/PA5 are not TWI.
 * USART0 TX uses the alternate mux on PA1 — default TX is PB2 (HV_PWM).
 * PA3, PA4, PA5, PA7, PB3, PB4, PB5, PC2, PC3 are no-connect.
 * Boost enable is firmware. There is no enable pin and no 3V3 sense.
 */
#define PULSE_IN_bm       PIN2_bm   /* PA2 COLLECTOR */
#define HV_SENSE_ADC      6u        /* PA6 SENSE */
#define SDA_bm            PIN1_bm   /* PB1 TWI0 SDA */
#define SCL_bm            PIN0_bm   /* PB0 TWI0 SCL */
#define ADDR_A0_bm        PIN0_bm   /* PC0 */
#define ADDR_A1_bm        PIN1_bm   /* PC1 */
#define HV_PWM_bm         PIN2_bm   /* PB2 boost gate via R25 */
#define UART_TX_bm        PIN1_bm   /* PA1 alternate USART0 TX */
#define UPDI_bm           PIN0_bm   /* PA0 */

#endif
