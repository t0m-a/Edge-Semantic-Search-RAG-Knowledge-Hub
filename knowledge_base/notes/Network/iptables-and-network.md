# Iptables & Network Management

> [← Back to Main Index](README.md)

## Table of Contents

- [Packet Capture with `tcpdump`](#packet-capture-with-tcpdump)
- [Network Routing, Interfaces & DNS](#network-routing-interfaces--dns)
- [Firewall Management with `iptables`](#firewall-management-with-iptables)
  - [Blocking IPs & Listing Rules](#blocking-ips--listing-rules)
  - [Saving & Restoring Rules (Persistence)](#saving--restoring-rules-persistence)
  - [Complete Server Firewall Ruleset Example](#complete-server-firewall-ruleset-example)
  - [Isolating a Web Server Behind a Load Balancer](#isolating-a-web-server-behind-a-load-balancer)
  - [Basic Web Server Firewall](#basic-web-server-firewall)
  - [Automated Log-Based Blocking (Use with Caution)](#automated-log-based-blocking-use-with-caution)

---

## Packet Capture with `tcpdump`

**Capture packets on interface `eth1` filtered by CIDR network, host IP, and ports:**

```bash
tcpdump -i eth1 -c 10000 -s0 -w /tmp/trace_file_name_20110812173738.pcap \
  tcp and net 10.0.1.0/24 or host 10.0.0.12 and port 80

tcpdump -i eth1 -c 10000 -s0 -w /tmp/trace_$(hostname)_$(date +%Y-%m-%d).pcap \
  tcp and host \(10.0.0.22 or 192.168.0.22\)

tcpdump -i eth1 -c 10000 -s0 -w /tmp/trace_$(hostname)_$(date +%Y-%m-%d).pcap \
  tcp and host 10.0.0.20 and \(port 443 or 8080\)
```

**Simple packet capture & connection termination (`tcpkill`):**

```bash
tcpdump -s0 -v -i eth0 -w output-file
tcpkill --arg --int --host
```

**Remote packet capture over SSH (excluding port 22):**

```bash
ssh root@HOST -- "tcpdump -w - -s 65535 'not port 22'" > capture.pcap
```

---

## Network Routing, Interfaces & DNS

**Configure a default gateway (`route` and `ip route`):**

```bash
route add default gw {IP-ADDRESS} {INTERFACE-NAME}
route add default gw 10.0.0.254

# Or using iproute2:
ip route add 192.168.1.0/24 via 192.168.1.254
```

**Delete a default route and gateway:**

```bash
route del 0.0.0.0 gw 10.0.0.254
```

**Display the kernel routing table:**

```bash
route -n
```

**Inspect physical links, IP routes, ARP table, and interface addresses:**

```bash
ip link
ip route
arp -a
ip addr show eth0
ifconfig eth0
```

**Query DNS servers (`dig` from `dnsutils`):**

```bash
dig @ip_address
dig fqdn.tld
```

---

## Firewall Management with `iptables`

### Blocking IPs & Listing Rules

Block incoming and outgoing traffic for specific IPs:

```bash
ip="IP_ADDRESS_TO_BLOCK_1 IP_ADDRESS_TO_BLOCK_2 IP_ADDRESS_TO_BLOCK_3"
iptables -A INPUT -s $ip -j DROP && iptables -A OUTPUT -d $ip -j DROP
```

List active rules with packet/byte counters and line numbers:

```bash
iptables -nvL --line-numbers
```

Insert or delete a rule at position `1` (top of the chain):

```bash
iptables -I INPUT 1 ...   # Insert at line 1
iptables -D INPUT 1       # Delete rule at line 1
```

### Saving & Restoring Rules (Persistence)

Save current rules to `/etc/iptables.conf` and restore them:

```bash
iptables-save > /etc/iptables.conf
iptables-restore < /etc/iptables.conf
```

To make rules persistent across reboots, save `/etc/iptables.conf` and add the following to `/etc/rc.local` as `root`:

```bash
# Load iptables rules from config file
iptables-restore < /etc/iptables.conf
```

### Complete Server Firewall Ruleset Example

Example combining `fail2ban` chains (`f2b-*`), stateful connection tracking, custom SSH port (`9922`), DNS (`53`), and HTTP/HTTPS (`80,443`):

```bash
# Fail2ban chains
iptables -A INPUT -p tcp -m multiport --dports 80,443 -j f2b-nginx-http-auth
iptables -A INPUT -p tcp -m multiport --dports 80,443 -j f2b-wordpress
iptables -A INPUT -p tcp -m multiport --dports 9922 -j f2b-sshd

# Inbound rules
iptables -A INPUT -i lo -j ACCEPT
iptables -A INPUT -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
iptables -A INPUT -p tcp -m tcp --dport 9922 -j ACCEPT
iptables -A INPUT -p tcp -m multiport --dports 80,443 -j ACCEPT
iptables -A INPUT -j DROP

# Outbound rules
iptables -A OUTPUT -m state --state RELATED,ESTABLISHED -j ACCEPT
iptables -A OUTPUT -p tcp -m tcp --dport 53 -j ACCEPT
iptables -A OUTPUT -p udp -m udp --dport 53 -j ACCEPT
iptables -A OUTPUT -p tcp -m tcp --dport 80 -j ACCEPT
iptables -A OUTPUT -p tcp -m tcp --dport 443 -j ACCEPT
iptables -A OUTPUT -p tcp -m tcp --dport 9922 -j ACCEPT
iptables -A OUTPUT -j DROP
```

### Isolating a Web Server Behind a Load Balancer

Reject all direct traffic on port `80` except from the load balancer IP (inserted at rule `#1`):

```bash
iptables -A INPUT -p tcp --dport 80 -j REJECT
iptables -I INPUT 1 -p tcp --dport 80 -s LOAD_BALANCER_IP -j ACCEPT
```

### Basic Web Server Firewall

Accept loopback traffic, established/related connections, SSH (`22`), and HTTP/HTTPS (`80,443`), then drop everything else:

```bash
iptables -A INPUT -i lo -j ACCEPT
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -A INPUT -p tcp --dport 22 -j ACCEPT
iptables -A INPUT -p tcp -m multiport --dports 80,443 -j ACCEPT
iptables -A INPUT -j DROP
```

### Automated Log-Based Blocking (Use with Caution)

> **Warning:** Automatically dropping IPs parsed from logs can lock out legitimate traffic if not carefully filtered.

```bash
# Drop IPs triggering HTTP 401 responses
for s in $(cat /logs/main_access.log | grep -i 401 | grep -v pingdom | grep -v IP_ADDRESS | cut -f 1 -d '-'); do
  iptables -A INPUT -s $s -j DROP
done

# Drop IPs sending suspicious POST requests
for s in $(cat main_access.log | grep POST | grep -v ciro | grep -v pingdom | cut -f 1 -d '-'); do
  iptables -A INPUT -s $s -j DROP
done
```
