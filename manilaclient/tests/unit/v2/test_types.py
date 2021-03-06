# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import ddt
import mock

from manilaclient.tests.unit import utils
from manilaclient.tests.unit.v2 import fakes
from manilaclient.v2 import share_types

cs = fakes.FakeClient()


@ddt.ddt
class TypesTest(utils.TestCase):

    @ddt.data(
        {'snapshot_support': 'False'},
        {'snapshot_support': 'False', 'foo': 'bar'},
    )
    def test_init(self, extra_specs):
        info = {'extra_specs': {'snapshot_support': 'False'}}

        share_type = share_types.ShareType(share_types.ShareTypeManager, info)

        self.assertTrue(hasattr(share_type, '_required_extra_specs'))
        self.assertTrue(hasattr(share_type, '_optional_extra_specs'))
        self.assertTrue(isinstance(share_type._required_extra_specs, dict))
        self.assertTrue(isinstance(share_type._optional_extra_specs, dict))
        self.assertEqual(
            {'snapshot_support': 'False'}, share_type.get_optional_keys())

    def test_list_types(self):
        tl = cs.share_types.list()
        cs.assert_called('GET', '/types?is_public=all')
        for t in tl:
            self.assertIsInstance(t, share_types.ShareType)
            self.assertTrue(callable(getattr(t, 'get_required_keys', '')))
            self.assertTrue(callable(getattr(t, 'get_optional_keys', '')))
            self.assertEqual({'test': 'test'}, t.get_required_keys())
            self.assertEqual(
                {'snapshot_support': 'unknown'}, t.get_optional_keys())

    def test_list_types_only_public(self):
        cs.share_types.list(show_all=False)
        cs.assert_called('GET', '/types')

    @ddt.data(
        (True, True, True),
        (True, True, False),
        (True, False, True),
        (False, True, True),
        (True, False, False),
        (False, False, True),
        (False, True, False),
        (False, False, False),
    )
    @ddt.unpack
    def test_create(self, is_public, dhss, snapshot_support):
        expected_body = {
            "share_type": {
                "name": 'test-type-3',
                'os-share-type-access:is_public': is_public,
                "extra_specs": {
                    "driver_handles_share_servers": dhss,
                    "snapshot_support": snapshot_support,
                }
            }
        }

        result = cs.share_types.create(
            'test-type-3', dhss, snapshot_support, is_public=is_public)
        cs.assert_called('POST', '/types', expected_body)
        self.assertIsInstance(result, share_types.ShareType)

    @ddt.data(True, False)
    def test_create_with_default_values(self, dhss):
        expected_body = {
            "share_type": {
                "name": 'test-type-3',
                'os-share-type-access:is_public': True,
                "extra_specs": {
                    "driver_handles_share_servers": dhss,
                    "snapshot_support": True,
                }
            }
        }

        result = cs.share_types.create('test-type-3', dhss)
        cs.assert_called('POST', '/types', expected_body)
        self.assertIsInstance(result, share_types.ShareType)

    def test_set_key(self):
        t = cs.share_types.get(1)
        t.set_keys({'k': 'v'})
        cs.assert_called('POST',
                         '/types/1/extra_specs',
                         {'extra_specs': {'k': 'v'}})

    def test_unsset_keys(self):
        t = cs.share_types.get(1)
        t.unset_keys(['k'])
        cs.assert_called('DELETE', '/types/1/extra_specs/k')

    def test_delete(self):
        cs.share_types.delete(1)
        cs.assert_called('DELETE', '/types/1')

    def test_get_keys_from_resource_data(self):
        manager = mock.Mock()
        manager.api.client.get = mock.Mock(return_value=(200, {}))
        valid_extra_specs = {'test': 'test'}
        share_type = share_types.ShareType(mock.Mock(),
                                           {'extra_specs': valid_extra_specs,
                                            'name': 'test'},
                                           loaded=True)

        actual_result = share_type.get_keys()

        self.assertEqual(actual_result, valid_extra_specs)
        self.assertEqual(manager.api.client.get.call_count, 0)

    @ddt.data({'prefer_resource_data': True,
               'resource_extra_specs': {}},
              {'prefer_resource_data': False,
               'resource_extra_specs': {'fake': 'fake'}},
              {'prefer_resource_data': False,
              'resource_extra_specs': {}})
    @ddt.unpack
    def test_get_keys_from_api(self, prefer_resource_data,
                               resource_extra_specs):
        manager = mock.Mock()
        valid_extra_specs = {'test': 'test'}
        manager.api.client.get = mock.Mock(
            return_value=(200, {'extra_specs': valid_extra_specs}))
        info = {
            'name': 'test',
            'uuid': 'fake',
            'extra_specs': resource_extra_specs
        }
        share_type = share_types.ShareType(manager, info, loaded=True)

        actual_result = share_type.get_keys(prefer_resource_data)

        self.assertEqual(actual_result, valid_extra_specs)
        self.assertEqual(manager.api.client.get.call_count, 1)
