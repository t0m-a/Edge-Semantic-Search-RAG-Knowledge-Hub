# SSH, DSH, SCP, PTS & TTY

> [← Back to Main Index](README.md)

## Table of Contents

- [SSH (Secure Shell)](#ssh-secure-shell)
  - [Shell vs. Console vs. Terminal (TTY & PTS)](#shell-vs-console-vs-terminal-tty--pts)
  - [SSH Tunneling (Local Port Forwarding)](#ssh-tunneling-local-port-forwarding)
  - [SSH Agent Configuration](#ssh-agent-configuration)
  - [SSH Key Management](#ssh-key-management)
  - [Cluster Execution over SSH](#cluster-execution-over-ssh)
- [DSH (Distributed Shell)](#dsh-distributed-shell)
  - [DSH Options](#dsh-options)
  - [DSH Examples](#dsh-examples)
- [SCP (Secure Copy)](#scp-secure-copy)
  - [SCP Syntax & Examples](#scp-syntax--examples)
  - [SCP Performance Tuning](#scp-performance-tuning)

---

## SSH (Secure Shell)

### Shell vs. Console vs. Terminal (TTY & PTS)

- **Terminal / Console / Shell:** The *terminal* connects to the *console*, where the *shell* is presented.
- **TTY (Teletypewriter):** The software-virtualized equivalent of a physical console port. On a Linux machine, switching virtual consoles with `Ctrl + Alt + F1` through `F12` and logging in creates multiple TTY sessions, which you can inspect using the `who` command.
- **PTS (Pseudo Terminal Slave):** An emulated virtual TTY device that allows terminal connections over a network or graphical session. **SSH** and **Telnet** are classic examples of programs that allocate PTS devices.

### SSH Tunneling (Local Port Forwarding)

*Source: [How-To Geek — How to Use SSH Tunneling](https://www.howtogeek.com/168145/how-to-use-ssh-tunneling/)*

To forward a local port through an SSH server, pass the `-L` flag:

```bash
ssh -L local_port:remote_address:remote_port username@server.com
```

**Example:**
Suppose a database server is located at `192.168.1.111` port `1234` on your office network, and you have SSH access to `ssh.youroffice.com` as user `bob`. Forward local port `8888` to that database server:

```bash
ssh -L 8888:192.168.1.111:1234 bob@ssh.youroffice.com
```

### SSH Agent Configuration

Start `ssh-agent` and load your private key manually:

```bash
eval `ssh-agent -s` && ssh-add
```

Automatically start `ssh-agent` in your `~/.bashrc` or `~/.bash_profile` for each new shell session:

```bash
SSHAGENT=/usr/bin/ssh-agent
SSHAGENTARGS="-s"
if [ -z "$SSH_AUTH_SOCK" -a -x "$SSHAGENT" ]; then
  eval `$SSHAGENT $SSHAGENTARGS`
  trap "kill $SSH_AGENT_PID" 0
fi
```

### SSH Key Management

**Add a passphrase to an existing private key that was generated without one:**

```bash
ssh-keygen -p -f keyfile
```

**Remove a passphrase from a private key (leave `new_passphrase` empty):**

```bash
ssh-keygen -p [-P old_passphrase] [-N new_passphrase] [-f keyfile]
```

### Cluster Execution over SSH

Restart Docker Compose services across all hosts listed in `server-cluster`:

```bash
for s in $(cat server-cluster); do
  ssh -i $PRIVATE_KEY USER_NAME@$s \
    "sudo su -c 'cd /root/dockerComposeWebServer && docker-compose down && docker-compose up -d'"
done
```

---

## DSH (Distributed Shell)

Server groups are configured in `/etc/dsh/group/`.

### DSH Options

| Option | Description |
| :--- | :--- |
| `-f machinefile` | Add all machines listed in `machinefile` to the target execution list |
| `-g groupname` | Add all machines listed in `/etc/dsh/group/groupname` to the target execution list |
| `-w` | Execute sequentially on each machine, waiting for completion before moving to the next |
| `-c` | Execute shells concurrently across all target machines |
| `-M` | Prepend machine names to standard output (useful with `-c` / `--concurrent-shell` for parsable output) |

### DSH Examples

Check disk space on `/` across a server group:

```bash
dsh -g POOL_Dir/Server_Group_File "df -h /"
```

Run a Perl log processing script concurrently across matching servers:

```bash
dsh -c -m $(grep serverSname* /etc/dsh/group/pool/servers_types | perl -pe 'print "," if($i++);chomp;') \
  '/users/dev/script.pl /logs/script.pl_log- 20181202[5-9]* /logs/script.pl_log'
```

---

## SCP (Secure Copy)

### SCP Syntax & Examples

**Copy a file from a remote host to the local host:**

```bash
scp your_username@remotehost.edu:foobar.txt /some/local/directory
```

**Copy a file from the local host to a remote host:**

```bash
scp foobar.txt your_username@remotehost.edu:/some/remote/directory
```

**Recursively copy directory `foo` from the local host to remote directory `bar`:**

```bash
scp -r foo your_username@remotehost.edu:/some/remote/directory/bar
```

**Copy a file directly between two remote hosts (`rh1.edu` to `rh2.edu`):**

```bash
scp your_username@rh1.edu:/some/remote/directory/foobar.txt \
    your_username@rh2.edu:/some/remote/directory/
```

**Copy multiple local files to your remote home directory (`~`):**

```bash
scp foo.txt bar.txt your_username@remotehost.edu:~
```

**Copy a file over a custom SSH port (`-P 2264`):**

```bash
scp -P 2264 foobar.txt your_username@remotehost.edu:/some/remote/directory
```

**Copy multiple files from a remote host to the current local directory (`.`):**

```bash
scp your_username@remotehost.edu:/some/remote/directory/\{a,b,c\} .
scp your_username@remotehost.edu:~/\{foo.txt,bar.txt\} .
```

### SCP Performance Tuning

By default, legacy `scp` implementations used Triple-DES encryption. Specifying a faster cipher (`-c blowfish`) can increase transfer speeds:

```bash
scp -c blowfish some_file your_username@remotehost.edu:~
```

Enabling compression (`-C`) can also increase transfer speed over slow links (on fast networks it may add unnecessary CPU overhead):

```bash
scp -c blowfish -C local_file your_username@remotehost.edu:~
```
