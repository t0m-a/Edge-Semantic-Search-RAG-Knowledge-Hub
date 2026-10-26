# Docker & Docker Compose Administration

> [← Back to Main Index](README.md)

## Table of Contents

- [Installing Docker & Docker Compose](#installing-docker--docker-compose)
  - [Debian Stretch](#debian-stretch)
  - [Ubuntu 18.04](#ubuntu-1804)
  - [Installing Docker Compose (Debian & Ubuntu)](#installing-docker-compose-debian--ubuntu)
- [Docker Basic Commands & Concepts](#docker-basic-commands--concepts)
  - [Running & Linking Containers](#running--linking-containers)
  - [Attaching & Executing Inside a Running Container](#attaching--executing-inside-a-running-container)
  - [Copying Files Between Container and Host (`docker cp`)](#copying-files-between-container-and-host-docker-cp)
- [Docker CLI Subcommands Reference](#docker-cli-subcommands-reference)
- [Common Docker Workflows](#common-docker-workflows)
  - [Tagging & Pushing Images to a Registry](#tagging--pushing-images-to-a-registry)
  - [Running Interactive & Database Containers](#running-interactive--database-containers)
  - [Stopping & Removing All Containers](#stopping--removing-all-containers)
  - [Post-Install Packages for Minimal Debian Containers](#post-install-packages-for-minimal-debian-containers)
- [Docker Compose (`docker-compose.yml`)](#docker-compose-docker-composeyml)
  - [Complete LEMP + phpMyAdmin Stack Example](#complete-lemp--phpmyadmin-stack-example)
  - [Lightweight Nginx + PHP-FPM Stack Example](#lightweight-nginx--php-fpm-stack-example)
- [Dockerfile Examples](#dockerfile-examples)
  - [Kali Linux + Sparta (X11 GUI Export)](#kali-linux--sparta-x11-gui-export)
  - [Kali Linux + Metasploit Framework & PostgreSQL](#kali-linux--metasploit-framework--postgresql)
- [Custom Commands, Bind Mounts & Aliases](#custom-commands-bind-mounts--aliases)

---

## Installing Docker & Docker Compose

### Debian Stretch

Verify the official Docker GPG fingerprint and install `docker-ce`:

```bash
curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add -
apt-key adv --list-public-keys --with-fingerprint --with-colons | grep 9DC8 | cut -c 13-52 | \
  grep -q -w "9DC858229FC7DD38854AE2D88D81803C0EBFCD88" && export KEY_OK=KEY_OK

if [ "$KEY_OK" = 'KEY_OK' ]; then
  add-apt-repository \
    "deb [arch=amd64] https://download.docker.com/linux/debian $(lsb_release -cs) stable" && \
    apt-get update && apt-get install -y docker-ce
fi
```

### Ubuntu 18.04

```bash
apt-get update && apt-get install -y docker.io
```

### Installing Docker Compose (Debian & Ubuntu)

Check the latest release on [GitHub — docker/compose/releases](https://github.com/docker/compose/releases):

```bash
sudo curl -L https://github.com/docker/compose/releases/download/1.22.0/docker-compose-$(uname -s)-$(uname -m) \
  -o /usr/local/bin/docker-compose && \
  sudo chmod +x /usr/local/bin/docker-compose && \
  docker-compose --version
```

---

## Docker Basic Commands & Concepts

### Running & Linking Containers

> **Note:** The `--link` flag is legacy. Prefer `docker-compose` and user-defined Docker networks for production setups. However, `--link` can still be used for quick ad-hoc container networking.

**Run a web server container linked to an SQL server container with `/sbin/init`:**

```bash
docker run --privileged --restart always -it \
  -v /local/mount/folder/path:/var/lib/mysql \
  --link sql_server_container_name:sql_server_container_name \
  -v /sys/fs/cgroup:/sys/fs/cgroup \
  --name web_server_container_name -d image_name:tag /sbin/init
```

**Run a web server container in daemon mode (`-d`) with a shared volume (`-v`) and port mapping (`-p`):**

```bash
docker run --name webserver \
  -v /shared/DIR/from/host:/path/in/container:ro \
  -p HOST_PORT:CONTAINER_PORT \
  -d image_name
# Use :rw instead of :ro for read-write volume mounts
```

**Run an interactive Nginx container linked to a PHP container (`phpserver`):**

```bash
docker run -it --link phpserver:phpserver nginx /bin/bash

# General syntax:
# docker run -it --link ContainerName_ToLink:ContainerAlias image_name command_to_run
```

The `ContainerAlias` is added to the `/etc/hosts` file inside the recipient container.

**Startup Hierarchy & Data Persistence:**
In a classic LEMP stack, Nginx connects to PHP, which connects to MySQL—so start the **MySQL** container first, then **PHP**, and finally **Nginx**. To preserve data when a container stops, **data must be stored outside the container** using a volume (e.g., `-v /my/own/datadir:/var/lib/mysql`).

### Attaching & Executing Inside a Running Container

1. **`docker attach`:** Attach to a running container using `--sig-proxy=false` so detaching does not kill the container:
   ```bash
   docker attach --sig-proxy=false CONTAINER_ID_OR_NAME
   ```
2. **`docker exec` (Recommended):** Spawn an interactive Bash shell inside a running container:
   ```bash
   docker exec -i -t CONTAINER_ID bash
   ```

### Copying Files Between Container and Host (`docker cp`)

```bash
docker cp <containerId>:/file/path/within/container /host/path/target

# Example:
docker cp 25bc97fc48e3:/home/kali-user/167.99.27.137-201806190451.tar.gz \
  /home/tom/Workspaces/docker/sparta/sparta-data/
```

---

## Docker CLI Subcommands Reference

| Subcommand | Description & Common Flags |
| :--- | :--- |
| `build` | Build an image from a `Dockerfile` |
| `commit` | Create a new image from a container's changes (`docker commit CONTAINER_ID` then `docker tag NEW_IMAGE_ID NAME:TAG`) |
| `cp` | Copy files/folders between a container's filesystem and the host |
| `create` | Create a new container without starting it |
| `diff` | Inspect changes to files or directories on a container's filesystem |
| `events` | Stream real-time events from the Docker daemon |
| `exec` | Run a command in an existing running container |
| `export` | Export a container's filesystem as a tar archive stream |
| `history` | Show the layer history of an image |
| `images` | List local images |
| `import` | Import the contents from a tarball to create a filesystem image |
| `info` | Display system-wide Docker information |
| `inspect` | Return low-level JSON information on Docker objects (containers, images, networks) |
| `kill` | Kill one or more running containers |
| `load` | Load an image from a tar archive or `STDIN` |
| `login` | Log in to a Docker registry |
| `logout` | Log out from a Docker registry |
| `logs` | Fetch the logs of a container |
| `port` | List port mappings or look up the public-facing port NAT-ed to a `PRIVATE_PORT` |
| `pause` | Pause all processes within one or more containers |
| `ps` | List running containers (use `--all` / `-a` to list all containers ever run) |
| `pull` | Pull an image or repository from a registry |
| `push` | Push an image or repository to a registry |
| `restart` | Restart one or more containers |
| `rm` | Remove one or more containers |
| `rmi` | Remove one or more images (`-f` or `--force` to force removal) |
| `run` | Run a command in a new container (`-d` daemon, `-p HOST:CONTAINER` port mapping, `-ti` interactive TTY, `-v` volume mount) |
| `save` | Save one or more images to a tar archive |
| `search` | Search Docker Hub for images |
| `start` | Start one or more stopped containers |
| `stop` | Stop one or more running containers |
| `tag` | Create a tag ` TARGET_IMAGE` that refers to `SOURCE_IMAGE` |
| `top` | Display the running processes of a container |
| `unpause` | Unpause all processes within one or more containers |
| `version` | Show the Docker version information |
| `wait` | Block until one or more containers stop, then print their exit codes |

---

## Common Docker Workflows

### Tagging & Pushing Images to a Registry

```bash
docker tag local-image:tagname new-repo:tagname
docker push new-repo:tagname
```

> **Note:** You must be logged in (`docker login`) or authenticate with your API key first (see [StackOverflow reference](https://stackoverflow.com/questions/41984399/denied-requested-access-to-the-resource-is-denied-docker)):

```bash
curl -u your_docker_user_name:apikey https://cloud.docker.com/api/app/v1/service/
docker push your_docker_user_name/remote-images:tagname
```

### Running Interactive & Database Containers

**Pull official Debian image and open an interactive shell:**

```bash
docker pull debian && docker run -it debian /bin/bash
```

**Launch a MySQL server container with persistent storage and initial database/user environment variables:**

```bash
docker run --name sqlsrv3 \
  -v /mnt/databases:/var/lib/mysql \
  -e MYSQL_ROOT_PASSWORD=root_password \
  -e MYSQL_DATABASE=db-sql \
  -e MYSQL_USER=db_user \
  -e MYSQL_PASSWORD=db_user_password \
  -d mysql:latest
```

### Stopping & Removing All Containers

```bash
docker stop $(docker ps -a -q)
docker rm $(docker ps -a -q)
```

### Post-Install Packages for Minimal Debian Containers

Install essential networking, archiving, and editing utilities inside a minimal Debian/Ubuntu container:

```bash
apt-get update && apt-get upgrade -y && apt-get install -y \
  curl wget gzip unzip vim vim-common vim-runtime htop sysstat net-tools
```

Or with APT HTTPS transport and GnuPG utilities:

```bash
apt-get install -y \
  curl gzip bzip2 unzip wget htop sysstat \
  apt-transport-https software-properties-common apt-utils gnupg2 nano
```

---

## Docker Compose (`docker-compose.yml`)

Complete working `docker-compose.yml` stack configurations are provided in the [Complete LEMP + phpMyAdmin Stack Example](#complete-lemp--phpmyadmin-stack-example) and [Lightweight Nginx + PHP-FPM Stack Example](#lightweight-nginx--php-fpm-stack-example) sections below.

### Complete LEMP + phpMyAdmin Stack Example

```yaml
version: '3'
services:
  web:
    image: nginx:latest
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf/nginx.conf:/etc/nginx/nginx.conf
      - ./html:/html
      - ./site.conf:/etc/nginx/sites-enabled
      - ./certs:/certs
      - ./logs:/var/log/nginx
      - ./mime.types/mime.types:/etc/nginx/mime.types
    networks:
      - lemp-network

  php:
    image: php:fpm
    restart: always
    volumes:
      - ./html:/html
      - ./php-log.conf:/usr/local/etc/php-fpm.d/zz-log.conf
    networks:
      - lemp-network

  db:
    image: mariadb:latest
    restart: always
    ports:
      - "3306:3306"
    volumes:
      - ./db-data:/var/lib/mysql
    environment:
      - MYSQL_ROOT_PASSWORD=test
    networks:
      - lemp-network

  phpmyadmin:
    image: phpmyadmin/phpmyadmin:latest
    restart: always
    ports:
      - "8080:443"
    volumes:
      - ./pma.conf/nginx.conf:/etc/nginx.conf
      - ./pma.conf/htpasswd:/htpasswd
      - ./logs:/var/log/nginx
      - ./certs:/certs
    environment:
      - MYSQL_USERNAME=root
      - MYSQL_ROOT_PASSWORD=test
      - PMA_HOST=db
    networks:
      - lemp-network

networks:
  lemp-network:
    driver: bridge
```

### Lightweight Nginx + PHP-FPM Stack Example

```yaml
version: '3'
services:
  web:
    environment:
      - HOSTNAME=web
    image: nginx:latest
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf/nginx.conf:/etc/nginx/nginx.conf
      - /var/www:/html
      - ./site.conf:/etc/nginx/sites-enabled
      - ./certs:/certs
      - ./logs:/var/log/nginx
      - ./mime.types/mime.types:/etc/nginx/mime.types
    networks:
      - webserver-network

  php:
    environment:
      - HOSTNAME=php
    image: php:fpm
    restart: always
    volumes:
      - /var/www:/html
      - ./php-log.conf:/usr/local/etc/php-fpm.d/zz-log.conf
    networks:
      - webserver-network

networks:
  webserver-network:
    driver: bridge
```

---

## Dockerfile Examples

Below are two complete, working `Dockerfile` examples with data persistence, database setup, and X11 GUI export:

### Kali Linux + Sparta (X11 GUI Export)

```dockerfile
FROM kalilinux/kali-linux-docker:latest
RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y iftop iptraf net-tools curl gzip bzip2 unzip
RUN apt-get install -y libxext-dev libxrender-dev libxtst-dev libqtwebkit4 libqt4-dev
RUN apt-get install -y python-elixir ldap-utils rwho rsh-client x11-apps finger python-pyside.qtwebkit python-qt4
RUN apt-get install -y hydra cutycapt nmap
RUN apt-get install -y sudo
RUN export uid=1000 gid=1000
RUN mkdir -p /home/kali-user
RUN echo "kali-user:x:${uid}:${gid}:kali-user,,,:/home/kali-user:/bin/bash" >> /etc/passwd
RUN echo "kali-user:x:${uid}:" >> /etc/group
RUN echo "kali-user ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers
RUN chmod 0440 /etc/sudoers
RUN chown ${uid}:${gid} -R /home/kali-user
USER kali-user
ENV home /home/kali-user
ADD bashrc /home/kali-user/.bashrc
ADD bashrc /root/.bashrc
ADD sparta-data /usr/share/sparta
ADD sparta-beta-1.0.3 /opt/sparta-beta-1.0.3
ADD sparta-beta-1.0.3/app/auxiliary.py /usr/share/sparta/app/auxiliary.py
RUN chown ${uid}:${gid} -R /opt/sparta-beta-1.0.3
CMD /opt/sparta-beta-1.0.3/sparta
```

### Kali Linux + Metasploit Framework & PostgreSQL

```dockerfile
FROM kalilinux/kali-linux-docker:latest
RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y libxext-dev libxrender-dev libxtst-dev bmon iftop iptraf nethogs net-tools nmap \
    wireshark htop curl apt-transport-https apt-utils strace sysstat ca-certificates gnupg2 \
    software-properties-common gzip bzip2 whois dnsutils rblcheck unzip vim vim-common vim-runtime httrack \
    python2.7-minimal python3 python-pip pexpect pycrypto requests pyopenssl pefile impacket qrcode \
    pillow python-elixir ldap-utils rwho rsh-client x11-apps finger \
    python-pyside.qtwebkit python-qt4 hydra libapache2-mod-php python-pefile python-pexpect \
    python-ptyprocess metasploit-framework setoolkit armitage kali-linux-web kali-linux-top10 man-db exploitdb
RUN export uid=1000 gid=1000
RUN mkdir -p /home/kali-user
RUN echo "kali-user:x:${uid}:${gid}:kali-user,,,:/home/kali-user:/bin/bash" >> /etc/passwd
RUN echo "kali-user:x:${uid}:" >> /etc/group
RUN echo "kali-user ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers
RUN chmod 0440 /etc/sudoers
RUN chown ${uid}:${gid} -R /home/kali-user
USER kali-user
ENV home /home/kali-user
ADD data /data
ADD root /root
ADD database.yml /usr/share/metasploit-framework/config/database.yml
ADD postgresql /var/lib/postgresql
ADD services.sh /services.sh
CMD sh - /services.sh; /bin/bash
```

---

## Custom Commands, Bind Mounts & Aliases

**Copy PostgreSQL data and Metasploit configuration from a container:**

```bash
sudo docker cp 6f69511443c5:/var/lib/postgresql/10 \
  $HOME/Workspaces/docker/armitage/postgresql
sudo docker cp 6f69511443c5:/usr/share/metasploit-framework/config/database.yml \
  $HOME/Workspaces/docker/armitage/database.yml
```

**Run X11 GUI security containers with bind mounts:**

```bash
# Generic X11 forwarding + home bind mount
docker run -ti --rm -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix \
  --mount type=bind,src=/path/to/docker/folders/home/kali-user,dst=/home/kali-user \
  $IMAGE_NAME:IMAGE_TAG

# Armitage container with persistent PostgreSQL and user data
docker run -ti --rm -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix \
  --mount type=bind,src=$HOME/Workspaces/docker/armitage/root,dst=/root \
  --mount type=bind,src=$HOME/Workspaces/docker/armitage/armitage-data,dst=/usr/share/armitage \
  --mount type=bind,src=$HOME/Workspaces/docker/armitage/home/kali-user,dst=/home/kali-user \
  --mount type=bind,src=$HOME/Workspaces/docker/armitage/postgresql,dst=/var/lib/postgresql \
  armitage:latest

# Maltego container
docker run -ti --rm -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix \
  --mount type=bind,src=$HOME/Workspaces/docker/maltego/root,dst=/root \
  --mount type=bind,src=$HOME/Workspaces/docker/maltego/home/kali-user,dst=/home/kali-user \
  simonthomas/maltego:latest

# Kali Linux Web Assessment container
docker run -ti -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix \
  --mount type=bind,src=$HOME/Workspaces/docker/kali-linux-web-assessment/root,dst=/root \
  --mount type=bind,src=$HOME/Workspaces/docker/kali-linux-web-assessment/bashrc,dst=/root/.bashrc \
  --mount type=bind,src=$HOME/Workspaces/docker/kali-linux-web-assessment/data,dst=/data \
  --mount type=bind,src=$HOME/Workspaces/docker/kali-linux-web-assessment/home/kali-user,dst=/home/kali-user \
  --mount type=bind,src=$HOME/Workspaces/docker/kali-linux-web-assessment/postgresql,dst=/var/lib/postgresql \
  simonthomas/kali-linux-web-assessment:latest
```

**Alias to list running containers, all containers, and images at once:**

```bash
export SEP="-------------------------------------------------"
alias full-docker-list='docker ps && echo $SEP && docker ps --all && echo $SEP && docker images'
```
