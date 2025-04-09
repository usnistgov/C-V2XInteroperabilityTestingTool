# Testing tool for Commsignia OBU and RSU

import argparse
import datetime
from fabric import ThreadingGroup as Group
from fabric.exceptions import GroupException
from invoke.exceptions import CommandTimedOut


# Devices under test (DUTs)
hosts = {
    "192.168.0.74": "ob4",
    "192.168.0.64": "rs4",
}


def print_exit_status(results) -> None:
    for conn, res in results.items():
        status = f"Error {res.exited}" if res.exited else "OK"
        print(f"*** {hosts[conn.host]} --> {status}")


def print_progress(i: int, msg: str) -> None:
    print(f"\n[{i+1}/{args.repeat}] {msg}...")


def positive_int(arg):
    value = int(arg)
    if value <= 0:
        raise TypeError
    return value


parser = argparse.ArgumentParser(description="Testing tool for Commsignia OBU and RSU")
parser.add_argument("-o", "--obu", action="extend", nargs="+", default=[], help="OBUs to test")
parser.add_argument("-r", "--rsu", action="extend", nargs="+", default=[], help="RSUs to test")
parser.add_argument("-n", "--repeat", type=positive_int, default=1,
                    help="how many times to repeat the test (default: %(default)s)")
parser.add_argument("-t", "--duration", type=positive_int, default=60,
                    help="duration of each test repetition, in seconds (default: %(default)s)")
parser.add_argument("-u", "--user", default="root",
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

results = all_devs.run("commsignia-device-info", in_stream=False)
print_exit_status(results)
print()
# muci always exits with status 1 for some reason
# results = all_devs.run("muci its get capture", in_stream=False, warn=True)
# print_exit_status(results)
# print()

for i in range(args.repeat):
    print_progress(i, f"Running test for {args.duration} seconds")
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"c2p_{timestamp}.pcap"
    try:
        results = all_devs.run(
            f"tcpdump -pi lo -w /tmp/{filename} port 7943",
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
    print(f"  {filename}")
    for conn in all_devs:
        conn.get(
            f"/tmp/{filename}",
            local=f"{args.directory}/{hosts[conn.host]}_{timestamp}",
            preserve_mode=False,
        )
