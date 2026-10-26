# Bash & Shell Scripting

> [← Back to Main Index](README.md)

## Table of Contents

- [The `for` Loop](#the-for-loop)
  - [Simple Usage](#simple-usage)
  - [Docker Image Iteration Example](#docker-image-iteration-example)
  - [Managing Servers with a `for` Loop](#managing-servers-with-a-for-loop)
  - [Managing Data & Files with a `for` Loop](#managing-data--files-with-a-for-loop)
  - [Cluster & Log Automation Loops](#cluster--log-automation-loops)
- [Colors & Text Formatting in Bash](#colors--text-formatting-in-bash)
  - [ANSI Escape Sequences](#ansi-escape-sequences)
  - [Color & Formatting Code Reference](#color--formatting-code-reference)
- [Shell Standard Streams (Inputs & Outputs)](#shell-standard-streams-inputs--outputs)
  - [Redirection Operators](#redirection-operators)
  - [How Stream Redirection Works](#how-stream-redirection-works)
- [Passing Arguments to a Shell Script](#passing-arguments-to-a-shell-script)
  - [Script Debugging](#script-debugging)
  - [Positional Parameters & Special Variables](#positional-parameters--special-variables)
  - [Quoting, Escaping & Exit Codes](#quoting-escaping--exit-codes)
- [Miscellaneous Shell Tips & Utilities](#miscellaneous-shell-tips--utilities)
  - [Word Count (`wc`)](#word-count-wc)
  - [Command Chaining Operators](#command-chaining-operators)
  - [Dates in Bash](#dates-in-bash)
  - [Process Management (`ps`)](#process-management-ps)
  - [WSL (Bash for Windows) Backup Script](#wsl-bash-for-windows-backup-script)
  - [VMware Workstation Auto-Launch Batch](#vmware-workstation-auto-launch-batch)

---

## The `for` Loop

### Simple Usage

Basic syntax:

```bash
for i in $(cmd); do cmd $i; done
```

Iterating over unquoted vs. double-quoted variables:

```bash
TEST="1 2 3"
for i in $TEST; do echo $i; done
# Output:
# 1
# 2
# 3
```

With double quotes (treats the variable as a single item):

```bash
for i in "$TEST"; do echo $i; done
# Output:
# 1 2 3
```

### Docker Image Iteration Example

Given the output of `docker images`:

```text
REPOSITORY              TAG                 IMAGE ID            CREATED             SIZE
php                     fpm                 0a757334c1f6        12 days ago         368MB
mariadb                 latest              4828ff028cad        12 days ago         401MB
phpmyadmin/phpmyadmin   latest              4bdc31ab2ded        13 days ago         164MB
owncloud/server         10.0                06205d21154b        2 weeks ago         782MB
redis                   latest              bfcb1f6df2db        5 weeks ago         107MB
nginx                   latest              ae513a47849c        5 weeks ago         109MB
debian                  latest              8626492fecd3        5 weeks ago         101MB
ubuntu                  latest              452a96d81c30        5 weeks ago         79.6MB
webhippie/mariadb       latest              ca4fdebdc099        8 weeks ago         202MB
webhippie/redis         latest              906a93578062        2 months ago        55MB
```

Extract and loop over all `IMAGE ID` values:

```bash
for i in $(docker images | awk '{print $3}' | grep -v IMAGE); do echo $i; done
```

Output:

```text
0a757334c1f6
4828ff028cad
4bdc31ab2ded
06205d21154b
bfcb1f6df2db
ae513a47849c
8626492fecd3
452a96d81c30
ca4fdebdc099
906a93578062
```

Write each ID to a temporary text file, display it, and remove the file:

```bash
for i in $(docker images | awk '{print $3}' | grep -v IMAGE); do
  echo $i > inTextFile.txt && cat inTextFile.txt && rm -f inTextFile.txt
done
```

### Managing Servers with a `for` Loop

Update remote `/etc/hosts` files with LAN IP mappings and ping them:

```bash
for s in $(cat servers_list | grep servers_prefix); do
  ssh $s 'cat /root/servers_list >> /etc/hosts && export servers=$(cat /etc/hosts | grep 192 | cut -c1-15) && ping -c 2 $servers'
done
```

Manage web services (backend first, then frontend) with a `for` loop:

```bash
services='apache2 nginx' # First the backend server, then the frontend server
for service in $services; do
  /etc/init.d/$service start|stop|status|reload
done
```

Iterate through a server list and append each host's non-loopback IP address to `/root/env_vars`:

```bash
for s in $(cat servers_list); do
  ssh $s 'echo "export eth=$(ifconfig | grep -i "inet addr:" | cut -c21-31 | grep -v "127.0.0.1")" >> /root/env_vars'
done
```

### Managing Data & Files with a `for` Loop

Display all IP addresses returned by `ifconfig`:

```bash
for i in $(ifconfig | grep -i "inet addr:" | awk '{print $2}' | cut -d: -f2); do
  echo $i
done
```

Copy specific numbered files with a loop:

```bash
for f in $(ls filename[0-9]); do cp $f /dir; done
# Or with timestamp and additional commands:
for f in $(ls filename[0-9]); do cp ${f}_$DATE; other_command; another_one; done
```

### Cluster & Log Automation Loops

Install a Docker Compose configuration file hosted in an AWS S3 bucket on every host in a cluster:

```bash
for s in $(cat servers-cluster); do
  ssh -i PRIVATE_KEY_FILE USER_NAME@$s \
    'sudo aws s3 cp s3://S3_BUCKET_NAME/SUB_DIR/DOCKER_FILE.conf /root/SUB_DIR/DOCKER_FILE.conf/'
done
```

Restart `docker-compose` services on every host in a cluster:

```bash
for s in $(cat servers-cluster); do
  ssh -i PRIVATE_KEY_FILE USER_NAME@$s \
    "sudo su -c 'cd /root/SUB_DIR && docker-compose down && docker-compose up -d'"
done
```

Ban offending IPs via `fail2ban-client` based on HTTP access logs (`401` responses or `POST` requests):

```bash
for s in $(cat /logs/main_access.log | grep -i 401 | grep -v Pingdom | cut -f 1 -d '-'); do
  fail2ban-client set wordpress banip $s
done

for s in $(cat /logs/main_access.log | grep POST | grep -v Pingdom | grep -v ciro | cut -f 1 -d '-'); do
  fail2ban-client set wordpress banip $s
done
```

Extract IPs from HTTP logs directly:

```bash
cat /logs/main_access.log | grep -i 401 | grep -v pingdom | cut -f 1 -d '-'
cat main_access.log | grep POST | grep -v ciro | grep -v pingdom | cut -f 1 -d '-'
```

---

## Colors & Text Formatting in Bash

### ANSI Escape Sequences

Color output in Bash is triggered by the escape sequence:

```text
\033[XXm
```

- `XX` is the code for the chosen color or style.
- `0` resets all formatting back to default terminal values (`\033[0m`).

**Background color example:**

```bash
echo -e "\033[45mHello world on pink background\033[0m"
```

**Stacking foreground and background colors:**

```bash
echo -e "\033[34m\033[45mBlue Hello world on pink background\033[0m"
```

> **Tip:** Stacking codes does not require repeating `\033[` for each attribute. You can combine multiple codes in a single sequence separated by semicolons (`;`).

For example, red, bold, underlined, blinking, and reversed text can be written either way:

```bash
# Separate sequences
echo -e "\033[31m\033[1m\033[4m\033[5m\033[7mThe Text\033[0m"

# Combined sequence
echo -e "\033[31;1;4;5;7mThe Text\033[0m"
```

Combining progressive styles in one line:

```bash
echo -e "\033[34mBlue, \033[1mBold, \033[4mUnderlined, \033[5mBlinking \033[7mAnd highlighted\033[0m"
```

### Color & Formatting Code Reference

Codes in the **30s** (`30`–`37`) set **foreground (text)** colors, while codes in the **40s** (`40`–`47`) set **background** colors:

| Color | Foreground (Text) | Background |
| :--- | :---: | :---: |
| **Black** | `30` | `40` |
| **Red** | `31` | `41` |
| **Green** | `32` | `42` |
| **Yellow** | `33` | `43` |
| **Blue** | `34` | `44` |
| **Pink / Magenta** | `35` | `45` |
| **Cyan** | `36` | `46` |
| **Grey / White** | `37` | `47` |

Codes `0`–`7` control **text formatting**:

| Code | Effect |
| :---: | :--- |
| `0` | Reset to default values |
| `1` | **Bold** text |
| `4` | <u>Underlined</u> text |
| `5` | Blinking text |
| `7` | Reverse video / highlighted |

---

## Shell Standard Streams (Inputs & Outputs)

Every Unix process has three standard streams:

| Stream Constant | File Descriptor | Default Device | Description |
| :--- | :---: | :--- | :--- |
| `STDIN` | `0` | Keyboard | Standard Input |
| `STDOUT` | `1` | Screen / File | Standard Output |
| `STDERR` | `2` | Screen / File | Standard Error Output |

### Redirection Operators

- `2>&1` — Redirect `STDERR` (`2`) to wherever `STDOUT` (`1`) is currently directed.
- `2>/dev/null` — Redirect `STDERR` to `/dev/null` (discard error messages).
- `1>/dev/null` (or `>/dev/null`) — Redirect `STDOUT` to `/dev/null` (discard standard output).

### How Stream Redirection Works

- Redirecting output to `/dev/null` with `>` only affects `STDOUT` (`1`), **not** `STDERR` (`2`). Error messages sent to `STDERR` will still appear on the screen (or current log output).
- Specifying `2>/dev/null` redirects **only** `STDERR`.
- Using `2>&1` tells the shell: *"redirect `STDERR` to the same destination as `STDOUT`"*.
  - If `STDOUT` was previously redirected to `/dev/null` (e.g., `cmd >/dev/null 2>&1`), both `STDOUT` and `STDERR` are discarded.
  - Otherwise, `STDERR` will be displayed on screen or written to the file where `STDOUT` is directed.

*Source: [lanterne-rouge.info](http://www.lanterne-rouge.info/article-que-signifie-dev-null-2-1-70233357.html)*

---

## Passing Arguments to a Shell Script

### Script Debugging

```bash
bash -x script.sh
```

Similar to `-v`, but `-x` is more verbose—it expands variables and prints each command before execution, making it ideal for debugging.

### Positional Parameters & Special Variables

| Variable | Description |
| :--- | :--- |
| `$0` | Name of the script itself (useful for `usage` / help messages). |
| `$(basename $0)` or `` `basename $0` `` | Displays only the script filename without the full absolute path. |
| `$1` | First positional argument passed to the script after its name. |
| `${10}` | Positional argument with two or more digits (braces `{}` are required for `$10` and above). |
| `$#` | Argument counter (number of arguments passed). Useful for validating required arguments. |
| `$*` | Refers to all positional arguments passed after the script name. |

### Quoting, Escaping & Exit Codes

- **Single quotes (`'...'`)** protect the entire expression from Bash interpretation, including the `$` variable prefix:
  ```bash
  echo '$1'   # Prints literal: $1
  echo "$1"   # Prints the value stored in $1
  ```
- **Backslash (`\`)** escapes a single character inside double quotes:
  ```bash
  echo "$USER text \$4"   # Prints the value of $USER, followed by literal: text $4
  ```
- **Exit status (`exit`)** should be placed at the end of scripts so callers can verify execution status:
  ```bash
  exit 0   # Exit without error (success)
  exit 1   # Exit with error (failure)
  ```

---

## Miscellaneous Shell Tips & Utilities

### Word Count (`wc`)

| Command / Option | Description |
| :--- | :--- |
| `wc` | Word, line, and byte count |
| `wc -l`, `--lines` | Print newline count |
| `wc -L`, `--max-line-length` | Print maximum display width (longest line) |
| `wc -w` | Print word count |

### Command Chaining Operators

- `cmd1 && cmd2` — Execute `cmd2` **only if `cmd1` exited successfully** (exit code `0`).
- `cmd1 || cmd2` — Execute `cmd2` **only if `cmd1` exited with an error** (non-zero exit code).

### Dates in Bash

Inline date formatting in a command or script:

```bash
`date +%Y%m%d%H%M`
```

Assigning a formatted timestamp to a variable:

```bash
myDateVar=$(date +%Y%m%d%H%M)
echo $myDateVar
# Returns e.g.: 201703251313
```

### Process Management (`ps`)

Filter processes by PID/date and pass to `xargs` (e.g., to kill):

```bash
ps -ef | grep -i "pid" | grep -i "Feb10" | awk '{print $2}' | xargs kill -9
```

Common `ps` invocations:

```bash
ps -aef
ps -ef
ps aux
```

| Flag | Description |
| :--- | :--- |
| `-e` or `-A` | List all active processes |
| `-au` or `aux` | List all processes in BSD format |
| `-ef` or `-eF` | List all processes in full/wide format |
| `-x` | List running processes (including those without a controlling terminal) |

*More details: [Tecmint — `ps` Command Examples for Linux Process Monitoring](https://www.tecmint.com/ps-command-examples-for-linux-process-monitoring/)*

### WSL (Bash for Windows) Backup Script

Script (`tarlxss.sh`) to back up local WSL (`lxss`) directories:

```bash
#!/bin/bash
# tarlxss.sh — script to back up lxss local directories

export myDate=`exec date '+%Y%m%d'`

# Change this line! Probably should be someplace in DrvFS (/mnt/...)
export backdir=/mnt/appropriate/backup/path

# Make sure this command doesn't wrap onto multiple lines without escaping
export TARCMD="/bin/tar --verbose --create --one-file-system --xz --exclude=./var/run --index-file=${backdir}/local-${myDate}.log --file ${backdir}/local-${myDate}.tar.xz"
export XZCMD="/usr/bin/xz"

# /etc contains modified config files and sshd certificates; consider adding ./etc/ssh or ./etc
# Start in the root of the filesystem
cd /
$TARCMD ./home ./root ./usr/local
tarreturn=$?
echo $0: finished, returned $tarreturn >> ${backdir}/local-${myDate}.log

$XZCMD ${backdir}/local-${myDate}.log
xzreturn=$?
echo $0: finished normally, tar with $tarreturn, xz with $xzreturn
```

**Automating via Windows Task Scheduler:**
- **Action:** Start a program
- **Program/script:** `C:\Windows\System32\bash.exe`
- **Add arguments (optional):** `-c 'sudo /path/to/tarlxss.sh'`

### VMware Workstation Auto-Launch Batch

Place a `.bat` file in the Windows Startup folder to automatically start a VMware Workstation VM:

```bat
cd "\Program Files\VMware\VMware Workstation"
vmware -x "C:\My virtual machine\winxppro.vmx"
```

Or using full paths (`-X` launches and enters full-screen mode):

```bat
"C:\Program Files (x86)\VMware\VMware Workstation\vmware.exe" -X "Z:\Virtual Machines\XP_Dev\winXPPro.vmx"
```
