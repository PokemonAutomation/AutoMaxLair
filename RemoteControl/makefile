#
#             LUFA Library
#     Copyright (C) Dean Camera, 2014.
#
#  dean [at] fourwalledcubicle [dot] com
#           www.lufa-lib.org
#
# --------------------------------------
#         LUFA Project Makefile.
# --------------------------------------

# MCU Types: 
# at90usb1286 for Teensy 2.0++
# atmega16u2 for Arduino UNO R3
# atmega32u4 for Arduino Micro/Teensy 2.0

MCU          = atmega32u4
ARCH         = AVR8
F_CPU        = 16000000
F_USB        = $(F_CPU)
OPTIMIZATION = s
TARGET       = RemoteControl_$(MCU)
UART_PATH    = ./Source/uart
SRC          = ./Source/RemoteControl.c ./Config/Descriptors.c $(LUFA_SRC_USB) $(UART_PATH).c
LUFA_PATH    = ./LUFA/LUFA
CC_FLAGS     = -DUSE_LUFA_CONFIG_HEADER -IConfig/
LD_FLAGS     =

# Default target
all:

# Include LUFA build script makefiles
include $(LUFA_PATH)/Build/lufa_core.mk
include $(LUFA_PATH)/Build/lufa_sources.mk
include $(LUFA_PATH)/Build/lufa_build.mk
include $(LUFA_PATH)/Build/lufa_cppcheck.mk
include $(LUFA_PATH)/Build/lufa_doxygen.mk
include $(LUFA_PATH)/Build/lufa_dfu.mk
include $(LUFA_PATH)/Build/lufa_hid.mk
include $(LUFA_PATH)/Build/lufa_avrdude.mk
include $(LUFA_PATH)/Build/lufa_atprogram.mk

clean:
	rm $(TARGET).elf
	rm $(TARGET).map
