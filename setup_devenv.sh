#!/usr/bin/env bash

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo \
  "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y --no-install-recommends \
		autoconf \
		automake \
		bzip2 \
		dpkg-dev \
		file \
		g++ \
		gcc \
		libbz2-dev \
		libc6-dev \
		libcurl4-openssl-dev \
		libevent-dev \
		libffi-dev \
		liblzma-dev \
		libmaxminddb-dev \
		libncurses5-dev \
		libncursesw5-dev \
		libpq-dev \
		libreadline-dev \
		libsqlite3-dev \
		libssl-dev \
		libtool \
		libyaml-dev \
		make \
		patch \
		unzip \
		xz-utils \
		zlib1g-dev \
		libpq-dev libgmp-dev libmpfr-dev libmpc-dev libmpdec-dev \
						intel-mkl uuid-dev libbz2-dev libncurses-dev libssl-dev \
						liblzma-dev libsqlite3-dev libreadline-dev   \
						zlib1g-dev libdb-dev libffi-dev wamerican
						
#python3 -m venv ~/.venv/dtcvotes
echo 'alias envdtc="source ~/.venv/dtcvotes/bin/activate"' >> ~/.bash_aliases
		
. .bash_aliases


