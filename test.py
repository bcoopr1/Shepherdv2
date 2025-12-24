import spidev
import gpiod
import time
from gpiod.line import Direction, Value

# Pin definitions (BCM)
PIN_CS = 21
PIN_RESET = 22
PIN_BUSY = 23

# Open GPIO chip and request lines
chip = gpiod.Chip('/dev/gpiochip4')

cs = chip.request_lines(
    consumer="lora",
    config={PIN_CS: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.ACTIVE)}
)

reset = chip.request_lines(
    consumer="lora",
    config={PIN_RESET: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.ACTIVE)}
)

busy = chip.request_lines(
    consumer="lora",
    config={PIN_BUSY: gpiod.LineSettings(direction=Direction.INPUT)}
)

# SPI setup
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 2000000
spi.mode = 0

# Reset the module
reset.set_value(PIN_RESET, Value.INACTIVE)
time.sleep(0.01)
reset.set_value(PIN_RESET, Value.ACTIVE)
time.sleep(0.01)

# Wait for busy to go low
timeout = 100
while busy.get_value(PIN_BUSY) == Value.ACTIVE and timeout > 0:
    time.sleep(0.001)
    timeout -= 1

if timeout == 0:
    print("FAIL: Module stuck in BUSY state")
else:
    # Send GetStatus command (0xC0)
    cs.set_value(PIN_CS, Value.INACTIVE)
    result = spi.xfer2([0xC0, 0x00])
    cs.set_value(PIN_CS, Value.ACTIVE)
    
    print(f"Response: {hex(result[1])}")
    print("SUCCESS: SX1262 is responding!")

spi.close()
