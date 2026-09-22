MCU=attiny1616
# avr-gcc 9 accepts this part but ships no iotn1616.h. Prefer the
# keg-only GCC 14 when it is installed. Override with `make CC=...`.
CC ?= avr-gcc
ifneq ($(wildcard /opt/homebrew/opt/avr-gcc@14/bin/avr-gcc),)
CC := /opt/homebrew/opt/avr-gcc@14/bin/avr-gcc
endif
OBJCOPY=avr-objcopy
OBJDUMP=avr-objdump
CFLAGS=-std=c11 -Os -Wall -Wextra -mmcu=$(MCU) -DF_CPU=20000000UL
TARGET=build/gLowCost-geiger

.PHONY: all flash clean

all: $(TARGET).hex $(TARGET).lst

build:
	mkdir -p build

$(TARGET).elf: main.c pins.h regs.h | build
	$(CC) $(CFLAGS) -I. main.c -o $@

$(TARGET).hex: $(TARGET).elf
	$(OBJCOPY) -O ihex -R .eeprom $< $@

$(TARGET).lst: $(TARGET).elf
	$(OBJDUMP) -S $< > $@

flash: $(TARGET).hex
	pymcuprog write -d $(MCU) -t uart -u /dev/cu.usbserial-* -f $<

clean:
	rm -rf build
