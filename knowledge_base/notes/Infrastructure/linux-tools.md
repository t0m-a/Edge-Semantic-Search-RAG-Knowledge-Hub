# Linux & Unix Command-Line Tools

> [← Back to Main Index](README.md)

## Table of Contents

- [`sed` — Stream Editor](#sed--stream-editor)
- [`echo` — Print Text & Newlines](#echo--print-text--newlines)
- [`cut` — Extract Columns & Fields](#cut--extract-columns--fields)
- [`grep` — Pattern Searching & Filtering](#grep--pattern-searching--filtering)
  - [Syntax & Main Options](#syntax--main-options)
  - [Practical `grep` Examples](#practical-grep-examples)
  - [Process & Log Filtering with Pipes and SSH](#process--log-filtering-with-pipes-and-ssh)
  - [Detecting Malicious Code & PHP Backdoors with `grep`](#detecting-malicious-code--php-backdoors-with-grep)
- [`find` — Search Files & Directory Trees](#find--search-files--directory-trees)
- [`cron` — Scheduled Tasks](#cron--scheduled-tasks)
- [`set` & `unset` — Shell Options & Variables](#set--unset--shell-options--variables)
  - [`set` Flags](#set-flags)
  - [`set -o` Option Names](#set--o-option-names)
  - [Unsetting Variables (`unset`)](#unsetting-variables-unset)
- [`awk` & `IFS` — Field Processing](#awk--ifs--field-processing)
- [Miscellaneous File & Sync Tools](#miscellaneous-file--sync-tools)
  - [`rename` & `shred`](#rename--shred)
  - [`man -k` — Search Manual Pages](#man--k--search-manual-pages)
  - [`rclone` & `rsync`](#rclone--rsync)

---

## `sed` — Stream Editor

- `^` — Matches the beginning of a line or string.
- `$` — Matches the end of a line or string.

**Replace all whitespace with newlines:**

```bash
sed -e 's/\s\+/\n/g'
```

**Comment out lines:**

```bash
# (1) Comment out all lines containing "192"
sed -e '/192/s/^/#/' file

# (2) Comment out the beginning of every line in a file
sed -e 's/^/#/' file
```

**Basic substitution:**

```bash
# Replace first occurrence of 'a' with 'b' on each line and print to STDOUT
sed 's/a/b/' file

# Remove all occurrences of 'a' globally (/g)
sed 's/a//g' file
```

> **Warning:** Using `sed` with the `-i` (in-place) option modifies the file directly on disk!

```bash
sed -i 's/a//g' file
```

**Pattern match + substitution:**
`/000/` matches lines containing `000`, `s` performs substitution, inserting `#` at the start of the line (`^`):

```bash
sed '/000/s/^/#/' file
```

**Remove or comment out MAC addresses in an interface configuration file:**

```bash
sed -e '/HWADDR=\[0-9][0-9][a-Z][a-Z]:/s///g' interfaces.cfg
echo "HWADDR=00:50:56:9a:54:a3" | sed -e "s/HWADDR=[0-Z:]*//"

# Comment out lines containing HWADDR
sed -e '/HWADD/s/^/#/' interfaces.cfg
```

**Remove commented and empty lines from a configuration file:**

```bash
sed '/^#\|^$/d' apache2.conf
```

---

## `echo` — Print Text & Newlines

Append multiple hostnames to a file with a newline after each item:

```bash
echo -e debsrv01'\n'debsrv02'\n'debsrv03'\n'debsrv04 >> file
```

---

## `cut` — Extract Columns & Fields

`cut` extracts specific character columns or delimited fields from each line of a file.

**Character position mode (`-c`):**

```bash
# Display the first character column of /etc/passwd
cut -c1 /etc/passwd
```

| Option | Meaning |
| :--- | :--- |
| `-c1-5` | Select character columns 1 through 5 |
| `-c14-` | Select from character column 14 to the end of the line |
| `-c1-3,14-18` | Select multiple character column ranges |

**Example — Extracting source IP addresses from `iptables -nvL`:**

```bash
iptables -nvL > file
cat file
# [...]
# 0     0 REJECT     all  --  *      *       47.95.1.0            0.0.0.0/0            reject-with icmp-port-unreachable
# 0     0 REJECT     all  --  *      *       117.81.166.134       0.0.0.0/0            reject-with icmp-port-unreachable
# [...]

cat file | cut -c 48-66 > file2
```

**Field delimiter mode (`-d` and `-f`):**

```bash
# Display the 6th field of /etc/passwd using ':' as the field delimiter
cut -d: -f6 /etc/passwd
```

**Extract client IPs from web server logs:**

```bash
cat /logs/main_access.log.1 \
  | grep -i wp-login.php \
  | grep -v Pingdom \
  | grep -v ciro \
  | grep -v your_ip_address \
  | cut -f 1 -d '-'
```

---

## `grep` — Pattern Searching & Filtering

`grep` searches for a character pattern in one or more text files and prints matching lines. Patterns use Basic Regular Expressions (BRE) by default, or Extended Regular Expressions (ERE) with `-E`.

### Syntax & Main Options

```bash
grep [options] regex [files...]
grep [options] -e regex1 -e regex2 [files...]
grep [options] -f regex_file [files...]
```

| Option | Description |
| :--- | :--- |
| `-c` | Count matching lines |
| `-nc2` | Show line numbers (`-n`) and `2` lines of context (`-C 2`) |
| `-e` | Specify multiple regular expressions |
| `-E` | Use Extended Regular Expressions (ERE) |
| `-f` | Read regular expressions from a file |
| `-F` | Treat pattern as a fixed literal string (do not interpret as regex) |
| `-i` | Case-insensitive search |
| `-l` | Display only the filenames containing a match |
| `-n` | Prefix each matching line with its line number |
| `-q` | Quiet mode (do not write to STDOUT; check exit code `$?`) |
| `-v` | Invert match (select non-matching lines) |
| `-w` | Match whole words only |
| `-x` | Match entire lines only |

### Practical `grep` Examples

**Compare two files (find lines in `bloc.list` that are NOT in `pingdom-ip.list`):**

```bash
grep -v -f pingdom-ip.list bloc.list
grep -v -f pingdom-ip.list bloc.list > tmp
```

**Examples using `depts2012.txt`:**

```bash
# 1. Show line containing 85191
$ grep 85191 depts2012.txt
52      85      85191   3       VENDEE  Vendée

# 2. Extended regex + case-insensitive search
$ grep -E -i '(paris|vosges)' depts2012.txt
75      75056   0       PARIS   Paris
88      88160   4       VOSGES  Vosges

# 3. Show lines NOT starting with the digit 9
$ grep -v '^9' depts2012.txt
REGION  DEP     CHEFLIEU        TNCC    NCC     NCCENR
01      01053   5       AIN     Ain
67      67482   2       BAS-RHIN        Bas-Rhin
68      68066   2       HAUT-RHIN       Haut-Rhin

# 4. Show lines starting with '0' OR ending with 's'
$ grep -e '^0' -e 's$' depts2012.txt
05      05061   4       HAUTES-ALPES    Hautes-Alpes
06      06088   4       ALPES-MARITIMES Alpes-Maritimes
14      14118   2       CALVADOS        Calvados
25      25056   2       DOUBS   Doubs

# 5. Show and number lines starting with 11
$ grep -n '^11' depts2012.txt

# 6. Quiet search (check return code via $?)
$ grep -q '^11' depts2012.txt
$ echo $?
0

# 7. Only show the count of matching lines
$ grep -c -e '^0' -e 's$' depts2012.txt
21

# 8. Exact word match (-w)
$ grep COTE depts2012.txt      # Without -w, both COTE and COTES match:
26      21      21231   3       COTE-D'OR       Côte-d'Or
53      22      22278   4       COTES-D'ARMOR   Côtes-d'Armor

$ grep -w COTE depts2012.txt   # With -w, only exact word COTE matches:
26      21      21231   3       COTE-D'OR       Côte-d'Or

# 9. Fixed string search (do not interpret '..' as regex any-char)
$ grep -F '..' file
..

# 10. Match lines containing only digits
$ grep -E -x '[0-9]+' file     # Using -x (full line)
2
34
$ grep -E '^[0-9]+$' file      # Equivalent using ^ and $ anchors
2
34

# 11. Read patterns from a pattern file ('search')
$ cat search
# Search lines ending with t
t$
# Search lines containing only digits
^[0-9]+$

$ grep -E -f search file
erytert
2
34
546
```

### Process & Log Filtering with Pipes and SSH

Filtering `ps` output (and excluding the `grep` process itself):

```bash
$ ps -ef | grep apache2 | grep -v grep
root       302     1  0 06:18 ?        00:00:00 /usr/sbin/apache2 -k start
www-data   351   302  0 06:18 ?        00:00:00 /usr/sbin/apache2 -k start
www-data   352   302  0 06:18 ?        00:00:00 /usr/sbin/apache2 -k start
```

Log searching locally and over SSH:

```bash
grep -r --color=always ERROR * | egrep --color "11:[0-9]{2}:[0-9]{2}" /var/log/*
grep -iE --color=always "ERROR|failing" /var/log/error.log

# Over SSH
ssh $SERVER 'grep -iE --color=always "ERROR|failing" /var/log/error.log'
ssh $SERVER 'grep -E --color=always "02:[0-9]{2}:[0-9]{2}" /var/log/error.log'

# Timestamp / status patterns
grep "10:[0-9]{2}:[0-9]{2}"
grep "200 [0-9]* -"
```

### Detecting Malicious Code & PHP Backdoors with `grep`

*Source: [InfoSec Institute — Free Detection Tools](http://resources.infosecinstitute.com/free-detection-tools/)*

Backdoor shells commonly use PHP functions like `shell_exec`, `base64_decode`, `eval`, `phpinfo`, `system`, `php_uname`, `chmod`, `fopen`, `fclose`, `readfile`, `edoced_46esab`, and `passthru` to execute arbitrary commands.

**Combined scan:**

```bash
grep -RPn "(passthru|shell_exec|system|base64_decode|fopen|fclose|eval)" html_prod/
grep -Rn "shell *(" /var/www
grep -Rn "tcp *(" /var/www
grep -Rn "system *(" /var/www
```

**Targeted function scans:**

```bash
grep -Rn "shell_exec *(" /var/www
grep -Rn "base64_decode *(" /var/www
grep -Rn "phpinfo *(" /var/www
grep -Rn "system *(" /var/www
grep -Rn "php_uname *(" /var/www
grep -Rn "chmod *(" /var/www
grep -Rn "fopen *(" /var/www
grep -Rn "fclose *(" /var/www
grep -Rn "readfile *(" /var/www
grep -Rn "edoced_46esab *(" /var/www
grep -Rn "eval *(" /var/www
grep -Rn "passthru *(" /var/www
```

---

## `find` — Search Files & Directory Trees

Search for strings inside files across a directory tree:

```bash
find . -type f -exec grep -i "107.168.129.2" {} \;
find . -type f -exec grep -iH "</body>" {} \;   # -H forces grep to show the filename
find / -name "*.txt" -exec grep -i "license" {} \;
find / -name \*.txt
```

**Breakdown of `find . -type f -exec grep STRING {} \;`:**

| Component | Meaning |
| :--- | :--- |
| `find .` | Start searching from the current working directory |
| `-type f` | Search for regular files only |
| `-exec ... \;` | Execute the given command for each matched file (`\;` terminates `-exec`) |
| `grep STRING {}` | Search for `STRING` inside each found file (`{}` is replaced by the filename) |

**Find and delete matched files:**

```bash
find . -type f -name "*.tmp" -delete
```

---

## `cron` — Scheduled Tasks

List and edit crontabs:

```bash
crontab -l
crontab -e
```

**Crontab job definition syntax:**

```text
# .---------------- minute (0 - 59)
# |  .------------- hour (0 - 23)
# |  |  .---------- day of month (1 - 31)
# |  |  |  .------- month (1 - 12) OR jan,feb,mar,apr ...
# |  |  |  |  .---- day of week (0 - 6) (Sunday=0 or 7) OR sun,mon,tue,wed,thu,fri,sat
# |  |  |  |  |
# *  *  *  *  *   user-name  command to be executed
*/30 *  *  *  *   root       /usr/local/bin/checks-all-30-minutes.sh
```

---

## `set` & `unset` — Shell Options & Variables

```text
set [--abefhkmnptuvxBCHP] [-o option-name] [arg ...]
```

`set` changes the value of shell attributes and positional parameters, or displays the names and values of shell variables. Using `+` instead of `-` turns flags off.

### `set` Flags

| Flag | Description |
| :---: | :--- |
| `-a` | Mark variables which are modified or created for export |
| `-b` | Notify of job termination immediately |
| `-e` | Exit immediately if a command exits with a non-zero status |
| `-f` | Disable file name generation (globbing) |
| `-h` | Remember the location of commands as they are looked up |
| `-k` | Place all assignment arguments in the environment for a command, not just those preceding the command name |
| `-m` | Enable job control |
| `-n` | Read commands but do not execute them (syntax check) |
| `-o` | Set the variable corresponding to `option-name` (see table below) |
| `-p` | Privileged mode: enabled when real and effective UIDs do not match; disables `$ENV` processing and importing shell functions |
| `-t` | Exit after reading and executing one command |
| `-u` | Treat unset variables as an error when substituting |
| `-v` | Print shell input lines as they are read |
| `-x` | Print commands and their arguments as they are executed |
| `-B` | Perform brace expansion |
| `-C` | Disallow existing regular files from being overwritten by output redirection |
| `-E` | Inherit the `ERR` trap in shell functions |
| `-H` | Enable `!`-style history substitution (on by default in interactive shells) |
| `-P` | Do not follow symbolic links when executing commands such as `cd` |
| `-T` | Inherit the `DEBUG` trap in shell functions |

### `set -o` Option Names

| Option Name | Equivalent Flag / Behavior |
| :--- | :--- |
| `allexport` | Same as `-a` |
| `braceexpand` | Same as `-B` |
| `emacs` | Use an Emacs-style line editing interface |
| `errexit` | Same as `-e` |
| `errtrace` | Same as `-E` |
| `functrace` | Same as `-T` |
| `hashall` | Same as `-h` |
| `histexpand` | Same as `-H` |
| `history` | Enable command history |
| `ignoreeof` | The shell will not exit upon reading `EOF` |
| `interactive-comments` | Allow `#` comments in interactive commands |
| `keyword` | Same as `-k` |
| `monitor` | Same as `-m` |
| `noclobber` | Same as `-C` |
| `noexec` | Same as `-n` |
| `noglob` | Same as `-f` |
| `nolog` | Currently accepted but ignored |
| `notify` | Same as `-b` |
| `nounset` | Same as `-u` |
| `onecmd` | Same as `-t` |
| `physical` | Same as `-P` |
| `pipefail` | Return value of a pipeline is the status of the last command to exit with a non-zero status (or zero if all succeeded) |
| `posix` | Match POSIX standard behavior where Bash defaults differ |
| `privileged` | Same as `-p` |
| `verbose` | Same as `-v` |
| `vi` | Use a `vi`-style line editing interface |
| `xtrace` | Same as `-x` |

### Unsetting Variables (`unset`)

```bash
unset TMOUT

var1=XXXX
echo $var1
unset var1
# var1 is now empty
```

---

## `awk` & `IFS` — Field Processing

**Basic `awk` field extraction:**

```bash
# Format: awk '{print $field_number}'
awk '{print $2}'

# Use custom delimiter '='
var=$(awk -F'=' '{print $2}')

# Top 10 most used commands from shell history
history | awk '{print $2}' | sort | uniq -c | sort -rn | head -10
```

**Passing a shell variable into `awk`:**

```bash
TEST=test
echo "1 2 3" | awk '{print "'"$TEST"'"$1}'
# Output: test1
```

**Changing the Internal Field Separator (`IFS`) to handle spaces in lines or variables:**

```bash
IFS=$'\n'   # Only treat newlines as field separators
# ... process lines ...
unset IFS   # Restore default IFS after processing
```

---

## Miscellaneous File & Sync Tools

### `rename` & `shred`

Rename all `.pdf` files to `.doc` using a substitution rule:

```bash
rename -v 's/\.pdf$/\.doc/' *.pdf
```

Securely overwrite and delete a file with `shred`:

```bash
shred -zvu file.pdf
```

| `shred` Option | Meaning |
| :---: | :--- |
| `-z` | Add a final overwrite with zeros to hide shredding |
| `-u` | Truncate and remove the file after overwriting |
| `-v` | Show progress verbosely |

### `man -k` — Search Manual Pages

Search short descriptions and manual page names for a keyword (regular expression):

```bash
man -k apache
man -k php
```

### `rclone` & `rsync`

**Cloud sync & copy with `rclone`:**

```bash
rclone sync --copy-links DIRECTORY/ google:/DIRECTORY
rclone copy ~/DIRECTORY google:/DIRECTORY/
rclone copy google:DIRECTORY/SUB_DIRECTORY ./
```

**Local / external drive backup with `rsync`:**

```bash
sudo rsync -a --delete-after $HOME/ /media/HDD/
rsync -a --delete-after $HOME /mnt/HDD
```
