# DTC-Vote
Simple, secure voting system. DTC-Vote allows for anonymous ballots using
homomorphic encryption or non-anonymous voting, ballot variations depending on
district or division, and supports plurality, majority, and ranked-choice
voting.

## Requirements
Python 3.8.x

## Usage
To run the server, please execute the following from the root directory:

```
pip3 install -r requirements.txt
python3 -m dtcvote
```

and open your browser to here:

```
http://localhost/api/v1/ui/
```

Your OpenAPI definition lives here:

```
http://localhost/api/v1/openapi.json
```

To launch the integration tests, use tox:
```
sudo pip install tox
tox
```

## Running with Docker

To run the server on a Docker container, use docker-compose to bring up an API
server and PostgreSQL server. From the root directory, enter:

```bash
# starting up the cluster
docker-compose up --build
```