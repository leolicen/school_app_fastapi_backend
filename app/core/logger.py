import logging
import sys
import os

        


def setup_logging() -> logging.Logger:
    
    # extract .env variable LOG_LEVEL (default INFO)
    log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # extract logging.INFO (default case) value which is an int
    log_level = getattr(logging, log_level_str, logging.INFO)
    
    # get root logger
    logger: logging.Logger = logging.getLogger()
    
    # remove preexisting Python/Uvicorn/FastAPI handlers + handlers cleanup when function called more than once (to avoid log duplicates)
    if logger.handlers:
        logger.handlers.clear()

    # stop log propagation towards parent loggers => only my handlers are showing logs 
    logger.propagate = False
    
    # set logger level dynamically
    logger.setLevel(log_level)

    # create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
        datefmt="%Y-%m-%d %H:%M:%S"
        )

    # -- CREATE HANDLERS --
    
    # Handler 1 => DEBUG/INFO (stdout) => shows only DEBUG/INFO level logs, because we have a second handler for higher levels
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.DEBUG) # if .env LOG_LEVEL == INFO, it logs only INFO, otherwise DEBUG & INFO
    stdout_handler.setFormatter(formatter)
    # custom filter to avoid the 2 handlers to log the same records whenever the level is >= warning
    stdout_handler.addFilter(lambda record: record.levelno <= logging.INFO) # without filter it would log everything from INFO and up
     
    
    # Handler 2 => WARNING > (stderr) => shows logs from WARNING and up 
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.WARNING)
    stderr_handler.setFormatter(formatter)
   


    # add handlers
    logger.addHandler(stdout_handler)
    logger.addHandler(stderr_handler)
    
    return logger

