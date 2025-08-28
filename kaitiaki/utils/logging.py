import logging

def setup_logger(name="kaitiaki", level=logging.INFO):
    logger = logging.getLogger(name)
    if not logger.handlers:
        h = logging.StreamHandler()
        fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        h.setFormatter(fmt)
        logger.addHandler(h)
    logger.setLevel(level)
    return logger

logger = setup_logger()