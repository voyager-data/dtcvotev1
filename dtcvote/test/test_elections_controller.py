# coding: utf-8

from __future__ import absolute_import
import unittest

from flask import json
from six import BytesIO

from dtcvote.models.election_request import ElectionRequest  # noqa: E501
from dtcvote.models.election_response import ElectionResponse  # noqa: E501
from dtcvote.models.election_search_response import ElectionSearchResponse  # noqa: E501
from dtcvote.models.error import Error  # noqa: E501
from dtcvote.models.voter_response import VoterResponse  # noqa: E501
from dtcvote.test import BaseTestCase


class TestElectionsController(BaseTestCase):
    """ElectionsController integration test stubs"""

    def test_election_get(self):
        """Test case for election_get

        
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/api/v1/election',
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_election_id_close_get(self):
        """Test case for election_id_close_get

        
        """
        query_string = [('dry_run', True)]
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/api/v1/election/{ID}/close'.format(ID=56),
            method='GET',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_election_id_count_get(self):
        """Test case for election_id_count_get

        
        """
        query_string = [('dry_run', True),
                        ('recount', True)]
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/api/v1/election/{ID}/count'.format(ID=56),
            method='GET',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_election_id_delete(self):
        """Test case for election_id_delete

        
        """
        query_string = [('dry_run', True)]
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/api/v1/election/{ID}'.format(ID=56),
            method='DELETE',
            headers=headers,
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

    def test_election_id_get(self):
        """Test case for election_id_get

        
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/api/v1/election/{ID}'.format(ID=56),
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_election_id_open_get(self):
        """Test case for election_id_open_get

        
        """
        query_string = [('dry_run', True)]
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/api/v1/election/{ID}/open'.format(ID=56),
            method='GET',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_election_id_put(self):
        """Test case for election_id_put

        
        """
        election_request = null
        query_string = [('dry_run', True)]
        headers = { 
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/api/v1/election/{ID}'.format(ID=56),
            method='PUT',
            headers=headers,
            data=json.dumps(election_request),
            content_type='application/json',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

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

    def test_election_post(self):
        """Test case for election_post

        
        """
        election_request = [{"questions": [{"candidates": [{"candidate_sequence": 1, "name": "Helen of Troy"}, {"candidate_sequence": 2, "name": "Aphrodite"}, {"candidate_sequence": 3, "name": "The Wicked Queen"}], "algorithm_id": 1, "name": "Who is the fairest one of all?", "number_of_winners": 1, "question_sequence": 0, "randomize_candidates": True}], "deadline": "2021-03-28T01:10:08.107Z", "name": "DTC Test", "not_voted_email": "you have not voted", "secret_ballot": False, "vote_email": "you must vote", "voted_email": "you voted"}]
        query_string = [('dry_run', True)]
        headers = { 
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/api/v1/election',
            method='POST',
            headers=headers,
            data=json.dumps(election_request),
            content_type='application/json',
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


if __name__ == '__main__':
    unittest.main()
