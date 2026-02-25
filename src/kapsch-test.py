# Testing tool for Kapsch OBU and RSU

import argparse
import datetime
import os
from fabric import ThreadingGroup as Group
from fabric.exceptions import GroupException
from invoke.exceptions import CommandTimedOut


# Devices under test (DUTs)
# Hardcoded for now to simplify testing
hosts = {
    "192.168.0.40": "rsu5",
}


def print_exit_status(results) -> None:
    for conn, res in results.items():
        status = f"Error {res.exited}" if res.exited else "OK"
        print(f"*** {hosts[conn.host]} --> {status}")


def print_progress(i: int, msg: str) -> None:
    print(f"\n[{i+1}/{args.repeat}] {msg}...")


def scp_progress(filename: bytes | str, size: int, sent: int, peername: tuple[str, int]) -> None:
    if isinstance(filename, bytes):
        filename = filename.decode(errors="replace")
    ratio = float(sent) / float(size)
    print(f"  {filename} from {peername[0]} ==> {ratio:6.1%}")


def positive_int(arg) -> int:
    value = int(arg)
    if value <= 0:
        raise TypeError
    return value


parser = argparse.ArgumentParser(description="Testing tool for Kapsch OBU and RSU")
parser.add_argument("-o", "--obu", action="extend", nargs="+", default=[], help="OBUs to test")
parser.add_argument("-r", "--rsu", action="extend", nargs="+", default=[], help="RSUs to test")
parser.add_argument("-n", "--repeat", type=positive_int, default=1,
                    help="how many times to repeat the test (default: %(default)s)")
parser.add_argument("-t", "--duration", type=positive_int, default=60,
                    help="duration of each test repetition, in seconds (default: %(default)s)")
parser.add_argument("-u", "--user", default="admin",
                    help="username for device login (default: %(default)s)")
parser.add_argument("-c", "--no-copy", action="store_true",
                    help="skip copying the test results to the local machine")
parser.add_argument("-d", "--directory", default="results",
                    help="name of the local directory where to store the test results (default: %(default)s)")
args = parser.parse_args()

if not args.obu and not args.rsu:
    parser.error("error: you must specify at least one OBU (-o/--obu) or one RSU (-r/--rsu)")
if not args.directory:
    args.directory = "."

obus = Group(*[host for host, name in hosts.items() if name in args.obu], user=args.user)
print("OBUs:", obus)
rsus = Group(*[host for host, name in hosts.items() if name in args.rsu], user=args.user)
print("RSUs:", rsus)
print()
if not obus and not rsus:
    parser.exit(message="No known devices selected, exiting.\n")
all_devs = Group.from_connections(obus + rsus)

for i in range(args.repeat):
    print_progress(i, f"Running test for {args.duration} seconds")
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"kap_{timestamp}.pcap"
    try:
        results = all_devs.sudo(
            f"tcpdump -i rmnet_data1 -w /tmp/{filename}",
            hide=True,
            in_stream=False,
            timeout=args.duration)
    except GroupException as e:
        for conn, res in e.result.items():
            status = "OK" if isinstance(res, CommandTimedOut) else str(res)
            print(f"*** {hosts[conn.host]} --> {status}")

    if args.no_copy:
        continue

    print_progress(i, "Transferring files")
    from scp import SCPClient
    for conn in all_devs:
        local_path = f"{args.directory}/{timestamp}/{hosts[conn.host]}"
        os.makedirs(local_path, exist_ok=True)
        with SCPClient(conn.transport, progress4=scp_progress) as client:
            client.get(f"/tmp/{filename}", local_path=local_path)
