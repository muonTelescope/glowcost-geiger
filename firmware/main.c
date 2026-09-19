#define F_CPU 20000000UL

#include <avr/io.h>
#include <avr/interrupt.h>
#include <avr/wdt.h>
#include <util/delay.h>
#include <stdint.h>
#include <stdbool.h>
#include "pins.h"

/*
 * gLowCost-geiger HV firmware (ATtiny1616).
 *
 * No hardware OVP comparator on this revision. PA6 SENSE
 * (4 x 33 MOhm + 412 kOhm => ~1.24 V at 400 V) is the clamp input.
 *
 *   ADC (VDD=3.3 V, 10-bit) ≈ HV_volts * 0.964
 *   400 V -> ~386,  420 V -> ~405,  390 V -> ~376
 */

#define HV_OVP_ADC      405u  /* ~420 V trip */
#define HV_RECOVER_ADC  376u  /* ~390 V restart */
#define HV_PWM_PERIOD   2000u /* 20 MHz / 2000 = 10 kHz */
#define HV_DUTY_MAX     400u  /* 20% bring-up cap */
#define HV_DUTY_START   20u

static volatile uint32_t pulse_count;
static volatile uint16_t pulse_window;
static bool hv_fault;
static uint16_t hv_duty;

static void uart_init(void) {
    PORTMUX.CTRLB = PORTMUX_USART0_ALTERNATE_gc; /* TX -> PA1 */
    PORTA.DIRSET = UART_TX_bm;
    USART0.BAUD = 138; /* ~115200 @ 20 MHz */
    USART0.CTRLB = USART_TXEN_bm;
}

static void uart_putc(char c) {
    while (!(USART0.STATUS & USART_DREIF_bm)) {}
    USART0.TXDATAL = (uint8_t)c;
}

static void uart_puts(const char *s) {
    while (*s) uart_putc(*s++);
}

static void uart_u32(uint32_t v) {
    char b[11];
    uint8_t i = 0;
    if (!v) { uart_putc('0'); return; }
    while (v && i < sizeof b) {
        b[i++] = (char)('0' + (v % 10u));
        v /= 10u;
    }
    while (i) uart_putc(b[--i]);
}

static void adc_init(void) {
    ADC0.CTRLC = ADC_PRESC_DIV16_gc | ADC_REFSEL_VDDREF_gc;
    ADC0.CTRLA = ADC_ENABLE_bm;
}

static uint16_t adc_read(uint8_t mux) {
    ADC0.MUXPOS = mux;
    ADC0.COMMAND = ADC_STCONV_bm;
    while (!(ADC0.INTFLAGS & ADC_RESRDY_bm)) {}
    ADC0.INTFLAGS = ADC_RESRDY_bm;
    return ADC0.RES;
}

static void hv_set_duty(uint16_t duty) {
    if (duty > HV_DUTY_MAX) duty = HV_DUTY_MAX;
    hv_duty = duty;
    TCA0.SINGLE.CMP2 = duty;
}

static void hv_enable(bool on) {
    if (on) {
        PORTB.OUTSET = HV_ENABLE_bm;
    } else {
        PORTB.OUTCLR = HV_ENABLE_bm;
        hv_set_duty(0);
    }
}

static void hv_pwm_init(void) {
    PORTB.DIRSET = HV_PWM_bm | HV_ENABLE_bm;
    PORTB.OUTCLR = HV_PWM_bm | HV_ENABLE_bm;
    TCA0.SINGLE.PER = HV_PWM_PERIOD - 1u;
    TCA0.SINGLE.CMP2 = 0;
    TCA0.SINGLE.CTRLB =
        TCA_SINGLE_WGMODE_SINGLESLOPE_gc | TCA_SINGLE_CMP2EN_bm;
    TCA0.SINGLE.CTRLA =
        TCA_SINGLE_CLKSEL_DIV1_gc | TCA_SINGLE_ENABLE_bm;
}

static void hv_service(void) {
    uint16_t sense = adc_read(HV_SENSE_ADC);

    if (!hv_fault && sense >= HV_OVP_ADC) {
        hv_fault = true;
        hv_enable(false);
        return;
    }
    if (hv_fault) {
        if (sense <= HV_RECOVER_ADC) {
            hv_fault = false;
            hv_enable(true);
            hv_set_duty(HV_DUTY_START);
        }
        return;
    }
    if (hv_duty < HV_DUTY_MAX) {
        hv_set_duty((uint16_t)(hv_duty + 1u));
    }
}

static void pulse_init(void) {
    PORTA.DIRCLR = PULSE_IN_bm;
    PORTA.PIN2CTRL = PORT_PULLUPEN_bm | PORT_ISC_RISING_gc;
}

static void gpio_init(void) {
    PORTB.DIRCLR = ADDR_A0_bm | ADDR_A1_bm;
    PORTB.PIN0CTRL = PORT_PULLUPEN_bm;
    PORTB.PIN1CTRL = PORT_PULLUPEN_bm;
}

static uint8_t address_bits(void) {
    uint8_t a = 0;
    if (!(PORTB.IN & ADDR_A0_bm)) a |= 1u;
    if (!(PORTB.IN & ADDR_A1_bm)) a |= 2u;
    return a;
}

ISR(PORTA_PORT_vect) {
    uint8_t flags = PORTA.INTFLAGS;
    PORTA.INTFLAGS = flags;
    if (flags & PULSE_IN_bm) {
        pulse_count++;
        pulse_window++;
    }
}

int main(void) {
    wdt_enable(WDTO_1S);
    gpio_init();
    uart_init();
    adc_init();
    pulse_init();
    hv_pwm_init();
    sei();

    uart_puts("gLowCost-geiger ATtiny1616\r\n");
    uart_puts("addr=0x");
    {
        uint8_t a = address_bits();
        if (a == 0) uart_puts("2F");
        else {
            uart_putc('3');
            uart_putc((char)('0' + a - 1));
        }
    }
    uart_puts(" L1=YNR6045-102M OVP=fw\r\n");

    hv_fault = false;
    hv_enable(true);
    hv_set_duty(HV_DUTY_START);

    uint16_t tick = 0;
    for (;;) {
        wdt_reset();
        hv_service();
        _delay_us(100);
        if (++tick >= 10000) {
            tick = 0;
            uart_puts("count=");
            uart_u32(pulse_count);
            uart_puts(" hv=");
            uart_u32(adc_read(HV_SENSE_ADC));
            uart_puts(" v3=");
            uart_u32(adc_read(V3V3_SENSE_ADC));
            uart_puts(" duty=");
            uart_u32(hv_duty);
            uart_puts(hv_fault ? " FAULT\r\n" : "\r\n");
            pulse_window = 0;
        }
    }
}
