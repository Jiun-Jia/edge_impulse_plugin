import logging
from colorama import Fore
from .utils import init_logger

system_logger = init_logger("System", Fore.GREEN, logging.INFO)
router_logger = init_logger("Router", Fore.CYAN, logging.DEBUG)
worker_logger = init_logger("Worker", Fore.MAGENTA, logging.INFO)
