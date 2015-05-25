#!/bin/bash
#
# Bootstrap a raw Ubuntu 14.04.2 LTS image w/ 3.8.13-bone71 kernel
# Run as root

this_dir=$(cd "`dirname "$0"`"; pwd)

echo >/etc/profile.d/lang.sh <<LANG
export LANGUAGE=en_US.UTF-8
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
LANG

source /etc/profile.d/lang.sh

run() {
    printf "\033[0;1;37m-> \033[0;1;34m"
    echo $@
    printf "\033[0m"
    "$@"
}

install_apt_pkgs() {
    run apt-get update
    run apt-get install -y \
        automake \
        build-essential \
        curl \
        dbus \
        gcc \
        git \
        gpsd \
        gpsd-clients \
        language-pack-en \
        libasound2-dev \
        libdbus-1-3 \
        libgps-dev \
        python \
        python-dev \
        python-gps \
        python-pip \
        redis-server \
        redis-tools \
        streamer \
        unzip \
        xawtv \
        --no-install-recommends
}

fix_dbus() {
    run mkdir /var/run/dbus
    run dbus-daemon --system
}

install_python_reqs() {
    run pip install -r "$this_dir/requirements.txt"
    run pip install Adafruit_BBIO
}

install_direwolf() {
    cd /tmp
    run curl -O http://home.comcast.net/~wb2osz/Version%201.1/direwolf-1.1-src.zip
    run unzip direwolf-1.1-src.zip

    cd /tmp/direwolf-1.1

    DWOLF_CFLAGS="-march=armv7-a -mtune=cortex-a8 -mfloat-abi=hard \
    -mfpu=neon -ffast-math -O3 -pthread -Iutm \
    -DENABLE_GPS -DUSE_ALSA -include errno.h"
    DWOLF_LDLIBS="-lgps -lasound"

    run make -f Makefile.linux CFLAGS="$DWOLF_CFLAGS" LDLIBS="$DWOLF_LDLIBS"
    run make -f Makefile.linux CFLAGS="$DWOLF_CFLAGS" LDLIBS="$DWOLF_LDLIBS" install
}

run ntpdate pool.ntp.org
install_apt_pkgs
install_python_reqs

cp "$this_dir/system/upstart-vanguard.conf" /etc/init/vanguard.conf

[[ -d /var/run/dbus ]] || fix_dbus
[[ -x /usr/local/bin/direwolf ]] || install_direwolf

