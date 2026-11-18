import lgpio
import time
from langchain_core.tools import tool
from utils.logger import get_logger

logger = get_logger(__name__)

# Servo motor configuration
CHIP = 0
PIN = 4
FREQ = 50  # 50Hz PWM
PERIOD = 1 / FREQ  # 20ms

def set_servo_angle(chip, angle: int) -> None:
    """
    Set servo motor to a specific angle (0-180 degrees).
    
    Args:
        chip: GPIO chip handle
        angle: Angle in degrees (0-180)
    """
    # Map 0–180° → 500–2500 µs
    pulse_us = 500 + (angle / 180) * 2000
    high = pulse_us / 1_000_000.0
    low = PERIOD - high

    # Send ~15 pulses (about 0.3s total at 50Hz)
    for _ in range(15):
        lgpio.gpio_write(chip, PIN, 1)
        time.sleep(high)
        lgpio.gpio_write(chip, PIN, 0)
        time.sleep(low)

@tool
def remove_frontplate() -> str:
    """
    Removes the frontplate by controlling a servo motor.
    The servo moves from 0 degrees to 180 degrees to release the frontplate.
    """
    chip = None
    try:
        logger.info("Starting frontplate removal process...")
        
        # Initialize GPIO
        chip = lgpio.gpiochip_open(CHIP)
        lgpio.gpio_claim_output(chip, PIN)
        
        # Move servo to 0 degrees (closed position)
        logger.info("Moving servo to closed position (0 degrees)...")
        set_servo_angle(chip, 0)
        time.sleep(0.3)
        
        # Move servo to 180 degrees (open position to release frontplate)
        logger.info("Moving servo to open position (180 degrees) to release frontplate...")
        set_servo_angle(chip, 180)
        time.sleep(0.3)
        
        logger.info("Frontplate removal completed successfully")
        return "Frontplate has been successfully removed. The servo motor moved to release the frontplate mechanism."
        
    except Exception as e:
        logger.error(f"Error during frontplate removal: {e}")
        return f"Error removing frontplate: {str(e)}"
    finally:
        # Clean up GPIO
        if chip is not None:
            try:
                lgpio.gpio_write(chip, PIN, 0)
                lgpio.gpiochip_close(chip)
            except Exception as cleanup_error:
                logger.error(f"Error during GPIO cleanup: {cleanup_error}")
