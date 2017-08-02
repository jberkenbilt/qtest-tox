from . import ddb


def main():
    try:
        ddb.MainClass().main()
    except KeyboardInterrupt:
        exit(130)
