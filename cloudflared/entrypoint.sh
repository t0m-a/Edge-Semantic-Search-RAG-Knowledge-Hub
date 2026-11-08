#!/usr/bin/env sh
set -eu

PERSIST_DIR="/var/lib/cloudflared"
BIN_DIR="${PERSIST_DIR}/bin"
PERSISTED_BIN="${BIN_DIR}/cloudflared"
APT_CACHE_DIR="${PERSIST_DIR}/apt/archives"
APT_LISTS_DIR="${PERSIST_DIR}/apt/lists"
VERSION_FILE="${PERSIST_DIR}/version.txt"
SYSTEM_BIN="/usr/bin/cloudflared"
UPSTREAM_SEED_BIN="/usr/local/share/cloudflared/cloudflared.upstream"

mkdir -p "${BIN_DIR}" "${APT_CACHE_DIR}/partial" "${APT_LISTS_DIR}/partial"

echo "[cloudflared-boot] Running apt update && apt upgrade -y at container boot..."
export DEBIAN_FRONTEND=noninteractive
if apt update && apt upgrade -y -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold"; then
    echo "[cloudflared-boot] apt update && apt upgrade -y completed successfully."
else
    echo "[cloudflared-boot] WARNING: Online apt update/upgrade failed. Checking persistent APT cache..."
    if ls "${APT_CACHE_DIR}"/cloudflared_*.deb >/dev/null 2>&1; then
        LatestDeb="$(ls -1v "${APT_CACHE_DIR}"/cloudflared_*.deb | tail -n 1)"
        echo "[cloudflared-boot] Installing cached package: ${LatestDeb}"
        dpkg -i "${LatestDeb}" || true
    fi
fi

get_version() {
    if [ -x "$1" ]; then
        "$1" --version 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i ~ /^[0-9]+\.[0-9]+\.[0-9]+/) {print $i; exit}}'
    fi
}

# Ensure the persistent binary holds the newest version across APT, upstream seed, and existing persistent volume
for CANDIDATE in "${SYSTEM_BIN}" "${UPSTREAM_SEED_BIN}"; do
    if [ ! -x "${CANDIDATE}" ]; then
        continue
    fi
    CAND_VER="$(get_version "${CANDIDATE}" || true)"
    PERSIST_VER="$(get_version "${PERSISTED_BIN}" || true)"

    if [ ! -x "${PERSISTED_BIN}" ] || [ -z "${PERSIST_VER}" ]; then
        echo "[cloudflared-boot] Seeding persistent cloudflared binary (${CAND_VER:-unknown}) -> ${PERSISTED_BIN}"
        cp -f "${CANDIDATE}" "${PERSISTED_BIN}"
        chmod +x "${PERSISTED_BIN}"
    elif [ -n "${CAND_VER}" ] && dpkg --compare-versions "${CAND_VER}" gt "${PERSIST_VER}"; then
        echo "[cloudflared-boot] Upgrading persistent cloudflared binary (${PERSIST_VER} -> ${CAND_VER})"
        cp -f "${CANDIDATE}" "${PERSISTED_BIN}"
        chmod +x "${PERSISTED_BIN}"
    fi
done

# Keep /usr/bin/cloudflared and /usr/local/bin/cloudflared aligned with the highest persisted binary
if [ -x "${PERSISTED_BIN}" ]; then
    SYS_VER="$(get_version "${SYSTEM_BIN}" || true)"
    PERSIST_VER="$(get_version "${PERSISTED_BIN}" || true)"
    if [ -n "${PERSIST_VER}" ] && [ -n "${SYS_VER}" ] && dpkg --compare-versions "${PERSIST_VER}" gt "${SYS_VER}"; then
        echo "[cloudflared-boot] Restoring newer persisted binary (${PERSIST_VER} > ${SYS_VER}) to ${SYSTEM_BIN}"
        cp -f "${PERSISTED_BIN}" "${SYSTEM_BIN}"
        chmod +x "${SYSTEM_BIN}"
    fi
    ln -sf "${PERSISTED_BIN}" /usr/local/bin/cloudflared
fi

ACTIVE_VER="$(get_version "${PERSISTED_BIN}" || echo "unknown")"
printf "version=%s\nupdated_at=%s\n" "${ACTIVE_VER}" "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" > "${VERSION_FILE}"
echo "[cloudflared-boot] Active persisted cloudflared version: ${ACTIVE_VER}"

# Normalize command arguments
if [ "$#" -eq 0 ]; then
    set -- tunnel --no-autoupdate run --token "${TUNNEL_TOKEN:-}"
elif [ "$1" = "cloudflared" ]; then
    shift
fi

echo "[cloudflared-boot] Starting Cloudflare Tunnel daemon..."
exec "${PERSISTED_BIN}" "$@"
