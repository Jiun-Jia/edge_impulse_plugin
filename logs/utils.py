import logging
from logging.handlers import TimedRotatingFileHandler
from colorama import Fore, Style, init

# Initialize colorama (ensures color works on Windows)
init(autoreset=True)


# Define a custom formatter
class CustomFormatter(logging.Formatter):
    """Custom log formatter with colored timestamp and log level, using Colorama."""

    COLOR_MAP = {
        "DEBUG": Fore.CYAN,
        "INFO": Fore.GREEN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "CRITICAL": Fore.RED + Style.BRIGHT,
    }

    def __init__(self, logger_name_color=Fore.BLUE, show_details: bool = True):
        super().__init__()
        self.logger_name_color = logger_name_color
        self.show_details = show_details

    def format(self, record):
        # Apply colors using Colorama
        timestamp = f"{Fore.YELLOW}{self.formatTime(record, '%Y-%m-%d %H:%M:%S')}"
        logger_name = f"{self.logger_name_color}{record.name:15}{Style.RESET_ALL}"
        level_color = self.COLOR_MAP.get(record.levelname, "")
        levelname = f"{level_color}{record.levelname:8}{Style.RESET_ALL}"
        if self.show_details:
            details = f" [{Fore.WHITE}{record.filename}:{record.lineno} {record.funcName}{Style.RESET_ALL}]"
        else:
            details = ""
        # Construct the log message with tabs
        log_msg = f"{timestamp} | {logger_name} | {levelname} | {record.getMessage()}{details}"
        return log_msg


def get_file_formatter():
    """
    創建文件日志格式化器，用於記錄到文件。
    """
    formatter = logging.Formatter(
        "%(asctime)s | %(name)-15s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return formatter


def get_general_handler():
    """
    創建通用日志處理器，按天滾動日志文件。
    """
    general_handler = TimedRotatingFileHandler(
        filename="./logs/general.log",
        when="midnight",  # 每天午夜切分一次
        interval=1,
        backupCount=7,  # 保留最近7天的日志
        encoding="utf-8",
    )
    formatter = get_file_formatter()
    general_handler.setFormatter(formatter)
    general_handler.setLevel(logging.INFO)  # 記錄 INFO 及以上級別日志
    return general_handler


def get_error_handler():
    """
    創建錯誤日志處理器，按天滾動日志文件。
    """
    error_handler = TimedRotatingFileHandler(
        filename="./logs/error.log",
        when="midnight",  # 每天午夜切分一次
        interval=1,
        backupCount=7,  # 保留最近7天的日志
        encoding="utf-8",
    )
    formatter = get_file_formatter()
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)  # 只記錄 ERROR 及以上級別日志
    return error_handler


def get_console_handler(formatter: logging.Formatter):
    """
    創建 Console 日志處理器，用於在終端輸出日志。
    """
    console_handler = logging.StreamHandler()

    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG)  # 記錄所有級別日志
    return console_handler


# Create the handler
general_handler = get_general_handler()
error_handler = get_error_handler()


def init_logger(
    logger_name: str,
    logger_name_color=Fore.BLUE,
    logger_level=logging.DEBUG,
    show_details: bool = True,
):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logger_level)  # Set the logging level

    # Create the formatter
    formatter = CustomFormatter(logger_name_color, show_details)

    # Create the handler
    console_handler = get_console_handler(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(general_handler)
    logger.addHandler(error_handler)

    logger.propagate = False
    logger.info(
        f"Logger '{logger_name}' initialized with level {logging.getLevelName(logger_level)}"
    )
    return logger
