# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack Foundation.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from quantum.api import extensions
from quantum.api.v2 import base
from quantum.common import exceptions
from quantum.db import servicetype_db
from quantum.extensions import servicetype
from quantum import manager
from quantum.openstack.common import uuidutils
from quantum.plugins.common import constants
from quantum.plugins.services.service_base import ServicePluginBase


DUMMY_PLUGIN_NAME = "dummy_plugin"
RESOURCE_NAME = "dummy"
COLLECTION_NAME = "%ss" % RESOURCE_NAME

# Attribute Map for dummy resource
RESOURCE_ATTRIBUTE_MAP = {
    COLLECTION_NAME: {
        'id': {'allow_post': False, 'allow_put': False,
               'validate': {'type:uuid': None},
               'is_visible': True},
        'name': {'allow_post': True, 'allow_put': True,
                 'validate': {'type:string': None},
                 'is_visible': True, 'default': ''},
        'tenant_id': {'allow_post': True, 'allow_put': False,
                      'required_by_policy': True,
                      'is_visible': True},
        'service_type': {'allow_post': True,
                         'allow_put': False,
                         'validate': {'type:servicetype_ref': None},
                         'convert_to': servicetype.set_default_svctype_id,
                         'is_visible': True,
                         'default': None}
    }
}


class Dummy(object):

    @classmethod
    def get_name(cls):
        return "dummy"

    @classmethod
    def get_alias(cls):
        return "dummy"

    @classmethod
    def get_description(cls):
        return "Dummy stuff"

    @classmethod
    def get_namespace(cls):
        return "http://docs.openstack.org/ext/quantum/dummy/api/v1.0"

    @classmethod
    def get_updated(cls):
        return "2012-11-20T10:00:00-00:00"

    @classmethod
    def get_resources(cls):
        """Returns Extended Resource for dummy management."""
        q_mgr = manager.QuantumManager.get_instance()
        dummy_inst = q_mgr.get_service_plugins()['DUMMY']
        controller = base.create_resource(
            COLLECTION_NAME, RESOURCE_NAME, dummy_inst,
            RESOURCE_ATTRIBUTE_MAP[COLLECTION_NAME])
        return [extensions.ResourceExtension(COLLECTION_NAME,
                                             controller)]


class DummyServicePlugin(ServicePluginBase):
    """This is a simple plugin for managing instantes of a fictional 'dummy'
        service. This plugin is provided as a proof-of-concept of how
        advanced service might leverage the service type extension.
        Ideally, instances of real advanced services, such as load balancing
        or VPN will adopt a similar solution.
    """

    supported_extension_aliases = ['dummy', servicetype.EXT_ALIAS]

    def __init__(self):
        self.svctype_mgr = servicetype_db.ServiceTypeManager.get_instance()
        self.dummys = {}

    def get_plugin_type(self):
        return constants.DUMMY

    def get_plugin_name(self):
        return DUMMY_PLUGIN_NAME

    def get_plugin_description(self):
        return "Quantum Dummy Service Plugin"

    def get_dummys(self, context, filters, fields):
        return self.dummys.values()

    def get_dummy(self, context, id, fields):
        try:
            return self.dummys[id]
        except KeyError:
            raise exceptions.NotFound()

    def create_dummy(self, context, dummy):
        d = dummy['dummy']
        d['id'] = uuidutils.generate_uuid()
        self.dummys[d['id']] = d
        self.svctype_mgr.increase_service_type_refcount(context,
                                                        d['service_type'])
        return d

    def update_dummy(self, context, id, dummy):
        pass

    def delete_dummy(self, context, id):
        try:
            svc_type_id = self.dummys[id]['service_type']
            del self.dummys[id]
            self.svctype_mgr.decrease_service_type_refcount(context,
                                                            svc_type_id)
        except KeyError:
            raise exceptions.NotFound()
