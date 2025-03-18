import datetime
import time

from fabric import ThreadingGroup as Group


user = "user"
hosts = {
    "fe80::6e5:48ff:fe50:c78": "obu1",
    "fe80::6e5:48ff:fe50:cb8": "obu2",
    "fe80::6e5:48ff:fe30:710": "rsu",
}
exp_duration = 5 * 60
num_runs = 5
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


def print_exit_status(results):
    for conn, res in results.items():
        status = f"Error {res.exited}" if res.exited else "OK"
        print(f"*** {hosts[conn.host]} --> {status}")


obus = Group(*[host for host, name in hosts.items() if name.startswith("obu")], user=user)
rsus = Group(*[host for host, name in hosts.items() if name.startswith("rsu")], user=user)

timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
results = obus.sudo("cv2x_get_status", in_stream=False)
results |= rsus.sudo("cv2x_get_status", in_stream=False)
print_exit_status(results)

for i in range(num_runs):
    print(f"\n[{i}] Starting experiment ...")
    results = obus.sudo(f"{binary} start obu", in_stream=False)
    results |= rsus.sudo(f"{binary} start rsu", in_stream=False)
    print_exit_status(results)

    print(f"\n[{i}] Waiting {exp_duration} seconds ...")
    time.sleep(exp_duration)

    print(f"\n[{i}] Stopping experiment ...")
    results = rsus.sudo(f"{binary} stop rsu", in_stream=False)
    results |= obus.sudo(f"{binary} stop obu", in_stream=False)
    print_exit_status(results)

    print(f"\n[{i}] Transferring files ...")
    for f in files_to_copy:
        print(f"  {f}")
        for conn in obus + rsus:
            conn.get(
                f"/tmp/log/current/{f}",
                local=f"results/{timestamp}/{i}/{hosts[conn.host]}/{f}",
                preserve_mode=False,
            )
        # res = obus.get(f"/tmp/log/current/{f}", preserve_mode=False)
        # res = rsus.get(f"/tmp/log/current/{f}", preserve_mode=False)
        # print([(r.remote, r.local) for r in res.values()])
