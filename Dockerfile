FROM buildpack-deps:bullseye-scm
ENV PATH /usr/local/bin:$PATH

RUN set -ex; \
	apt-get update ;\
    apt-get purge python* -y; \
    apt-get --purge autoremove -y; \
    apt-get upgrade -y; \
	apt-get install -y --no-install-recommends \
		autoconf \
		automake \
		bzip2 \
		dpkg-dev \
		file \
		gcc \
        gfortran \
		libbz2-dev \
		libc6-dev \
		libcurl4-openssl-dev \
		libevent-dev \
		libffi-dev \
		libgmp-dev \
		liblzma-dev \
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
		libmaxminddb-dev \
		libmpfr-dev \
        libmpc-dev \
        libmpdec-dev \
		uuid-dev \
        wamerican \
        locales \
        libexpat1-dev \
		libopenblas-dev \
	; \
	rm -rf /var/lib/apt/lists/*

RUN locale-gen --purge en_US.UTF-8
ENV LANG en_US.UTF-8
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

RUN curl https://codeload.github.com/python/cpython/tar.gz/refs/tags/v3.8.9 | tar xz
WORKDIR /usr/src/app/cpython-3.8.9
RUN ./configure --enable-optimizations --with-lto --enable-shared --enable-loadable-sqlite-extensions --enable-big-digits --with-system-expat --with-dbmliborder=bdb --enable-ipv6
RUN make install
RUN ldconfig
WORKDIR /usr/src/app
RUN rm -rf *

COPY requirements.txt /usr/src/app/
COPY . /usr/src/app

RUN pip3 install --no-cache-dir poetry

WORKDIR /usr/src
RUN git clone --depth 1 https://github.com/microsoft/electionguard-python.git
WORKDIR /usr/src/electionguard-python
RUN poetry build

WORKDIR /usr/src/app
RUN pip3 install --no-cache-dir -r requirements.txt

EXPOSE 80

ENTRYPOINT ["python3"]

CMD ["-m", "dtcvote"]
