import spidev
import gpiod
import time
from gpiod.line import Direction, Value

PIN_CS = 21
PIN_RESET = 22
PIN_BUSY = 23

chip = gpiod.Chip('/dev/gpiochip4')

cs = chip.request_lines(consumer="lora", config={PIN_CS: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.ACTIVE)})
reset = chip.request_lines(consumer="lora", config={PIN_RESET: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.ACTIVE)})
busy = chip.request_lines(consumer="lora", config={PIN_BUSY: gpiod.LineSettings(direction=Direction.INPUT)})

spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 2000000
spi.mode = 0

def wait_busy():
    while busy.get_value(PIN_BUSY) == Value.ACTIVE:
        time.sleep(0.001)

def spi_command(cmd):
    wait_busy()
    cs.set_value(PIN_CS, Value.INACTIVE)
    result = spi.xfer2(cmd)
    cs.set_value(PIN_CS, Value.ACTIVE)
    return result

def write_register(addr, data):
    spi_command([0x0D, (addr >> 8) & 0xFF, addr & 0xFF] + data)

def read_register(addr, length):
    return spi_command([0x1D, (addr >> 8) & 0xFF, addr & 0xFF, 0x00] + [0x00]*length)[4:]

def reset_module():
    reset.set_value(PIN_RESET, Value.INACTIVE)
    time.sleep(0.01)
    reset.set_value(PIN_RESET, Value.ACTIVE)
    time.sleep(0.01)
    wait_busy()

def setup_radio():
    reset_module()
    spi_command([0x80, 0x00])  # SetStandby STDBY_RC
    time.sleep(0.01)
    spi_command([0x8A, 0x01])  # SetPacketType LoRa
    spi_command([0x86, 0x39, 0x30, 0x00, 0x00])  # SetRfFrequency 915MHz
    spi_command([0x8B, 0x07, 0x04, 0x01, 0x00])  # SetModulationParams SF7, BW125, CR4/5
    spi_command([0x8C, 0x00, 0x08, 0x00, 0x40, 0x00, 0x00, 0x00, 0x00])  # SetPacketParams
    spi_command([0x08, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])  # SetDioIrqParams

print("Setting up radio...")
setup_radio()
print("Base station ready - listening on 915 MHz")

while True:
    # Start RX mode (continuous)
    spi_command([0x82, 0xFF, 0xFF, 0xFF])
    time.sleep(0.1)
    
    # Check IRQ status
    irq = spi_command([0x12, 0x00, 0x00, 0x00])
    irq_status = (irq[2] << 8) | irq[3]
    
    if irq_status & 0x02:  # RxDone
        # Get RX buffer status
        status = spi_command([0x13, 0x00, 0x00, 0x00])
        payload_len = status[2]
        start_ptr = status[3]
        
        # Read the buffer
        data = spi_command([0x1E, start_ptr, 0x00] + [0x00]*payload_len)
        message = bytes(data[3:3+payload_len])
        
        print(f"Received: {message}")
        
        # Clear IRQ
        spi_command([0x02, 0xFF, 0xFF])
