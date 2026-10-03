#!/usr/bin/env python3
import sys
import argparse

from roxint import RoxClient, ProfileCollector, Correlator, Exporter
from roxint.utils import get_logger


def prompt_identifier() -> str:
    try:
        return input("Target: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return ""


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("identifier", nargs="?", default=None)
    parser.add_argument("-o", "--output", default="output")
    parser.add_argument("--no-csv", action="store_true")
    parser.add_argument("--no-summary", action="store_true")
    parser.add_argument("--timeout", type=int, default=25)
    parser.add_argument("--retries", type=int, default=6)
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("-h", "--help", action="store_true")

    args = parser.parse_args()

    if args.help:
        print("Usage: python cli.py <username_or_id> [-o output] [-v]")
        return 0

    identifier = args.identifier or prompt_identifier()
    if not identifier:
        print("No target provided.")
        return 1

    log = get_logger(args.verbose)
    client = RoxClient(timeout=args.timeout, max_retries=args.retries, verbose=args.verbose)
    collector = ProfileCollector(client)

    log.info(f"Resolving target: {identifier}")
    user_id = collector.resolver.username_to_id(identifier)
    if not user_id:
        log.info("Target not found.")
        return 1

    log.info(f"User ID: {user_id}")
    log.info("Collecting friends...")
    friends = collector._social_list(user_id, "friends")
    log.info(f"  -> {len(friends)} friends")

    log.info("Collecting followers...")
    followers = collector._social_list(user_id, "followers")
    log.info(f"  -> {len(followers)} followers")

    log.info("Collecting following...")
    followings = collector._social_list(user_id, "followings")
    log.info(f"  -> {len(followings)} following")

    log.info("Collecting profile data...")
    data = collector.collect_full(user_id)
    if not data:
        log.info("Collection failed.")
        return 1

    data["friends"] = friends
    data["followers"] = followers
    data["followings"] = followings

    log.info("Analyzing correlations...")
    data["correlations"] = Correlator().analyze(data)

    exporter = Exporter(args.output)
    json_path = exporter.write_json(data, user_id)
    log.info(f"JSON        -> {json_path}")

    conn_path = exporter.write_connections(data, user_id)
    log.info(f"Connections -> {conn_path}")

    if not args.no_csv:
        for name, path in exporter.write_csvs(data, user_id).items():
            log.info(f"CSV         -> {path} ({name})")

    if not args.no_summary:
        report_path = exporter.write_report(data, user_id)
        log.info(f"Report      -> {report_path}")

    counts = data.get("counts", {})
    print()
    print(f"Target        : {data.get('username')} ({data.get('id')})")
    print(f"Display Name  : {data.get('display_name')}")
    print(f"Created       : {data.get('created')}")
    print(f"Friends       : {len(friends)}")
    print(f"Followers     : {len(followers)}")
    print(f"Following     : {len(followings)}")
    print(f"Groups        : {len(data.get('groups', []))}")
    print(f"Badges        : {len(data.get('badges', []))}")
    print(f"Created Games : {len(data.get('created_games', []))}")
    print(f"Social Links  : {len(data.get('social_links', []))}")
    print(f"Output        : {args.output}/{user_id}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())