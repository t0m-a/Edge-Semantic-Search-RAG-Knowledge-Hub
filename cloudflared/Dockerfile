FROM cloudflare/cloudflared:latest AS upstream

FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive

# Seed upstream cloudflared binary as fallback reference
COPY --from=upstream /usr/local/bin/cloudflared /usr/local/share/cloudflared/cloudflared.upstream

# Configure official Cloudflare APT repository and install cloudflared
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    && mkdir -p --mode=0755 /usr/share/keyrings \
    && curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg -o /usr/share/keyrings/cloudflare-main.gpg \
    && chmod a+r /usr/share/keyrings/cloudflare-main.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared bookworm main" > /etc/apt/sources.list.d/cloudflared.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends cloudflared \
    && rm -rf /var/lib/apt/lists/* \
    && rm -f /etc/apt/apt.conf.d/docker-clean \
    && printf 'Dir::Cache::archives "/var/lib/cloudflared/apt/archives";\nDir::State::lists "/var/lib/cloudflared/apt/lists";\nBinary::apt::APT::Keep-Downloaded-Packages "true";\nAPT::Keep-Downloaded-Packages "true";\n' > /etc/apt/apt.conf.d/99persistent-cache \
    && mkdir -p /var/lib/cloudflared/bin /var/lib/cloudflared/apt/archives/partial /var/lib/cloudflared/apt/lists/partial

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN sed -i 's/\r$//' /usr/local/bin/entrypoint.sh && chmod +x /usr/local/bin/entrypoint.sh

VOLUME ["/var/lib/cloudflared"]

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["tunnel", "--no-autoupdate", "run"]
