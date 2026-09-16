#ifndef GLOWCOST_PINS_H
#define GLOWCOST_PINS_H

#include <avr/io.h>

/* Provisional logical map; verify package mux before production release. */
#define PULSE_IN_bm       PIN2_bm
#define PULSE_OUT_bm      PIN3_bm
#define SDA_bm            PIN4_bm
#define SCL_bm            PIN5_bm
#define HV_SENSE_ADC      6u
#define V3V3_SENSE_ADC    7u
#define ADDR_A0_bm        PIN0_bm
#define ADDR_A1_bm        PIN1_bm
#define HV_ENABLE_bm      PIN2_bm
#define UART_TX_bm        PIN3_bm
#define UART_RX_bm        PIN4_bm

#endif
