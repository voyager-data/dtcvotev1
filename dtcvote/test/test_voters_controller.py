# coding: utf-8

from __future__ import absolute_import
import unittest

from flask import json
from six import BytesIO

from dtcvote.models.election_response import ElectionResponse  # noqa: E501
from dtcvote.models.error import Error  # noqa: E501
from dtcvote.models.voter_base import VoterBase  # noqa: E501
from dtcvote.models.voter_response import VoterResponse  # noqa: E501
from dtcvote.test import BaseTestCase


class TestVotersController(BaseTestCase):
    """VotersController integration test stubs"""

    def test_election_id_voters_delete(self):
        """Test case for election_id_voters_delete

        
        """
        query_string = [('dry_run', True)]
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/api/v1/election/{ID}/voters'.format(ID=56),
            method='DELETE',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_election_id_voters_get(self):
        """Test case for election_id_voters_get

        
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/api/v1/election/{ID}/voters'.format(ID=56),
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_election_id_voters_post(self):
        """Test case for election_id_voters_post

        
        """
        request_body = [56]
        query_string = [('dry_run', True)]
        headers = { 
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/api/v1/election/{ID}/voters'.format(ID=56),
            method='POST',
            headers=headers,
            data=json.dumps(request_body),
            content_type='application/json',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_voter_get(self):
        """Test case for voter_get

        
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/api/v1/voter',
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_voter_id_delete(self):
        """Test case for voter_id_delete

        
        """
        query_string = [('dry_run', True)]
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/api/v1/voter/{ID}'.format(ID=56),
            method='DELETE',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_voter_id_elections_get(self):
        """Test case for voter_id_elections_get

        
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/api/v1/voter/{ID}/elections'.format(ID=56),
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_voter_id_get(self):
        """Test case for voter_id_get

        
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/api/v1/voter/{ID}'.format(ID=56),
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_voter_post(self):
        """Test case for voter_post

        
        """
        voter_base = {
  "name" : "name",
  "email" : "email"
}
        query_string = [('dry_run', True)]
        headers = { 
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/api/v1/voter',
            method='POST',
            headers=headers,
            data=json.dumps(voter_base),
            content_type='application/json',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
