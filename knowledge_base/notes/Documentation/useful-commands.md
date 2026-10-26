# Useful Miscellaneous Commands

> [← Back to Main Index](README.md)

## Table of Contents

- [Network Commands](#network-commands)
- [Network File System (NFS)](#network-file-system-nfs)
- [Monitoring & Log Inspection](#monitoring--log-inspection)
- [System & Service Management](#system--service-management)
- [Miscellaneous CLI Shortcuts & Utilities](#miscellaneous-cli-shortcuts--utilities)
  - [Shell Shortcuts & Navigation](#shell-shortcuts--navigation)
  - [Debian / Ubuntu Package Management](#debian--ubuntu-package-management)
  - [Job Control, System Info & Disk Usage](#job-control-system-info--disk-usage)
  - [File Permissions, Formatting & `screen`](#file-permissions-formatting--screen)
  - [Init Runlevels & Sorting](#init-runlevels--sorting)

---

## Network Commands

**Download / test HTTPS endpoints ignoring certificate checks (`wget` equivalent of `curl -k`):**

```bash
wget https://hostname.fqdn/ --delete-after --no-check-certificate
wget https://10.0.0.20/ --no-check-certificate
```

**Forge HTTP `POST` requests with `curl` for testing:**

```bash
curl -i -X POST -H 'Content-Type: application/json' -d '{"name": "New item", "year": "2009"}' https://domain.com/
curl -i -X POST -H 'Content-Type: application/php' -d '{"name": "wanan.php"}' https://domain.com/
```

**Add a network route:**

```bash
route add default gw {IP-ADDRESS} {INTERFACE-NAME}
ip route add 192.168.1.0/24 via 192.168.1.254
```

**Remotely capture all traffic via `tcpdump` over SSH (excluding SSH port 22):**

```bash
ssh root@HOST -- "tcpdump -w - -s 65535 'not port 22'" > capture.pcap
```

---

## Network File System (NFS)

**Example exports / `/etc/fstab` definitions:**

```text
/mnt/db1      IP_ADDRESS/255.255.255.0(rw,sync)
/mnt/db0      IP_ADDRESS/255.255.255.0(ro,sync)
/mnt/dnbd1    IP_ADDRESS/255.255.255.0(rw,sync)
/mnt/dnbd0    IP_ADDRESS/255.255.255.0(rw,sync)
```

**Manual NFS mount commands:**

```bash
mount -o nolock IP_ADDRESS_NFS_SERVER:/shared/mount/point /LOCAL/MOUNT/POINT

# Examples:
mount -o nolock IP_ADDRESS:/mnt/db1 /srv/db1
mount -o nolock IP_ADDRESS:/mnt/dnbd0 /srv/dnbd0
mount -o nolock IP_ADDRESS:/mnt/dnbd1 /srv/dnbd1
```

---

## Monitoring & Log Inspection

**Watch established connections between two hosts in real time:**

```bash
watch -d -n 3 "netstat -ap | grep `hostname`:4444[1-4] | grep ESTABLISHED"
```

**Watch reverse proxy `access_log` files and process today's logs with `flog`:**
*(Note: `flog` dumps `STDIN` to a file and reopens on `SIGHUP`.)*

```bash
cd /logs && for s in `ls -lrt *_access_log | grep " $(date "+%b %d")" | grep -v servername | awk '{print $9}'`; do flog $s; done
```

**Remote multi-tail on log files with colorization (`ccze`):**

```bash
ssh -i id-do-sfo02 root@web01 -p9922 'tail -F /logs/*.log | ccze -A'
```

**Live log filtering with `tail`, `cat`, `grep`, `awk`, and `cut`:**

```bash
tail -f /logs/access | grep 'string'
tail -f /logs/access | grep -E --color "$string|OtherString|AnotherString"
cat /logs/access | grep -E "string" | tail -1 | awk '{print $3}' | cut -d= -f2
```

**Process limits, open files (`lsof`, `fuser`), and `watch`:**

```text
/proc/$PID/limits
  └── Maximum number of open files and file descriptors for $PID

sysctl /etc/security/limits.conf
lsof   ─┐
        ├── Check which process or user is using a file or remote filesystem
fuser  ─┘
```

```bash
watch -d -n SECONDS "command1 | command2 | ..."
```

---

## System & Service Management

**Manage services via `systemctl`:**

```bash
systemctl list-units --type=service
systemctl is-active service_name.service
```

**Rename a host with `hostnamectl`:**

```bash
hostnamectl set-hostname NEW_NAME_HERE
systemctl restart systemd-logind.service

# One-liner example:
hostnamectl set-hostname debsrv01 && systemctl restart systemd-logind.service
```

**Reconfigure system time zone (Debian / Ubuntu):**

```bash
dpkg-reconfigure tzdata
```

---

## Miscellaneous CLI Shortcuts & Utilities

### Shell Shortcuts & Navigation

| Shortcut / Command | Description |
| :--- | :--- |
| `Ctrl + R` | Reverse search through Bash command history |
| `Ctrl + L` | Clear the terminal screen |
| `Leading space` | Putting a blank space before typing a command in Bash prevents it from being recorded in history |
| `cd -` | Return to the previous working directory |
| `apachectl -t` | Test Apache configuration syntax |
| `chkconfig` / `systemctl` | Manage system services |

### Debian / Ubuntu Package Management

**List all installed packages on a Debian / Ubuntu system:**

```bash
dpkg-query -f '${binary:Package}\n' -W
```

**Remove all packages installed on or after a specific date:**

```bash
grep "2015-12-19.*.install " /var/log/dpkg.log | awk '{ print $4 }' | cut -d: -f1 > file.txt
apt-get remove --purge $(paste -s -d ' ' file.txt)
```

### Job Control, System Info & Disk Usage

| Command | Description |
| :--- | :--- |
| `bg` | Send a suspended job to the background (see also `jobs`) |
| `fg` | Bring a background job to the foreground (see also `jobs`) |
| `free` | Display memory usage |
| `uname` | Display system and kernel information |
| `whereis` | Locate the binary, source, and manual page files for a command |
| `whatis` | Display one-line manual page descriptions |
| `id` / `whoami` | Print current user and group identity |
| `who` | Show who is logged on |
| `w` | Show who is logged on and what they are doing |
| `mtr` | MyTraceRoute — combines `ping` and `traceroute` |
| `nl` | Number lines of files |
| `ss` | Socket statistics (modern replacement for `netstat` with more options and info) |
| `tree` | Display directory contents as a tree (not installed by default on all distros) |
| `pstree` | Display a tree of processes (great when given a specific PID) |
| `tac` | Concatenate and print files in reverse (inverse of `cat`) |
| `less` + `Shift + F` | Follow file changes in real time inside `less` (like `tail -f`) |

**Check human-readable disk usage for the current folder (`--max-depth=1`):**

```bash
du -h --max-depth=1 .
```

**Inspect file type and metadata (`file` and `stat`):**

```bash
file infos.txt && stat infos.txt
```

### File Permissions, Formatting & `screen`

**Copy ownership and permissions from a reference file to other files:**

```bash
chown --reference=reference_file file
chmod --reference=users.list users1.list users2.list users3.list
```

**Format output into aligned columns with `column -t`:**

```bash
mount | column -t
```

**Keep long-running scripts alive with `screen`:**

```bash
# 1. Start the script inside a screen session
screen ./long-unix-script.sh

# 2. Press Ctrl+A then D to detach from the current terminal process

# 3. Re-attach to the running session (PID.pts-DEVICE.hostname)
screen -r 4980.pts-0.localhost
```

### Init Runlevels & Sorting

**Init commands:**
- `init 0` — Halt / shut down immediately
- `init 6` — Reboot gracefully (equivalent to `shutdown -r now`)

**Sorting files (`sort`):**
- `sort -f -b FILE` — Sort file contents ignoring case (`-f`) and leading blanks (`-b`)
- `sort -f -b -o OUTPUT_FILE FILE` — Write sorted output directly to `OUTPUT_FILE`
