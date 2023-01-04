import sys
import logging
import time


def main():
    try:
        logging.info("Start")
        time.sleep(5)
        print(1 / 0)
    except Exception as e:
        logging.error(f"Exception: {e}", exc_info=True)
    finally:
        logging.info("End")


def exception_hook(exc_type, exc_value, exc_traceback):
    logging.critical(
        f"Uncaught exception: {exc_value}",
        exc_info=(exc_type, exc_value, exc_traceback),
    )


if __name__ == "__main__":
    sys.excepthook = exception_hook
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-6s: (%(name)-5s) -  %(message)s",
        datefmt="%H:%M:%S",
    )
    main()
