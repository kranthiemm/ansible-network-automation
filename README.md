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
- `02_interface_status.yml` assumes privileged mode is not required - some 
commands may need enable access on other devices.

### 04_vlan_summary.yml
Runs `show vlan brief` via `ios_command` and parses the output into VLAN ID +
Name pairs using a single regex with `multiline=True`, following the same
no-`zip` pattern from Day 4. Includes an `assert` check confirming at least
one VLAN was parsed.

## Releases
See the [Releases](https://github.com/kranthiemm/ansible-network-automation/releases) 
page for version history and changelogs.

### 06_precedence_check.yml
Demonstrates Ansible's variable precedence hierarchy using an `ntp_server`
example defined at three levels (`group_vars/all.yml`, `group_vars/cisco_ios.yml`,
`inventory/host_vars/R1.yml`) plus a runtime `-e` extra-var override. No
device connection required - purely resolves variables on the controller
to reveal which definition wins.

### 07_render_interface_report.yml
Renders a markdown interface status report using the `template` module and
a Jinja2 template (`templates/interface_report.j2`). Loops over
`ansible_net_interfaces` from `ios_facts` to build a status table, and uses
an `{% if %}` conditional to generate a separate "Interfaces Down" section
that only populates when something is actually down.

### 08_critical_interface_check.yml
Loops over a list of "critical" interfaces (`GigabitEthernet1`, `Loopback0`)
and checks each one's operational status against `ios_facts` data. Uses
`when: item in facts_result...` to safely skip any interface name that
doesn't exist on the device (avoiding a crash), and `assert` to fail loudly
with a clear message if a critical interface is actually down.

### 09_loop_interfaces.yml
Demonstrates advanced loop patterns beyond basic `loop:` usage: `index_var`
for numbered output, `loop_control: label` for clean task-header display
when looping over complex dicts, and `dict2items` + `default([])` to build
a filtered "down interfaces" list by appending matching items one at a time
across loop iterations - the step-by-step equivalent of a single-line
`selectattr`/`map` filter chain.

### 10_facts_audit_role.yml + roles/facts_audit
Converts the facts-gathering logic into a reusable role instead of a
standalone playbook. `tasks/main.yml` holds the fixed logic (gather, check,
archive, display); `defaults/main.yml` holds overridable settings
(`gather_subset`, output directory) that any calling playbook can override
via `vars:` without touching the role itself. The calling playbook itself
is now just a few lines - all real logic lives in the role.

## Known Issues
As of Day 15, `inventory/group_vars/cisco_ios.yml`'s vault password and
  `.vault_pass` may be out of sync after rekey practice - results in
  "Decryption failed" on playbooks using `cisco_ios` group vars without
  `--ask-vault-pass`. Needs regenerating `ansible_password` to match
  whichever password `.vault_pass` currently holds.

### 11_block_rescue_demo.yml
Demonstrates `block`/`rescue`/`always` error handling - fundamentally
different from `retries`/`until` (which repeats the same action hoping it
eventually succeeds). Attempts to gather facts inside a `block:`; if any
task in the block fails, execution stops immediately and jumps to
`rescue:` to run a fallback connectivity check instead. `always:` runs
regardless of which path was taken, used here to log that the check was
attempted either way.