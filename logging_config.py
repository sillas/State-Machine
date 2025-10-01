import logging
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def _i(message: Any) -> None:
    logger.info(message)


def _e(error_message: Any) -> None:
    logger.error(error_message)


def _w(warning_message: Any) -> None:
    logger.warning(warning_message)
