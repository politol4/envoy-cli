"""Command-line interface for envoy-cli."""

import sys
import argparse
from pathlib import Path

from envoy_cli.env_file import load_file, save_file
from envoy_cli.vault import Vault
from envoy_cli.remote import RemoteClient, RemoteError
from envoy_cli.sync import SyncManager


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envoy",
        description="Manage and sync .env files securely across environments.",
    )
    parser.add_argument("--vault", default=".envoy_vault", help="Path to local vault file")
    parser.add_argument("--passphrase", required=True, help="Encryption passphrase")

    sub = parser.add_subparsers(dest="command", metavar="COMMAND")

    # set
    p_set = sub.add_parser("set", help="Set a key/value pair in the vault")
    p_set.add_argument("key", help="Variable name")
    p_set.add_argument("value", help="Variable value")

    # get
    p_get = sub.add_parser("get", help="Get a value from the vault")
    p_get.add_argument("key", help="Variable name")

    # delete
    p_del = sub.add_parser("delete", help="Delete a key from the vault")
    p_del.add_argument("key", help="Variable name")

    # list
    sub.add_parser("list", help="List all keys stored in the vault")

    # push
    p_push = sub.add_parser("push", help="Push vault to remote server")
    p_push.add_argument("--url", required=True, help="Remote base URL")
    p_push.add_argument("--token", required=True, help="API token")
    p_push.add_argument("--env", default="production", help="Target environment name")

    # pull
    p_pull = sub.add_parser("pull", help="Pull vault from remote server")
    p_pull.add_argument("--url", required=True, help="Remote base URL")
    p_pull.add_argument("--token", required=True, help="API token")
    p_pull.add_argument("--env", default="production", help="Source environment name")

    # export
    p_export = sub.add_parser("export", help="Export vault contents to a .env file")
    p_export.add_argument("output", nargs="?", default=".env", help="Output file path")

    # import
    p_import = sub.add_parser("import", help="Import a .env file into the vault")
    p_import.add_argument("input", nargs="?", default=".env", help="Input file path")

    return parser


def run(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        sys.exit(0)

    vault = Vault(args.vault, args.passphrase)

    try:
        if args.command == "set":
            vault.set(args.key, args.value)
            print(f"Set {args.key}")

        elif args.command == "get":
            value = vault.get(args.key)
            if value is None:
                print(f"Key '{args.key}' not found.", file=sys.stderr)
                sys.exit(1)
            print(value)

        elif args.command == "delete":
            vault.delete(args.key)
            print(f"Deleted {args.key}")

        elif args.command == "list":
            keys = vault.keys()
            if keys:
                print("\n".join(sorted(keys)))
            else:
                print("(empty vault)")

        elif args.command == "push":
            client = RemoteClient(args.url, args.token)
            manager = SyncManager(vault, client)
            manager.push(args.env)
            print(f"Pushed to {args.env}")

        elif args.command == "pull":
            client = RemoteClient(args.url, args.token)
            manager = SyncManager(vault, client)
            manager.pull(args.env)
            print(f"Pulled from {args.env}")

        elif args.command == "export":
            data = vault.all()
            save_file(args.output, data)
            print(f"Exported {len(data)} variable(s) to {args.output}")

        elif args.command == "import":
            data = load_file(args.input)
            for k, v in data.items():
                vault.set(k, v)
            print(f"Imported {len(data)} variable(s) from {args.input}")

    except RemoteError as exc:
        print(f"Remote error: {exc}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError as exc:
        print(f"File not found: {exc}", file=sys.stderr)
        sys.exit(1)


def main():
    run()


if __name__ == "__main__":
    main()
