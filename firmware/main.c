#define F_CPU 20000000UL
#include <avr/io.h>
#include <avr/interrupt.h>
#include <avr/wdt.h>
#include <util/delay.h>
#include <stdint.h>
#include <stdbool.h>
#include "pins.h"

static volatile uint32_t pulse_count;
static volatile uint16_t pulse_window;
static volatile uint8_t pulse_out_ticks;

static void uart_init(void) {
    PORTB.DIRSET = UART_TX_bm;
    PORTB.DIRCLR = UART_RX_bm;
    /* 20 MHz / (16 * 115200) - 1, rounded for the internal oscillator. */
    USART0.BAUD = 138;
    USART0.CTRLB = USART_TXEN_bm | USART_RXEN_bm;
}

static void uart_putc(char c) {
    while (!(USART0.STATUS & USART_DREIF_bm)) {}
    USART0.TXDATAL = (uint8_t)c;
}

static void uart_puts(const char *s) { while (*s) uart_putc(*s++); }

static void uart_u32(uint32_t v) {
    char b[11]; uint8_t i = 0;
    if (!v) { uart_putc('0'); return; }
    while (v && i < sizeof b) { b[i++] = '0' + (uint8_t)(v % 10u); v /= 10u; }
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

static void timer_init(void) {
    /* Timer counts accepted comparator edges; EVSYS routing is finalized with
       the package pin mux in the native schematic. */
    TCA0.SINGLE.PER = 999;
    TCA0.SINGLE.CTRLA = TCA_SINGLE_CLKSEL_DIV64_gc | TCA_SINGLE_ENABLE_bm;
    PORTA.DIRCLR = PULSE_IN_bm;
    PORTA.PIN2CTRL = PORT_PULLUPEN_bm | PORT_ISC_RISING_gc;
}

static void gpio_init(void) {
    PORTA.DIRSET = PULSE_OUT_bm;
    PORTA.OUTCLR = PULSE_OUT_bm;
    PORTB.DIRSET = HV_ENABLE_bm;
    PORTB.OUTCLR = HV_ENABLE_bm;
    PORTB.DIRCLR = ADDR_A0_bm | ADDR_A1_bm;
    PORTB.PIN0CTRL = PORT_PULLUPEN_bm;
    PORTB.PIN1CTRL = PORT_PULLUPEN_bm;
}

static uint8_t address_bits(void) {
    uint8_t a = 0;
    if (!(PORTB.IN & ADDR_A0_bm)) a |= 1;
    if (!(PORTB.IN & ADDR_A1_bm)) a |= 2;
    return a;
}

ISR(PORTA_PORT_vect) {
    uint8_t flags = PORTA.INTFLAGS;
    PORTA.INTFLAGS = flags;
    if (flags & PULSE_IN_bm) {
        pulse_count++;
        pulse_window++;
        PORTA.OUTSET = PULSE_OUT_bm;
        pulse_out_ticks = 5; /* nominal 50 us at the 100 us service tick */
    }
}

int main(void) {
    wdt_enable(WDT_PERIOD_1S_gc);
    gpio_init(); uart_init(); adc_init(); timer_init(); sei();
    uart_puts("GLOWCOST ATtiny1616 bringup\r\n");
    uart_puts("I2C address=0x3"); uart_putc('6' + address_bits()); uart_puts("\r\n");
    uint16_t tick = 0;
    for (;;) {
        wdt_reset();
        _delay_us(100);
        if (pulse_out_ticks && --pulse_out_ticks == 0) PORTA.OUTCLR = PULSE_OUT_bm;
        if (++tick >= 10000) {
            tick = 0;
            uart_puts("count="); uart_u32(pulse_count);
            uart_puts(" hv="); uart_u32(adc_read(HV_SENSE_ADC));
            uart_puts(" v3v3="); uart_u32(adc_read(V3V3_SENSE_ADC));
            uart_puts("\r\n");
            pulse_window = 0;
        }
    }
}
