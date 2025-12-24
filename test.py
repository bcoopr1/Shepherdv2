import spidev
import gpiod
import time

# Pin definitions (BCM)
PIN_CS = 21
PIN_RESET = 22
PIN_BUSY = 23

# Open GPIO chip
chip = gpiod.Chip('gpiochip4')

cs = chip.get_line(PIN_CS)
reset = chip.get_line(PIN_RESET)
busy = chip.get_line(PIN_BUSY)

cs.request(consumer="lora", type=gpiod.LINE_REQ_DIR_OUT, default_val=1)
reset.request(consumer="lora", type=gpiod.LINE_REQ_DIR_OUT, default_val=1)
busy.request(consumer="lora", type=gpiod.LINE_REQ_DIR_IN)

# SPI setup
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 2000000
spi.mode = 0

# Reset the module
reset.set_value(0)
time.sleep(0.01)
reset.set_value(1)
time.sleep(0.01)

# Wait for busy to go low
timeout = 100
while busy.get_value() == 1 and timeout > 0:
    time.sleep(0.001)
    timeout -= 1

if timeout == 0:
    print("FAIL: Module stuck in BUSY state")
else:
    # Send GetStatus command (0xC0)
    cs.set_value(0)
    result = spi.xfer2([0xC0, 0x00])
    cs.set_value(1)
    
    print(f"Response: {hex(result[1])}")
    print("SUCCESS: SX1262 is responding!")

spi.close()
