import logging
from rich.logging import RichHandler
from rich.console import Console
from rich.theme import Theme
custom_theme = Theme({
    "logging.level.info": "green", 
    "logging.level.warning": "yellow",
    "logging.level.error": "red",
    "logging.level.debug": "cyan",
})

console = Console(theme=custom_theme)

def get_logger(name: str = None) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        handler = RichHandler(
            rich_tracebacks=True,
            markup=True,
            console=console
        )
        formatter = logging.Formatter(
            "[%(name)s] %(message)s", datefmt="[%X]"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
