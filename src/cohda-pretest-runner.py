# Pretesting tool for Cohda MK6 OBU and RSU

# Check GPS status
# check C-V2X communication status before test C-V2X and collect data
# Hosts could be any one of obu1, obu2 or rsu


# user is pw (user)
user = "user"

# Devices under test (DUTs)
hosts = {
    "fe80::6e5:48ff:fe50:c78": "obu1",
    "fe80::6e5:48ff:fe50:cb8": "obu2",
    "fe80::6e5:48ff:fe30:710": "rsu",
}

# Go to work directory
binary = "/mnt/rw/example1609/rc.example1609"

# Check status of network connections of DUTs
def print_exit_status(results):
    for conn, res in results.items():
        status = f"Error {res.exited}" if res.exited else "OK"
        print(f"*** {hosts[conn.host]} --> {status}")

# Remotely login DUTs (obu1, or obu2, or rsu) with pw ( user)
obus = Group(*[host for host, name in hosts.items() if name.startswith("obu")], user=user)
rsus = Group(*[host for host, name in hosts.items() if name.startswith("rsu")], user=user)

# check GPS signal status of DUTs
results = obus.sudo("kinematics-sample-client -a -n 1", in_stream=False)
results |= rsus.sudo("kinematics-sample-client -a -n 1", in_stream=False)
print_exit_status(results)

# run "cv2x_get_capabilities" and check C-V2X capabilities of DUTs
results = obus.sudo("cv2x_get_capabilities", in_stream=False)
results |= rsus.sudo("cv2x_get_capabilities", in_stream=False)
print_exit_status(results)

# run "cv2x_get_status" and check C-V2X status of each device 
results = obus.sudo("cv2x_get_status", in_stream=False)
results |= rsus.sudo("cv2x_get_status", in_stream=False)
print_exit_status(results)