#!/usr/bin/env python3
import csv
import json
import os

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_file = os.path.join(script_dir, "devices.csv")

    hostvars = {}
    hosts = []

    with open(csv_file, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            hostname = row.pop("hostname")
            hosts.append(hostname)
            hostvars[hostname] = row

    inventory = {
        "cisco_ios": {
            "hosts": hosts
        },
        "_meta": {
            "hostvars": hostvars
        }
    }

    print(json.dumps(inventory, indent=2))

if __name__ == "__main__":
    main()
