FROM python:3.8

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app
COPY requirements.txt /usr/src/app/
COPY . /usr/src/app

RUN apt-get update
RUN apt-get purge python* -y
RUN apt-get --purge autoremove -y
RUN apt-get upgrade -y
RUN apt-get install -y libmpfr-dev libmpc-dev

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