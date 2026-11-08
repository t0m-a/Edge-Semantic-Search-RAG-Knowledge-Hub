# Cloudflare Tunnels Explained

## Document Metadata
- **Category:** Network Security / Infrastructure
- **Keywords:** Cloudflare, Tunnel, cloudflared, Edge Networking, Zero Trust, NAT Traversal, Inbound Security

## Core Definition
A **Cloudflare Tunnel** is a secure networking tool that connects private servers, home labs, or local applications to the internet without opening inbound firewall ports or exposing a public IP address. 

## Architectural Workflow
Instead of waiting for incoming internet traffic to hit a local router or server, the structural model operates on an outbound-only connection workflow:
1. **Outbound Connection:** A lightweight daemon named `cloudflared` is installed on the local machine, internal server, or container environment.
2. **Persistent Link:** The `cloudflared` agent initiates and maintains long-lived, outbound-only, post-quantum encrypted connections to Cloudflare's edge network over port `7844`.
3. **Traffic Routing:** When an external client visits a configured public domain (e.g., `app.example.com`), Cloudflare routes that request back through the established outbound tunnel to the mapped local service (e.g., `http://localhost:8080`).

## Functional Capabilities and Benefits
- **Zero Inbound Firewalls:** Eliminates the traditional external network attack surface by blocking all incoming port connections at the boundary router.
- **NAT and CGNAT Traversal:** Resolves connectivity issues behind Carrier-Grade NAT (CGNAT) and standard Network Address Translation environments without requiring public static IPs or port-forwarding rules.
- **Edge Layer Protection:** Automatically wraps internal web assets in Cloudflare's edge capabilities, including DDoS Protection, Web Application Firewall (WAF), and CDN caching optimization.
- **Zero Trust Authentication:** Allows engineers to layer access control restrictions (such as identity providers, multi-factor tokens, or Cloudflare WARP client validation) directly over internal endpoints.

## Primary Implementations
- **Public App Exposure:** Exposing self-hosted infrastructure, local APIs, or developer environments securely to the public web.
- **Quick Ephemeral Tunnels:** Provisioning rapid, testing URLs using `cloudflared tunnel --url` on the `trycloudflare.com` zone.
- **Private Subnet Access:** Replacing legacy corporate VPN architectures by connecting authenticated remote workers to interior corporate subnets or databases.