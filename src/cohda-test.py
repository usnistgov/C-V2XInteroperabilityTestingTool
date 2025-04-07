# Testing tool for Cohda MK6 OBU and RSU

import argparse
import datetime
import time
from fabric import ThreadingGroup as Group


# Devices under test (DUTs)
hosts = {
    "fe80::6e5:48ff:fe50:c78": "obu1",
    "fe80::6e5:48ff:fe50:cb8": "obu2",
    "fe80::6e5:48ff:fe30:710": "rsu1",
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


parser = argparse.ArgumentParser(description="Testing tool for Cohda MK6 OBU and RSU")
parser.add_argument("-o", "--obu", action="extend", nargs="+", default=[], help="OBUs to test")
parser.add_argument("-r", "--rsu", action="extend", nargs="+", default=[], help="RSUs to test")
parser.add_argument("-n", "--repeat", type=positive_int, default=1,
                    help="how many times to repeat the test (default: %(default)s)")
parser.add_argument("-t", "--duration", type=positive_int, default=60,
                    help="duration of each test repetition, in seconds (default: %(default)s)")
parser.add_argument("-u", "--user", default="user",
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

timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
results = obus.sudo("cv2x_get_status", in_stream=False)
results |= rsus.sudo("cv2x_get_status", in_stream=False)
print_exit_status(results)

binary = "/mnt/rw/example1609/rc.example1609"
files_to_copy = frozenset(
    (
        "cfg",
        "conf.all",
        "conf.diff",
        "config.gz",
        "gps.pcap",
        "info",
        "rx.pcap",
        "rx_pc5.pcap",
        "stderr",
        "stdout",
        "tx.pcap",
        "tx_pc5.pcap",
    )
)

for i in range(args.repeat):
    print_progress(i, "Starting test")
    results = obus.sudo(f"{binary} start obu", in_stream=False)
    results |= rsus.sudo(f"{binary} start rsu", in_stream=False)
    print_exit_status(results)

    print_progress(i, f"Waiting {args.duration} seconds")
    time.sleep(args.duration)

    print_progress(i, "Stopping test")
    results = rsus.sudo(f"{binary} stop rsu", in_stream=False)
    results |= obus.sudo(f"{binary} stop obu", in_stream=False)
    print_exit_status(results)

    if args.no_copy:
        continue

    print_progress(i, "Transferring files")
    for f in files_to_copy:
        print(f"  {f}")
        for conn in obus + rsus:
            conn.get(
                f"/tmp/log/current/{f}",
                local=f"{args.directory}/{timestamp}/{i}/{hosts[conn.host]}/{f}",
                preserve_mode=False,
            )
