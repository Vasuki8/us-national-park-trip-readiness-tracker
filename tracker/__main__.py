"""Retired direct-write collector; use private staging and reviewed promotion."""
import sys


def main(argv: list[str] | None = None) -> int:
    # Deliberately do not parse old arguments, read keys or access destinations.
    # Forwarding them could authorize live collection or bypass paired history.
    print('Direct-write collection is retired. Use python -m tracker.stage '
          'with an explicit private staging directory; follow the collection '
          'runbook and reviewed promotion before changing public site data.',
          file=sys.stderr)
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
