#
# Donnie V Savage | Copyright (C) 2025
# Free to use - no copyrights
#
import os
import sys
import logging

# Debugging functions
# =======================================================================

# Logging Variables
file_fmt = "%(asctime)s - %(levelname)s - %(message)s"
console_fmt = "%(levelname)s: %(message)s"

DEBUG    = 'DEBUG'
INFO     = 'INFO'
WARNING  = 'WARNING'
ERROR    = 'ERROR'
CRITICAL = 'CRITICAL'

# Log level mapping to standard Python logging levels
log_levels = {
    DEBUG:    logging.DEBUG,
    INFO:     logging.INFO,
    WARNING:  logging.WARNING,
    ERROR:    logging.ERROR,
    CRITICAL: logging.CRITICAL
}

# ------------------------------------------------------------------------------
# Initialize Logger
# ------------------------------------------------------------------------------
def logger_init(logpath, logfile, level=INFO):
    # Check if the specified log level is valid
    #   CRITICAL: Indicates a very serious error, typically leading to program termination.
    #   ERROR:    Indicates an error that caused the program to fail to perform a specific function.
    #   WARNING:  Indicates a warning that something unexpected happened
    #   INFO:     Provides confirmation that things are working as expected
    #   DEBUG:    Provides info useful for diagnosing problems
    if level not in log_levels:
        print("Invalid log level. Please use one of: DEBUG, INFO, WARNING, ERROR, CRITICAL")
        sys.exit(1)

    os.makedirs(logpath, exist_ok=True)

    log_file = os.path.join(logpath, logfile)
    if os.path.exists(log_file):
        os.remove(log_file)

    # File handler with timestamp
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(file_fmt))

    # Console handler without timestamp
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_levels[level])

    # Small inline filter that drops INFO records
    console_handler.addFilter(lambda record: record.levelno != logging.INFO)
    console_handler.setFormatter(logging.Formatter(console_fmt))
    
    # Attach both handlers
    logging.basicConfig(level=logging.DEBUG, handlers=[file_handler, console_handler])

# ------------------------------------------------------------------------------
# Logger helper to log messages based on custom string level
# ------------------------------------------------------------------------------
def logger(msg_level, *args, **kwargs):
    # Join the arguments into a single string, just like print does
    end = kwargs.pop('end', '\n')
    message = ' '.join(map(str, args))

    # Get the logging level based on the custom log level
    logging_value = log_levels.get(msg_level)
    if logging_value is None:
        raise ValueError(f"Invalid log level: {msg_level}")

    # Log the message using the root logger
    logging.getLogger().log(logging_value, message)

    # For INFO, echo to stdout with print()
    if logging_value == logging.INFO:
        print(message, end=end)
