#define F_CPU 20000000UL

#include <avr/io.h>
#include <avr/interrupt.h>
#include <avr/cpufunc.h>
#include <avr/wdt.h>
#include <stdint.h>
#include <stdbool.h>
#include "pins.h"
#include "regs.h"

/*
 * ATtiny1616 HV regulator and I2C slave.
 *
 * CTC-5 / STS-5 and SBM-20 share this ~400 V bias. The tube register
 * only labels which one is fitted. PA6 is the feedback (VDD reference,
 * about 1.04 V of tube voltage per count at 3.3 V). TCA0 WO2 on PB2
 * is 10 kHz. The loop steps one count every 10 ms toward the setpoint
 * and will not go past 20% duty. A stuck 20% with the sense still low
 * latches off. TWI0 is PB1 SDA / PB0 SCL.
 */

#define HV_OVP_ADC      405u /* ~420 V at 3.3 V */
#define HV_RECOVER_ADC  376u /* ~390 V */
#define HV_TARGET_ADC   386u /* ~400 V */
#define HV_TARGET_MIN   200u /* ~208 V, lowest host setpoint */
#define HV_BAND         8u
#define HV_PWM_PERIOD   2000u /* 20 MHz / 2000 = 10 kHz */
#define HV_DUTY_MAX     400u  /* 20% ceiling */
#define HV_DUTY_START   20u   /* 1% */
#define HV_CEIL_TICKS   20u   /* 200 ms at the ceiling with sense still low */
#define HV_TICKS_10MS   100u  /* TCA overflows of 100 us */
#define PULSE_BLANK     3u    /* 200–300 us, rejects a bouncing edge */

static volatile uint32_t pulse_count;
static volatile uint16_t pulse_window;
static volatile uint16_t cps_latched;
static volatile uint16_t hv_sense;
static volatile uint16_t hv_duty;
static volatile uint16_t hv_target = HV_TARGET_ADC;
static volatile uint8_t pulse_blank;
static volatile uint8_t tube_id = TUBE_EITHER;
static volatile bool hv_en;
static volatile bool hv_ovp;
static volatile bool hv_fail;
static volatile bool hv_due;
static volatile bool report_due;

static uint8_t i2c_ptr;
static bool i2c_ptr_set;
static uint8_t snap[REG_MAP_LEN];

static uint16_t load16(const volatile uint16_t *p) {
    uint16_t v;
    uint8_t s = SREG;
    cli();
    v = *p;
    SREG = s;
    return v;
}

static void store16(volatile uint16_t *p, uint16_t v) {
    uint8_t s = SREG;
    cli();
    *p = v;
    SREG = s;
}

static uint32_t load32(const volatile uint32_t *p) {
    uint32_t v;
    uint8_t s = SREG;
    cli();
    v = *p;
    SREG = s;
    return v;
}

static void clock_init(void) {
    /* Factory prescaler is 6, which would leave 3.33 MHz. */
    ccp_write_io((void *)&CLKCTRL.MCLKCTRLB, 0);
}

static void uart_init(void) {
    PORTMUX.CTRLB = PORTMUX_USART0_ALTERNATE_gc; /* TX -> PA1 */
    PORTA.DIRSET = UART_TX_bm;
    /* BAUD = 64 * F_CPU / (16 * 115200) = 694. */
    USART0.BAUD = 694;
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

static void uart_hex8(uint8_t v) {
    static const char h[] = "0123456789ABCDEF";
    uart_putc(h[v >> 4]);
    uart_putc(h[v & 0x0Fu]);
}

static void adc_init(void) {
    /* The 412 kOhm sense leg needs a long sample. */
    ADC0.CTRLC = ADC_PRESC_DIV64_gc | ADC_REFSEL_VDDREF_gc;
    ADC0.SAMPCTRL = 31;
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
    uint8_t s;
    if (duty > HV_DUTY_MAX) duty = HV_DUTY_MAX;
    s = SREG;
    cli();
    hv_duty = duty;
    TCA0.SINGLE.CMP2 = duty;
    SREG = s;
}

static void hv_pwm_init(void) {
    PORTB.DIRSET = HV_PWM_bm;
    PORTB.OUTCLR = HV_PWM_bm;
    TCA0.SINGLE.PER = HV_PWM_PERIOD - 1u;
    TCA0.SINGLE.CMP2 = 0;
    TCA0.SINGLE.CTRLB =
        TCA_SINGLE_WGMODE_SINGLESLOPE_gc | TCA_SINGLE_CMP2EN_bm;
    TCA0.SINGLE.INTCTRL = TCA_SINGLE_OVF_bm;
    TCA0.SINGLE.CTRLA =
        TCA_SINGLE_CLKSEL_DIV1_gc | TCA_SINGLE_ENABLE_bm;
}

static void hv_stop(void) {
    hv_ovp = false;
    hv_fail = false;
    hv_set_duty(0);
}

static void hv_request(bool on) {
    hv_en = on;
    if (!on) hv_stop();
    else if (load16(&hv_duty) == 0) hv_set_duty(HV_DUTY_START);
}

static void hv_service(void) {
    uint16_t sense = adc_read(HV_SENSE_ADC);
    uint16_t target = load16(&hv_target);
    uint16_t duty = load16(&hv_duty);
    static uint8_t ceil_ticks;

    store16(&hv_sense, sense);
    if (!hv_en || hv_fail) {
        hv_set_duty(0);
        ceil_ticks = 0;
        return;
    }
    if (sense >= HV_OVP_ADC) {
        hv_ovp = true;
        hv_set_duty(0);
        ceil_ticks = 0;
        return;
    }
    if (hv_ovp) {
        if (sense <= HV_RECOVER_ADC) {
            hv_ovp = false;
            hv_set_duty(HV_DUTY_START);
        }
        return;
    }
    if (sense + HV_BAND < target) {
        if (duty < HV_DUTY_MAX) {
            hv_set_duty((uint16_t)(duty + 1u));
            ceil_ticks = 0;
        } else if (++ceil_ticks >= HV_CEIL_TICKS) {
            hv_fail = true;
            hv_set_duty(0);
        }
    } else {
        ceil_ticks = 0;
        if (sense > target + HV_BAND && duty > 0)
            hv_set_duty((uint16_t)(duty - 1u));
    }
}

static void pulse_init(void) {
    PORTA.DIRCLR = PULSE_IN_bm;
    PORTA.PIN2CTRL = PORT_PULLUPEN_bm | PORT_ISC_RISING_gc;
}

static void gpio_init(void) {
    PORTC.DIRCLR = ADDR_A0_bm | ADDR_A1_bm;
    PORTC.PIN0CTRL = PORT_PULLUPEN_bm;
    PORTC.PIN1CTRL = PORT_PULLUPEN_bm;
}

static uint8_t address_bits(void) {
    uint8_t a = 0;
    if (!(PORTC.IN & ADDR_A0_bm)) a |= 1u;
    if (!(PORTC.IN & ADDR_A1_bm)) a |= 2u;
    return a;
}

static uint8_t i2c_address(void) {
    return (uint8_t)(0x2Fu + address_bits());
}

static void counts_clear(void) {
    uint8_t s = SREG;
    cli();
    pulse_count = 0;
    pulse_window = 0;
    SREG = s;
}

static uint8_t status_byte(void) {
    uint8_t st = 0;
    uint16_t sense = load16(&hv_sense);
    uint16_t target = load16(&hv_target);
    if (hv_en) st |= ST_HV_EN;
    if (hv_ovp) st |= ST_OVP;
    if (hv_fail) st |= ST_FAIL;
    if (hv_en && !hv_ovp && !hv_fail && load16(&hv_duty) > 0 &&
        sense + HV_BAND >= target && sense <= target + HV_BAND)
        st |= ST_REG;
    return st;
}

static void snapshot(void) {
    uint32_t count = pulse_count;
    uint16_t cps = load16(&cps_latched);
    uint16_t sense = load16(&hv_sense);
    uint16_t duty = load16(&hv_duty);
    uint16_t target = load16(&hv_target);
    uint8_t i;

    for (i = 0; i < REG_MAP_LEN; i++) snap[i] = 0xFF;
    snap[REG_ID] = REG_ID_VALUE;
    snap[REG_FW] = REG_FW_VALUE;
    snap[REG_STATUS] = status_byte();
    snap[REG_CTRL] = hv_en ? CTRL_HV_EN : 0;
    snap[REG_COUNT + 0] = (uint8_t)count;
    snap[REG_COUNT + 1] = (uint8_t)(count >> 8);
    snap[REG_COUNT + 2] = (uint8_t)(count >> 16);
    snap[REG_COUNT + 3] = (uint8_t)(count >> 24);
    snap[REG_CPS] = (uint8_t)cps;
    snap[REG_CPS + 1] = (uint8_t)(cps >> 8);
    snap[REG_HV_ADC] = (uint8_t)sense;
    snap[REG_HV_ADC + 1] = (uint8_t)(sense >> 8);
    snap[REG_DUTY] = (uint8_t)duty;
    snap[REG_DUTY + 1] = (uint8_t)(duty >> 8);
    snap[REG_TARGET] = (uint8_t)target;
    snap[REG_TARGET + 1] = (uint8_t)(target >> 8);
    snap[REG_TUBE] = tube_id;
    snap[REG_CMD] = 0;
}

static void reg_write(uint8_t reg, uint8_t val) {
    uint16_t target;
    switch (reg) {
    case REG_CTRL:
        hv_request((val & CTRL_HV_EN) != 0);
        break;
    case REG_TARGET:
        target = (uint16_t)((load16(&hv_target) & 0xFF00u) | val);
        if (target < HV_TARGET_MIN) target = HV_TARGET_MIN;
        if (target >= HV_OVP_ADC) target = HV_OVP_ADC - 1u;
        store16(&hv_target, target);
        break;
    case REG_TARGET + 1:
        target = (uint16_t)((load16(&hv_target) & 0x00FFu) | ((uint16_t)val << 8));
        if (target < HV_TARGET_MIN) target = HV_TARGET_MIN;
        if (target >= HV_OVP_ADC) target = HV_OVP_ADC - 1u;
        store16(&hv_target, target);
        break;
    case REG_TUBE:
        if (val <= TUBE_SBM20) tube_id = val;
        break;
    case REG_CMD:
        if (val == REG_CMD_CLEAR) counts_clear();
        break;
    default:
        break;
    }
}

static void twi_init(uint8_t addr7) {
    /* Default TWI pins are PB1 SDA and PB0 SCL. ADDR[7:1], no general call. */
    TWI0.SADDR = (uint8_t)(addr7 << 1);
    TWI0.SCTRLA = TWI_DIEN_bm | TWI_APIEN_bm | TWI_PIEN_bm | TWI_ENABLE_bm;
}

ISR(TWI0_TWIS_vect) {
    uint8_t s = TWI0.SSTATUS;

    if (s & (TWI_BUSERR_bm | TWI_COLL_bm)) {
        TWI0.SSTATUS = (uint8_t)(s & (TWI_BUSERR_bm | TWI_COLL_bm));
        i2c_ptr_set = false;
        TWI0.SCTRLB = TWI_SCMD_COMPTRANS_gc;
        return;
    }
    if (s & TWI_APIF_bm) {
        if (s & TWI_AP_bm) {
            if (s & TWI_DIR_bm) {
                snapshot();
                TWI0.SDATA = (i2c_ptr < REG_MAP_LEN) ? snap[i2c_ptr] : 0xFF;
                if (i2c_ptr < 255) i2c_ptr++;
            } else {
                i2c_ptr_set = false;
            }
            TWI0.SCTRLB = TWI_ACKACT_ACK_gc | TWI_SCMD_RESPONSE_gc;
        } else {
            i2c_ptr_set = false;
            TWI0.SCTRLB = TWI_SCMD_COMPTRANS_gc;
        }
        return;
    }
    if (s & TWI_DIF_bm) {
        if (s & TWI_DIR_bm) {
            if (s & TWI_RXACK_bm) {
                TWI0.SCTRLB = TWI_SCMD_COMPTRANS_gc;
            } else {
                TWI0.SDATA = (i2c_ptr < REG_MAP_LEN) ? snap[i2c_ptr] : 0xFF;
                if (i2c_ptr < 255) i2c_ptr++;
                TWI0.SCTRLB = TWI_ACKACT_ACK_gc | TWI_SCMD_RESPONSE_gc;
            }
        } else {
            uint8_t b = TWI0.SDATA;
            if (!i2c_ptr_set) {
                i2c_ptr = b;
                i2c_ptr_set = true;
            } else {
                reg_write(i2c_ptr, b);
                if (i2c_ptr < 255) i2c_ptr++;
            }
            TWI0.SCTRLB = TWI_ACKACT_ACK_gc | TWI_SCMD_RESPONSE_gc;
        }
        return;
    }
    TWI0.SCTRLB = TWI_SCMD_COMPTRANS_gc;
}

ISR(TCA0_OVF_vect) {
    static uint8_t ticks;
    TCA0.SINGLE.INTFLAGS = TCA_SINGLE_OVF_bm;
    if (pulse_blank) pulse_blank--;
    if (++ticks >= HV_TICKS_10MS) {
        ticks = 0;
        hv_due = true;
    }
}

ISR(RTC_PIT_vect) {
    RTC.PITINTFLAGS = RTC_PI_bm;
    store16(&cps_latched, pulse_window);
    pulse_window = 0;
    report_due = true;
}

ISR(PORTA_PORT_vect) {
    uint8_t flags = PORTA.INTFLAGS;
    PORTA.INTFLAGS = flags;
    if ((flags & PULSE_IN_bm) && pulse_blank == 0) {
        pulse_count++;
        pulse_window++;
        pulse_blank = PULSE_BLANK;
    }
}

static void rtc_init(void) {
    RTC.CLKSEL = RTC_CLKSEL_INT32K_gc;
    while (RTC.PITSTATUS & RTC_CTRLBUSY_bm) {}
    RTC.PITCTRLA = RTC_PERIOD_CYC32768_gc | RTC_PITEN_bm;
    RTC.PITINTCTRL = RTC_PI_bm;
}

int main(void) {
    uint8_t addr;

    clock_init();
    wdt_enable(WDTO_1S);
    gpio_init();
    uart_init();
    adc_init();
    pulse_init();
    hv_pwm_init();
    rtc_init();
    addr = i2c_address();
    twi_init(addr);
    sei();

    uart_puts("gLowCost-geiger ATtiny1616\r\naddr=0x");
    uart_hex8(addr);
    uart_puts(" STS-5/SBM-20 HV off\r\n");

    for (;;) {
        wdt_reset();
        if (hv_due) {
            hv_due = false;
            hv_service();
        }
        if (report_due) {
            report_due = false;
            uart_puts("count=");
            uart_u32(load32(&pulse_count));
            uart_puts(" cps=");
            uart_u32(load16(&cps_latched));
            uart_puts(" hv=");
            uart_u32(load16(&hv_sense));
            uart_puts(" duty=");
            uart_u32(load16(&hv_duty));
            if (hv_fail) uart_puts(" FAIL");
            else if (hv_ovp) uart_puts(" OVP");
            else if (!hv_en) uart_puts(" OFF");
            uart_puts("\r\n");
        }
    }
}
