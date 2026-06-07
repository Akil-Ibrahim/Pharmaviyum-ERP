import sys
from structlog import get_logger, configure, processors, stdlib
import logging


def configure_logging(level: str = "INFO"):
	logging.basicConfig(stream=sys.stdout, level=getattr(logging, level.upper(), logging.INFO))
	configure(
		processors=[
			processors.TimeStamper(fmt="iso"),
			processors.StackInfoRenderer(),
			processors.format_exc_info,
			stdlib.add_log_level,
			processors.JSONRenderer()
		],
		logger_factory=stdlib.LoggerFactory(),
	)


def get_app_logger(name: str = "pharmaviyum"):
	return get_logger(name)
