
# Copyright 2017-present Open Networking Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import unittest
from mock import patch, call, Mock, PropertyMock
import mock

import os, sys

test_path=os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
service_dir=os.path.join(test_path, "../../../..")
xos_dir=os.path.join(test_path, "../../..")
if not os.path.exists(os.path.join(test_path, "new_base")):
    xos_dir=os.path.join(test_path, "../../../../../../orchestration/xos/xos")
    services_dir=os.path.join(xos_dir, "../../xos_services")

# While transitioning from static to dynamic load, the path to find neighboring xproto files has changed. So check
# both possible locations...
def get_models_fn(service_name, xproto_name):
    name = os.path.join(service_name, "xos", xproto_name)
    if os.path.exists(os.path.join(services_dir, name)):
        return name
    else:
        name = os.path.join(service_name, "xos", "synchronizer", "models", xproto_name)
        if os.path.exists(os.path.join(services_dir, name)):
            return name
    raise Exception("Unable to find service=%s xproto=%s" % (service_name, xproto_name))

class TestModelPolicyVsgTenant(unittest.TestCase):
    def setUp(self):
        global VEGTenantPolicy, LeastLoadedNodeScheduler, MockObjectList

        self.sys_path_save = sys.path
        sys.path.append(xos_dir)
        sys.path.append(os.path.join(xos_dir, 'synchronizers', 'new_base'))

        config = os.path.join(test_path, "test_config.yaml")
        from xosconfig import Config
        Config.clear()
        Config.init(config, 'synchronizer-config-schema.yaml')

        from synchronizers.new_base.mock_modelaccessor_build import build_mock_modelaccessor
        build_mock_modelaccessor(xos_dir, services_dir, [get_models_fn("vEG", "veg.xproto"),
                                                         get_models_fn("addressmanager", "addressmanager.xproto")])

        import synchronizers.new_base.modelaccessor
        import synchronizers.new_base.model_policies.model_policy_tenantwithcontainer
        import model_policy_vegtenant
        from model_policy_vegtenant import VEGTenantPolicy, model_accessor
        from synchronizers.new_base.model_policies.model_policy_tenantwithcontainer import LeastLoadedNodeScheduler

        from mock_modelaccessor import MockObjectList

        # import all class names to globals
        for (k, v) in model_accessor.all_model_classes.items():
            globals()[k] = v

        # Some of the functions we call have side-effects. For example, creating a VEGTenant may lead to creation of
        # tags. Ideally, this wouldn't happen, but it does. So make sure we reset the world.
        model_accessor.reset_all_object_stores()

        # attic functions that are not present in the mock model accessor
        VEGTenant.volt = PropertyMock(return_value = None)
        AddressManagerServiceInstance.set_attribute = Mock()

        self.policy = VEGTenantPolicy()
        self.tenant = VEGTenant()
        self.user = User(email="testadmin@test.org")
        self.tenant = VEGTenant(creator=self.user, id=1)
        self.flavor = Flavor(name="m1.small")
        self.npt_ctag = NetworkParameterType(name="c_tag", id=1)
        self.npt_stag = NetworkParameterType(name="s_tag", id=2)
        self.npt_neutron_port_name = NetworkParameterType(name="neutron_port_name", id=3)
        self.node = Node(hostname="my.node.com")
        self.slice = Slice(name="mysite_test1", default_flavor=self.flavor, default_isolation="vm")
        self.priv_template = NetworkTemplate(name="access_network", visibility="private")
        self.priv_network = Network(name="mysite_test1_private", template=self.priv_template)
        self.image = Image(name="trusty-server-multi-nic")
        self.deployment = Deployment(name="testdeployment")
        Tag.objects.item_list = []

    def tearDownb(self):
        sys.path = self.sys_path_save

    def test_handle_create(self):
        with patch.object(VEGTenantPolicy, "manage_container") as manage_container, \
             patch.object(VEGTenantPolicy, "manage_address_service_instance") as manage_address_service_instance, \
             patch.object(VEGTenantPolicy, "cleanup_orphans") as cleanup_orphans:
            self.policy.handle_create(self.tenant)
            manage_container.assert_called_with(self.tenant)
            manage_address_service_instance.assert_called_with(self.tenant)
            cleanup_orphans.assert_called_with(self.tenant)

    def test_handle_update(self):
        with patch.object(VEGTenantPolicy, "manage_container") as manage_container, \
             patch.object(VEGTenantPolicy, "manage_address_service_instance") as manage_address_service_instance, \
             patch.object(VEGTenantPolicy, "cleanup_orphans") as cleanup_orphans:
            self.policy.handle_create(self.tenant)
            manage_container.assert_called_with(self.tenant)
            manage_address_service_instance.assert_called_with(self.tenant)
            cleanup_orphans.assert_called_with(self.tenant)

    def test_handle_delete_asi_exist(self):
        with patch.object(AddressManagerServiceInstance, "delete") as amsi_delete:
            vrtenant = AddressManagerServiceInstance()
            self.tenant.address_service_instance = vrtenant
            self.policy.handle_delete(self.tenant)
            # The delete model policy should be called.
            #   NOTE: This will change when vEG is brought up to compliance with R-CORD vSG. See comments in VSG
            #         model policy test case.
            amsi_delete.assert_called()

    def test_handle_delete_asi_noexist(self):
        with patch.object(AddressManagerServiceInstance, "delete") as amsi_delete:
            self.tenant.address_service_instance = None
            self.policy.handle_delete(self.tenant)
            amsi_delete.assert_not_called()

# TODO: vEG doesn't currently implement this functionality

#    def test_handle_delete_cleaup_instance(self):
#        with patch.object(VEGTenant.objects, "get_items") as vegtenant_objects, \
#             patch.object(Instance.objects, "get_items") as instance_objects, \
#             patch.object(Instance, "delete") as instance_delete:
#            veg_service = VEGService()
#            instance = Instance(id=1)
#            instance_objects.return_value = [instance]
#            self.tenant.address_service_instance = None
#            self.tenant.instance = instance
#            self.tenant.instance_id = instance.id
#            self.tenant.owner = veg_service
#            vegtenant_objects.return_value = [self.tenant]
#            self.policy.handle_delete(self.tenant)
#            instance_delete.assert_called()

# TODO: vEG doesn't currently implement this functionality

#    def test_handle_delete_cleanup_instance_live(self):
#        with patch.object(VEGTenant.objects, "get_items") as vegtenant_objects, \
#             patch.object(Instance.objects, "get_items") as instance_objects, \
#             patch.object(Instance, "delete") as instance_delete:
#            # Make sure if an Instance still has active VSG Tenants, that we don't clean it up
#            veg_service = VEGService()
#            instance = Instance(id=1)
#            instance_objects.return_value = [instance]
#            self.tenant.address_service_instance = None
#            self.tenant.instance = instance
#            self.tenant.instance_id = instance.id
#            self.tenant.owner = veg_service
#
#            other_tenant = VEGTenant()
#            other_tenant.address_service_instance = None
#            other_tenant.instance = instance
#            other_tenant.instance_id = instance.id
#            other_tenant.owner = veg_service
#
#            vegtenant_objects.return_value = [self.tenant, other_tenant]
#
#            self.policy.handle_delete(self.tenant)
#            instance_delete.assert_not_called()


# TODO: vEG doesn't currently implement this functionality

#    def test_handle_delete_cleanup_instance_and_tags_and_stuff(self):
#        with patch.object(ServiceInstance.objects, "get_items") as si_objects, \
#             patch.object(AddressManagerServiceInstance.objects, "get_items") as amsi_objects, \
#             patch.object(Tag.objects, "get_items") as tag_objects, \
#             patch.object(VEGTenant.objects, "get_items") as vegtenant_objects, \
#             patch.object(Instance.objects, "get_items") as instance_objects, \
#             patch.object(AddressManagerServiceInstance, "delete") as amsi_delete, \
#             patch.object(Tag, "delete") as tag_delete, \
#             patch.object(Instance, "delete") as instance_delete:
#            veg_service = VEGService()
#            am_instance = AddressManagerServiceInstance()
#            amsi_objects.return_value = [am_instance]
#            si_objects.return_value = [am_instance]  # AddressManagerServiceInstance is a subclass of ServiceInstance
#            instance = Instance(id=1)
#            instance_objects.return_value = [instance]
#            self.tenant.address_service_instance = None
#            self.tenant.instance = instance
#            self.tenant.instance_id = instance.id
#            self.tenant.owner = veg_service
#            vegtenant_objects.return_value = [self.tenant]
#            stag_tag = Tag(service_id=self.tenant.owner.id, content_type=instance.self_content_type_id,
#                           object_id=instance.id, name="s_tag")
#            vrouter_tag = Tag(service_id=self.tenant.owner.id, content_type=instance.self_content_type_id,
#                           object_id=instance.id, name="vm_vrouter_tenant", value=am_instance.id)
#            tag_objects.return_value = [stag_tag, vrouter_tag]
#            self.policy.handle_delete(self.tenant)
#            instance_delete.assert_called()
#            assert stag_tag.delete.called
#            assert vrouter_tag.delete.called
#            assert am_instance.delete.called

    def test_cleanup_orphans(self):
        with patch.object(AddressManagerServiceInstance.objects, "get_items") as amsi_objects, \
             patch.object(AddressManagerServiceInstance, "delete") as amsi_delete:
            vrtenant = AddressManagerServiceInstance(id=1)
            self.tenant.address_service_instance = vrtenant
            some_other_vrtenant = AddressManagerServiceInstance(id=2)
            link = ServiceInstanceLink(subscriber_service_instance=self.tenant, provider_service_instance=some_other_vrtenant)
            self.tenant.subscribed_links = MockObjectList(initial=[link])
            amsi_objects.return_value = [some_other_vrtenant]
            self.policy.cleanup_orphans(self.tenant)
            amsi_delete.assert_called()

    def test_find_instance_for_s_tag_noexist(self):
        with patch.object(Tag.objects, "get_items") as tag_objects:
            tag_objects.filter.return_value = []
            instance = self.policy.find_instance_for_s_tag(3)
            self.assertEqual(instance, None)

    def test_find_instance_for_s_tag(self):
        with patch.object(Tag, "objects") as tag_objects:
            tagged_instance = Instance()
            tag = Tag(content_object = tagged_instance)
            tag_objects.filter.return_value = [tag]
            instance = self.policy.find_instance_for_s_tag(3)
            self.assertEqual(instance, tagged_instance)

    def test_manage_container_no_volt(self):
        with self.assertRaises(Exception) as e:
            self.policy.manage_container(self.tenant)
        self.assertEqual(e.exception.message, "This VEG container has no volt")

    def test_manage_container_noinstance(self):
        with patch.object(VEGTenantPolicy, "find_or_make_instance_for_s_tag") as find_or_make_instance_for_s_tag, \
             patch.object(VEGTenant, "save") as tenant_save, \
             patch.object(VEGTenant, "volt") as volt:
            instance = Instance()
            volt.s_tag=222
            volt.c_tag=111
            find_or_make_instance_for_s_tag.return_value = instance
            self.policy.manage_container(self.tenant)
            self.assertEqual(self.tenant.instance, instance)
            tenant_save.assert_called()

    def test_manage_container_hasinstance(self):
        with patch.object(VEGTenantPolicy, "find_or_make_instance_for_s_tag") as find_or_make_instance_for_s_tag, \
             patch.object(VEGTenant, "save") as tenant_save, \
             patch.object(VEGTenant, "volt") as volt:
            instance = Instance()
            volt.s_tag=222
            volt.c_tag=111
            self.tenant.instance = instance
            self.policy.manage_container(self.tenant)
            find_or_make_instance_for_s_tag.assert_not_called()
            self.assertEqual(self.tenant.instance, instance)
            tenant_save.assert_not_called()

    def test_manage_container_deleted(self):
        with patch.object(VEGTenantPolicy, "find_or_make_instance_for_s_tag") as find_or_make_instance_for_s_tag, \
             patch.object(VEGTenant, "save") as tenant_save, \
             patch.object(VEGTenant, "volt") as volt:
            self.tenant.deleted = True
            self.policy.manage_container(self.tenant)
            find_or_make_instance_for_s_tag.assert_not_called()
            tenant_save.assert_not_called()

    def test_find_or_make_port_noexist(self):
        with patch.object(Port, "save") as port_save, \
             patch.object(Port, "objects") as port_objects:
            instance = Instance(id=123)
            network = Instance(id=456)
            port_objects.filter.return_value = []
            port=self.policy.find_or_make_port(instance, network)
            self.assertNotEqual(port, None)
            port_save.assert_called()

    def test_find_or_make_port_exists(self):
        with patch.object(Port, "save") as port_save, \
             patch.object(Port, "objects") as port_objects:
            someport = Port()
            def mock_port_filter(network_id, instance_id):
                if (network_id==456) and (instance_id==123):
                    return [someport]
                return None
            instance = Instance(id=123)
            network = Instance(id=456)
            port_objects.filter.side_effect = mock_port_filter
            port=self.policy.find_or_make_port(instance, network)
            self.assertEqual(port, someport)
            port_save.assert_not_called()

    def test_get_lan_network_noexist(self):
        with patch.object(VEGService.objects, "get_items") as vegservice_objects:
            vegservice=VEGService(name="myvegservice", id=1, slices=MockObjectList(initial=[self.slice]))
            vegservice_objects.return_value = [vegservice]
            self.tenant.owner = vegservice
            self.slice.networks = MockObjectList()
            with self.assertRaises(Exception) as e:
                self.policy.get_lan_network(self.tenant, None)
            self.assertEqual(e.exception.message, "No lan_network")

    def test_get_lan_network(self):
        with patch.object(VEGService.objects, "get_items") as vegservice_objects:
            vegservice=VEGService(name="myvegservice", id=1, slices=MockObjectList(initial=[self.slice]))
            vegservice_objects.return_value = [vegservice]
            self.tenant.owner = vegservice
            self.slice.networks = MockObjectList([self.priv_network])
            lan_network = self.policy.get_lan_network(self.tenant, None)
            self.assertEqual(lan_network, self.priv_network)

    def test_get_lan_network_toomany(self):
        with patch.object(VEGService.objects, "get_items") as vegservice_objects:
            some_other_network = Network(name="mysite_test1_private", template=self.priv_template)
            vegservice=VEGService(name="myvegservice", id=1, slices=MockObjectList(initial=[self.slice]))
            vegservice_objects.return_value = [vegservice]
            self.tenant.owner = vegservice
            self.slice.networks = MockObjectList([self.priv_network, some_other_network])
            with self.assertRaises(Exception) as e:
                lan_network = self.policy.get_lan_network(self.tenant, None)
            self.assertEqual(e.exception.message, "The vEG slice should only have one non-management private network")

    def test_port_set_parameter_noparamexist(self):
        with patch.object(NetworkParameterType.objects, "get_items") as npt_objects:
            npt_objects.return_value = [self.npt_stag]
            port = Port()
            self.policy.port_set_parameter(port, "s_tag", "123")
            self.assertNotEqual(NetworkParameter.objects.all(), [])
            param = NetworkParameter.objects.first()
            self.assertEqual(param.value, "123")
            self.assertEqual(param.parameter, self.npt_stag)

    def test_port_set_parameter_paramexist(self):
        with patch.object(NetworkParameterType.objects, "get_items") as npt_objects, \
             patch.object(NetworkParameter.objects, "get_items") as np_objects:
            port = Port(id=1)
            np_orig = NetworkParameter(parameter_id=self.npt_stag.id, value="456", object_id=port.id, content_type=port.self_content_type_id)
            np_objects.return_value = [np_orig]
            npt_objects.return_value = [self.npt_stag]
            self.policy.port_set_parameter(port, "s_tag", "123")
            self.assertEqual(NetworkParameter.objects.count(), 1)
            param = NetworkParameter.objects.first()
            self.assertEqual(param.value, "123")

    def test_find_or_make_instance_for_s_tag(self):
        with patch.object(NetworkParameterType.objects, "get_items") as npt_objects, \
             patch.object(Node.objects, "get_items") as node_objects, \
             patch.object(Flavor.objects, "get_items") as flavor_objects, \
             patch.object(VEGService.objects, "get_items") as vegservice_objects, \
             patch.object(VEGTenant, "volt") as volt, \
             patch.object(VEGTenant, "save") as tenant_save, \
             patch.object(VEGTenantPolicy, "get_image") as get_image, \
             patch.object(VEGTenantPolicy, "allocate_public_service_instance") as get_psi, \
             patch.object(LeastLoadedNodeScheduler, "pick") as pick, \
             patch.object(Node, "site_deployment") as site_deployment, \
             patch.object(Instance, "save") as instance_save, \
             patch.object(Instance, "delete") as instance_delete, \
             patch.object(VEGTenantPolicy, "port_set_parameter") as port_set_parameter:
            # setup mocks
            vrtenant = AddressManagerServiceInstance(public_ip="1.2.3.4", public_mac="01:02:03:04:05:06")
            vegservice=VEGService(name="myvegservice", id=1, slices=MockObjectList(initial=[self.slice]))
            vegservice_objects.return_value = [vegservice]
            self.tenant.owner = vegservice
            volt.s_tag=222
            volt.c_tag=111
            get_image.return_value = self.image
            get_psi.return_value = vrtenant
            pick.return_value = (self.node, None)
            site_deployment.deployment = self.deployment
            flavor_objects.return_value=[self.flavor]
            node_objects.return_value=[self.node]
            npt_objects.return_value=[self.npt_stag, self.npt_ctag, self.npt_neutron_port_name]
            self.slice.networks = MockObjectList([self.priv_network])
            # done setup mocks

            # call the function under test
            instance = self.policy.find_or_make_instance_for_s_tag(self.tenant, volt.s_tag)

            # make sure Instance was created
            self.assertNotEqual(instance, None)
            self.assertEqual(instance.creator.email, "testadmin@test.org")
            self.assertEqual(instance.image.name, "trusty-server-multi-nic")
            self.assertEqual(instance.flavor.name, "m1.small")
            self.assertEqual(instance.isolation, "vm")
            self.assertEqual(instance.node.hostname, "my.node.com")
            self.assertEqual(instance.slice.name, "mysite_test1")
            self.assertEqual(instance.parent, None)
            instance_save.assert_called()
            instance_delete.assert_not_called()

            # Access Network Port should have tags to c-tag and s-tag
            port = Port.objects.first()
            self.assertEqual(port.instance, instance)
            self.assertEqual(port.network, self.priv_network)
            port_set_parameter.assert_has_calls([mock.call(port, "c_tag", 111),
                                                 mock.call(port, "s_tag", 222),
                                                 mock.call(port, "neutron_port_name", "stag-222")])

            # The instance should be tagged with the s-tag
            tag = Tag.objects.get(name="s_tag")
            self.assertEqual(tag.value, "222")
            self.assertEqual(tag.object_id, instance.id)

            # The instance should have a tag pointing to its address_service_instance
            tag = Tag.objects.get(name="vm_vrouter_tenant")
            self.assertNotEqual(tag.value, vrtenant.id)
            self.assertEqual(tag.object_id, instance.id)

            # Allocate_public_service_instance should have been called
            get_psi.assert_called()

    def test_manage_address_service_instance(self):
        with patch.object(VEGTenantPolicy, "allocate_public_service_instance") as get_psi:
            vrtenant = AddressManagerServiceInstance(public_ip="1.2.3.4", public_mac="01:02:03:04:05:06")
            get_psi.return_value = vrtenant

            self.tenant.vrouter = None

            self.policy.manage_address_service_instance(self.tenant)

            get_psi.assert_called_with(address_pool_name="addresses_veg", subscriber_tenant=self.tenant)

if __name__ == '__main__':
    unittest.main()

