# coding: utf-8

from __future__ import absolute_import
import unittest

from flask import json
from six import BytesIO

from dtcvote.models.error import Error  # noqa: E501
from dtcvote.test import BaseTestCase


class TestCountingController(BaseTestCase):
    """CountingController integration test stubs"""

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

    def test_question_id_blt_get(self):
        """Test case for question_id_blt_get

        
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/api/v1/question/{ID}/blt'.format(ID=56),
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
