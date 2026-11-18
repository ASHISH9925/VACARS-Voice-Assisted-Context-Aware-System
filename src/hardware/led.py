from utils.logger import get_logger

logger = get_logger(__name__)

try:
    from gpiozero import LED, Device
    try:
        from gpiozero.pins.lgpio import LGPIOFactory
        Device.pin_factory = LGPIOFactory()
    except Exception:
        # If lgpio not available, use default pin factory
        pass
except Exception:
    LED = None  # type: ignore

_blue = None


def _ensure_blue_led(pin: int):
    global _blue
    if _blue is None and LED is not None:
        try:
            _blue = LED(pin)
        except Exception as e:
            logger.warning(f"Failed to initialize BLUE LED on GPIO {pin}: {e}")
            _blue = None


def blue_led_on(pin: int) -> None:
    _ensure_blue_led(pin)
    if _blue is not None:
        try:
            _blue.on()
        except Exception as e:
            logger.warning(f"Failed to turn BLUE LED on: {e}")


def blue_led_off() -> None:
    if _blue is not None:
        try:
            _blue.off()
            _blue.close()
        except Exception as e:
            logger.warning(f"Failed to turn BLUE LED off: {e}")
        finally:
            # Ensure we release the reference so the pin can be re-acquired
            globals()["_blue"] = None

