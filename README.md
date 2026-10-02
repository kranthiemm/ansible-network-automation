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