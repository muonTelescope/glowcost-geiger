MCU=attiny1616
CC=avr-gcc
OBJCOPY=avr-objcopy
OBJDUMP=avr-objdump
CFLAGS=-std=c11 -Os -Wall -Wextra -mmcu=$(MCU) -DF_CPU=20000000UL
TARGET=build/gLowCost-geiger

.PHONY: all flash clean

all: $(TARGET).hex $(TARGET).lst

build:
	mkdir -p build

$(TARGET).elf: main.c pins.h | build
	$(CC) $(CFLAGS) -I. main.c -o $@

$(TARGET).hex: $(TARGET).elf
	$(OBJCOPY) -O ihex -R .eeprom $< $@

$(TARGET).lst: $(TARGET).elf
	$(OBJDUMP) -S $< > $@

flash: $(TARGET).hex
	pymcuprog write -d $(MCU) -t uart -u /dev/cu.usbserial-* -f $<

clean:
	rm -rf build
