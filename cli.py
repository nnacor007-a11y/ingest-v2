import argparse
import sys

from ic_v2.ingest_v2.cli_ingest_fact_v2 import build_parser as build_ingest_fact_v2_parser
from ic_v2.ingest_v2.errors import IngestV2Error


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="cli.py")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # V2 command
    build_ingest_fact_v2_parser(subparsers)

    args = parser.parse_args(argv)

    try:
        return args.func(args)
    except IngestV2Error as e:
        sys.stderr.write(str(e) + "\n")
        return getattr(e, "exit_code", 2)
    except Exception:
        sys.stderr.write("Error:Unhandled\n")
        return 10


if __name__ == "__main__":
    raise SystemExit(main())