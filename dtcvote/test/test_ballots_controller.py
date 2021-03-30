# coding: utf-8

from __future__ import absolute_import
import unittest

from flask import json
from six import BytesIO

from dtcvote.models.ballot_put_request import BallotPutRequest  # noqa: E501
from dtcvote.models.ballot_response import BallotResponse  # noqa: E501
from dtcvote.models.error import Error  # noqa: E501
from dtcvote.test import BaseTestCase


class TestBallotsController(BaseTestCase):
    """BallotsController integration test stubs"""

    def test_ballot_id_uuid_get(self):
        """Test case for ballot_id_uuid_get

        
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/api/v1/ballot/{ID}/{uuid}'.format(ID=56, uuid='uuid_example'),
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_ballot_id_uuid_put(self):
        """Test case for ballot_id_uuid_put

        
        """
        ballot_put_request = {
  "votes" : [ {
    "rank" : 1,
    "question_id" : 0,
    "candidate_sequence" : 6
  }, {
    "rank" : 1,
    "question_id" : 0,
    "candidate_sequence" : 6
  } ]
}
        query_string = [('dry_run', True)]
        headers = { 
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/api/v1/ballot/{ID}/{uuid}'.format(ID=56, uuid='uuid_example'),
            method='PUT',
            headers=headers,
            data=json.dumps(ballot_put_request),
            content_type='application/json',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_election_id_generate_ballots_get(self):
        """Test case for election_id_generate_ballots_get

        
        """
        query_string = [('dry_run', True)]
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/api/v1/election/{ID}/generate_ballots'.format(ID=56),
            method='GET',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
