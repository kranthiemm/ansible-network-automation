# Ansible Network Automation

Ansible playbooks for network device automation - fact gathering, status
checks, and discovery - built and version-controlled incrementally, with
a GitHub Actions CI/CD pipeline in progress.

## Structure
- `inventory/` — device inventory (static + dynamic)
- `playbooks/` — example playbooks
- `playbooks/templates/` — Jinja2 templates used by playbooks
- `roles/` — reusable roles
- `ansible.cfg` — project config
- `requirements.yml` — pinned collection dependencies
- `.github/workflows/` — CI/CD pipeline definitions

## Playbooks

### 01_gather_facts_prod.yml
Connects to all devices in the `cisco_ios` inventory group, pulls key facts
(hostname, model, IOS version, serial, interfaces), saves a timestamped
snapshot per device to `outputs/facts/`, and prints a summary. Includes
retry logic for transient connection issues and a sanity check on the
returned data.

### 02_interface_status.yml
Connects to all devices in the `cisco_ios` inventory group, executes
`show ip interface brief` and `show version` via `ios_command`, stores the
output, and displays it.

### 03_cdp_neighborss.yml
Runs `show cdp neighbors detail` via `ios_command` and parses the raw output
into a clean list of neighbor Device ID + IP address pairs, using a single
regex capture (two capture groups per match) instead of separate lists +
`zip`. Includes an `assert` check confirming at least one neighbor was
actually parsed, rather than silently showing an empty result.

### 04_vlan_summary.yml
Runs `show vlan brief` via `ios_command` and parses the output into VLAN ID +
Name pairs using a single regex with `multiline=True`, following the same
no-`zip` pattern as `03_cdp_neighborss.yml`. Includes an `assert` check
confirming at least one VLAN was parsed.

### 05_device_audit.yml
A combined entry point that chains the four checks above in sequence via
`import_playbook` — facts, interface status, CDP neighbors, VLAN summary —
so the full audit suite can be run with a single command instead of four.

### 06_precedence_check.yml
Demonstrates Ansible's variable precedence hierarchy using an `ntp_server`
example defined at three levels (`group_vars/all.yml`, `group_vars/cisco_ios.yml`,
`inventory/host_vars/R1.yml`) plus a runtime `-e` extra-var override. No
device connection required - purely resolves variables on the controller
to reveal which definition wins.

### 07_render_interface_report.yml
Renders a markdown interface status report using the `template` module and
a Jinja2 template (`playbooks/templates/interface_report.j2`). Loops over
`ansible_net_interfaces` from `ios_facts` to build a status table, and uses
an `{% if %}` conditional to generate a separate "Interfaces Down" section
that only populates when something is actually down.

### 08_critical_interface_check.yml
Loops over a list of "critical" interfaces (`GigabitEthernet1`, `Loopback0`)
and checks each one's operational status against `ios_facts` data. Uses
`when: item in facts_result...` to safely skip any interface name that
doesn't exist on the device (avoiding a crash), and `assert` to fail loudly
with a clear message if a critical interface is actually down.

### 09_loop_patterns.yml
Demonstrates advanced loop patterns beyond basic `loop:` usage: `index_var`
for numbered output, `loop_control: label` for clean task-header display
when looping over complex dicts, and `dict2items` to build a filtered
"down interfaces" list. The list is explicitly initialized with an empty
`set_fact` *before* the loop — a `default([])` filter inline inside the
loop's own task isn't enough, since that task never runs at all if every
interface is up (the condition is false for every iteration), leaving the
variable genuinely undefined rather than merely empty.

### 10_facts_audit_role.yml + roles/facts_audit
Converts the facts-gathering logic into a reusable role instead of a
standalone playbook. `tasks/main.yml` holds the fixed logic (gather, check,
archive, display); `defaults/main.yml` holds overridable settings
(`gather_subset`, output directory) that any calling playbook can override
via `vars:` without touching the role itself. The calling playbook itself
is now just a few lines - all real logic lives in the role.

### 11_block_rescue_demo.yml
Demonstrates `block`/`rescue`/`always` error handling - fundamentally
different from `retries`/`until` (which repeats the same action hoping it
eventually succeeds). Attempts to gather facts inside a `block:`; if any
task in the block fails, execution stops immediately and jumps to
`rescue:` to run a fallback connectivity check instead. `always:` runs
regardless of which path was taken, used here to log that the check was
attempted either way.

### 12_tagged_audit.yml
Splits a multi-section audit (facts, interfaces, CDP) into tagged groups,
demonstrating `--tags` (run only a specific section), `--skip-tags` (run
everything except one section), and `--list-tags` (preview available tags
without running anything). A task can carry multiple tags at once (the CDP
section is tagged both `cdp` and `slow`). Each tagged group is kept
self-contained - no task depends on a variable from a task that might be
skipped independently.

### inventory/dynamic/dynamic_inventory.py
A dynamic inventory script - reads device data from `devices.csv` and
outputs Ansible's expected JSON inventory format (`_meta.hostvars` +
group-to-hosts mapping). Demonstrates the core dynamic inventory contract:
any executable that prints this JSON shape when run counts as a valid
inventory source, regardless of what it reads from internally (a file, an
API, a database). Secrets are deliberately kept OUT of the script - a
symlinked `group_vars` folder (`inventory/dynamic/group_vars ->
../group_vars`) lets Ansible's normal vault-encrypted group_vars loading
work the same way it does for the static inventory, avoiding
duplicated/hardcoded credentials inside the inventory script itself.

## Collections & Dependencies
Collections are pinned via `requirements.yml` (not left to whatever happens
to be globally installed) and installed into a project-local
`./collections` folder via `ansible.cfg`'s `collections_path` setting -
keeps the project self-contained and reproducible, rather than depending on
a machine-wide `~/.ansible/collections` default. Modules use fully-
qualified names (`cisco.ios.ios_facts`, `ansible.builtin.*`) throughout,
removing ambiguity about which collection a module comes from.

## Linting & Check Mode
`yamllint` and `ansible-lint` are run across the whole repo, not just
individual files. `.yamllint` overrides the `truthy` rule to allow
`yes`/`no` (used throughout for `gather_facts: no`). The entire repo
(`playbooks/`, `roles/`, `inventory/`) passes `ansible-lint` at its
strictest `production` profile with zero findings - FQCN on every module,
consistent task naming, explicit `mode:` on all file/copy operations, clean
Jinja2 spacing, and valid role metadata throughout.

`--check --diff` is used as a dry-run safety habit before real changes: it
computes and displays the full proposed output without actually writing
anything to disk - the same mechanism the CI/CD pipeline uses as a dry-run
gate before any real deploy.

## CI/CD Pipeline

### .github/workflows/syntax-check.yml
First GitHub Actions workflow - triggers on every push/PR to `main`, spins
up a fresh Ubuntu runner, installs Ansible + the `cisco.ios` collection
(via `requirements.yml`), then runs `--syntax-check` against every playbook
in the repo. Uses a placeholder `.vault_pass` file since `ansible.cfg`'s
`vault_password_file` setting makes Ansible look for it unconditionally,
even for syntax-only checks that never decrypt real data - the real vault
password doesn't reach CI until GitHub Secrets are wired up. Hosted on
GitHub's own runner (not self-hosted), so it validates structure only - it
has no network path to reach the lab device.

## Releases
See the [Releases](https://github.com/kranthiemm/ansible-network-automation/releases)
page for version history and changelogs.

## Known Issues
- `02_interface_status.yml` assumes privileged mode is not required - some
  commands may need enable access on other devices.
- `cisco.ios` 11.6.0 shows warnings about not supporting ansible-core
  2.15.13 (the installed version). Still functions correctly in practice,
  but `requirements.yml` should probably be tightened to
  `>=5.0.0,<11.0.0` to avoid the warning on fresh installs.
- The CI/CD pipeline currently only covers syntax-checking (hosted runner).
  Stages requiring device access (check-mode, deploy) need either a
  self-hosted runner or confirmation the hosted runner can reach the lab
  device's public IP directly - pending internal IT review before
  proceeding.