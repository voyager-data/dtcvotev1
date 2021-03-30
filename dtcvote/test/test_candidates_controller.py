# coding: utf-8

from __future__ import absolute_import
import unittest

from flask import json
from six import BytesIO

from dtcvote.models.error import Error  # noqa: E501
from dtcvote.test import BaseTestCase


class TestCandidatesController(BaseTestCase):
    """CandidatesController integration test stubs"""

    def test_candidate_id_delete(self):
        """Test case for candidate_id_delete

        
        """
        query_string = [('dry_run', True)]
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/api/v1/candidate/{ID}'.format(ID=56),
            method='DELETE',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
