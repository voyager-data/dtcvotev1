# coding: utf-8

from __future__ import absolute_import
import unittest

from flask import json
from six import BytesIO

from dtcvote.models.algorithm_response import AlgorithmResponse  # noqa: E501
from dtcvote.models.error import Error  # noqa: E501
from dtcvote.test import BaseTestCase


class TestAlgorithmsController(BaseTestCase):
    """AlgorithmsController integration test stubs"""

    def test_algorithm_get(self):
        """Test case for algorithm_get

        
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/api/v1/algorithm',
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_algorithm_id_get(self):
        """Test case for algorithm_id_get

        
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/api/v1/algorithm/{ID}'.format(ID=56),
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
