# mypyのbugでloggingの型がうまく読み込めないので、それぞれをimportしている
from logging import DEBUG, INFO, Formatter, Logger, StreamHandler, getLogger


def get_logger(name: str = "") -> Logger:
    logger = getLogger(name)
    logger.setLevel(DEBUG)

    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    console_handler = StreamHandler()
    console_handler.setLevel(INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)

    return logger
