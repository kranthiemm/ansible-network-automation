# Ansible Network Automation

30-day build: one Ansible/Git example per day, each committed and pushed on completion.

## Structure
- `inventory/` — device inventory
- `playbooks/` — daily example playbooks
- `ansible.cfg` — project config

## Playbooks

### 01_gather_facts_prod.yml
Connects to all devices in the `cisco_ios` inventory group, pulls key facts
(hostname, model, IOS version, serial, interfaces), saves a timestamped
snapshot per device to `outputs/facts/`, and prints a summary. Includes
retry logic for transient connection issues and a sanity check on the
returned data.

### 02_interface_status.yml
Connects to all devices in the `cisco_ios` inventory group, execute the commands
in the ios_command module and store the output and another task to display the 
output

### 03_cdp_neighbors.yml
Runs `show cdp neighbors detail` via `ios_command` and parses the raw output
into a clean list of neighbor Device ID + IP address pairs, using a single
regex capture (two capture groups per match) instead of separate lists +
`zip`. Includes an `assert` check confirming at least one neighbor was
actually parsed, rather than silently showing an empty result.
## Known Issues
- `02_interface_status.yml` assumes privileged mode is not required - some commands may need enable access on other devices.
