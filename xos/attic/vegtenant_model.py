
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


sync_attributes = ("wan_container_ip", "wan_container_mac", "wan_container_netbits",
                   "wan_container_gateway_ip", "wan_container_gateway_mac",
                   "wan_vm_ip", "wan_vm_mac")


def __init__(self, *args, **kwargs):
    super(VEGTenant, self).__init__(*args, **kwargs)
    self.cached_vrouter=None

@property
def vrouter(self):
    vrouter = self.get_newest_subscribed_tenant(VRouterTenant)
    if not vrouter:
        return None

    # always return the same object when possible
    if (self.cached_vrouter) and (self.cached_vrouter.id == vrouter.id):
        return self.cached_vrouter

    vrouter.caller = self.creator
    self.cached_vrouter = vrouter
    return vrouter

@vrouter.setter
def vrouter(self, value):
    raise XOSConfigurationError("vEGTenant.vrouter setter is not implemented")

@property
def volt(self):
    from services.volt.models import VOLTTenant
    if not self.subscriber_tenant:
        return None
    volts = VOLTTenant.objects.filter(id=self.subscriber_tenant.id)
    if not volts:
        return None
    return volts[0]

@volt.setter
def volt(self, value):
    raise XOSConfigurationError("VEGTenant.volt setter is not implemented")

@property
def ssh_command(self):
    if self.instance:
        return self.instance.get_ssh_command()
    else:
        return "no-instance"

def get_vrouter_field(self, name, default=None):
    if self.vrouter:
        return getattr(self.vrouter, name, default)
    else:
        return default

@property
def wan_container_ip(self):
    return self.get_vrouter_field("public_ip", None)

@property
def wan_container_mac(self):
    return self.get_vrouter_field("public_mac", None)

@property
def wan_container_netbits(self):
    return self.get_vrouter_field("netbits", None)

@property
def wan_container_gateway_ip(self):
    return self.get_vrouter_field("gateway_ip", None)

@property
def wan_container_gateway_mac(self):
    return self.get_vrouter_field("gateway_mac", None)

@property
def wan_vm_ip(self):
    tags = Tag.select_by_content_object(self.instance).filter(name="vm_vrouter_tenant")
    if tags:
        tenant = VRouterTenant.objects.get(id=tags[0].value)
        return tenant.public_ip
    else:
        raise Exception("no vm_vrouter_tenant tag for instance %s" % o.instance)

@property
def wan_vm_mac(self):
    tags = Tag.select_by_content_object(self.instance).filter(name="vm_vrouter_tenant")
    if tags:
        tenant = VRouterTenant.objects.get(id=tags[0].value)
        return tenant.public_mac
    else:
        raise Exception("no vm_vrouter_tenant tag for instance %s" % o.instance)

@property
def is_synced(self):
    return (self.enacted is not None) and (self.enacted >= self.updated)

@is_synced.setter
def is_synced(self, value):
    pass

def get_vrouter_service(self):
    vrouterServices = VRouterService.get_service_objects().all()
    if not vrouterServices:
        raise XOSConfigurationError("No VROUTER Services available")
    return vrouterServices[0]

def manage_vrouter(self):
    # Each vEG object owns exactly one vRouterTenant object

    if self.deleted:
        return

    if self.vrouter is None:
        vrouter = self.get_vrouter_service().get_tenant(address_pool_name="addresses_veg", subscriber_tenant = self)
        vrouter.caller = self.creator
        vrouter.save()

def cleanup_vrouter(self):
    if self.vrouter:
        # print "XXX cleanup vrouter", self.vrouter
        self.vrouter.delete()

def cleanup_orphans(self):
    # ensure vEG only has one vRouter
    cur_vrouter = self.vrouter
    for vrouter in list(self.get_subscribed_tenants(VRouterTenant)):
        if (not cur_vrouter) or (vrouter.id != cur_vrouter.id):
            # print "XXX clean up orphaned vrouter", vrouter
            vrouter.delete()

    if self.orig_instance_id and (self.orig_instance_id != self.get_attribute("instance_id")):
        instances=Instance.objects.filter(id=self.orig_instance_id)
        if instances:
            # print "XXX clean up orphaned instance", instances[0]
            instances[0].delete()

def get_slice(self):
    if not self.provider_service.slices.count():
        print self, "dio porco"
        raise XOSConfigurationError("The service has no slices")
    slice = self.provider_service.slices.all()[0]
    return slice

def get_veg_service(self):
    return VEGService.get_service_objects().get(id=self.provider_service.id)

def find_instance_for_s_tag(self, s_tag):
    #s_tags = STagBlock.objects.find(s_s_tag)
    #if s_tags:
    #    return s_tags[0].instance

    tags = Tag.objects.filter(name="s_tag", value=s_tag)
    if tags:
        return tags[0].content_object

    return None

def find_or_make_instance_for_s_tag(self, s_tag):
    instance = self.find_instance_for_s_tag(self.volt.s_tag)
    if instance:
        return instance

    flavors = Flavor.objects.filter(name="m1.small")
    if not flavors:
        raise XOSConfigurationError("No m1.small flavor")

    slice = self.provider_service.slices.all()[0]

    if slice.default_isolation == "container_vm":
        (node, parent) = ContainerVmScheduler(slice).pick()
    else:
        (node, parent) = LeastLoadedNodeScheduler(slice, label=self.get_veg_service().node_label).pick()

    instance = Instance(slice = slice,
                    node = node,
                    image = self.image,
                    creator = self.creator,
                    deployment = node.site_deployment.deployment,
                    flavor = flavors[0],
                    isolation = slice.default_isolation,
                    parent = parent)

    self.save_instance(instance)

    return instance

def manage_container(self):
    from core.models import Instance, Flavor

    if self.deleted:
        return

    # For container or container_vm isolation, use what TenantWithCotnainer
    # provides us
    slice = self.get_slice()
    if slice.default_isolation in ["container_vm", "container"]:
        super(VEGTenant,self).manage_container()
        return

    if not self.volt:
        raise XOSConfigurationError("This vEG container has no volt")

    if self.instance:
        # We're good.
        return

    instance = self.find_or_make_instance_for_s_tag(self.volt.s_tag)
    self.instance = instance
    super(TenantWithContainer, self).save()

def cleanup_container(self):
    if self.get_slice().default_isolation in ["container_vm", "container"]:
        super(VEGTenant,self).cleanup_container()

    # To-do: cleanup unused instances
    pass

def find_or_make_port(self, instance, network, **kwargs):
    port = Port.objects.filter(instance=instance, network=network)
    if port:
        port = port[0]
    else:
        port = Port(instance=instance, network=network, **kwargs)
        port.save()
    return port

def get_lan_network(self, instance):
    slice = self.provider_service.slices.all()[0]
    # there should only be one network private network, and its template should not be the management template
    lan_networks = [x for x in slice.networks.all() if x.template.visibility == "private" and (not "management" in x.template.name)]
    if len(lan_networks) > 1:
        raise XOSProgrammingError("The vEG slice should only have one non-management private network")
    if not lan_networks:
        raise XOSProgrammingError("No lan_network")
    return lan_networks[0]

def save_instance(self, instance):
    with transaction.atomic():
        instance.volumes = "/etc/dnsmasq.d,/etc/ufw"
        super(VEGTenant, self).save_instance(instance)

        if instance.isolation in ["container", "container_vm"]:
            lan_network = self.get_lan_network(instance)
            port = self.find_or_make_port(instance, lan_network, ip="192.168.0.1", port_id="unmanaged")
            port.set_parameter("c_tag", self.volt.c_tag)
            port.set_parameter("s_tag", self.volt.s_tag)
            port.set_parameter("device", "eth1")
            port.set_parameter("bridge", "br-lan")

            wan_networks = [x for x in instance.slice.networks.all() if "wan" in x.name]
            if not wan_networks:
                raise XOSProgrammingError("No wan_network")
            port = self.find_or_make_port(instance, wan_networks[0])
            port.set_parameter("next_hop", value="10.0.1.253")   # FIX ME
            port.set_parameter("device", "eth0")

        if instance.isolation in ["vm"]:
            lan_network = self.get_lan_network(instance)
            port = self.find_or_make_port(instance, lan_network)
            port.set_parameter("c_tag", self.volt.c_tag)
            port.set_parameter("s_tag", self.volt.s_tag)
            port.set_parameter("neutron_port_name", "stag-%s" % self.volt.s_tag)
            port.save()

        # tag the instance with the s-tag, so we can easily find the
        # instance later
        if self.volt and self.volt.s_tag:
            tags = Tag.objects.filter(name="s_tag", value=self.volt.s_tag)
            if not tags:
                tag = Tag(service=self.provider_service, content_object=instance, name="s_tag", value=self.volt.s_tag)
                tag.save()

        # VTN-CORD needs a WAN address for the VM, so that the VM can
        # be configured.
        tags = Tag.select_by_content_object(instance).filter(name="vm_vrouter_tenant")

        if not tags:
            vrouter = self.get_vrouter_service().get_tenant(address_pool_name="addresses_veg", subscriber_service=self.provider_service)
            vrouter.set_attribute("tenant_for_instance_id", instance.id)
            vrouter.save()
            tag = Tag(service=self.provider_service, content_object=instance, name="vm_vrouter_tenant",value="%d" % vrouter.id)
            tag.save()

def __xos_save_base(self, *args, **kwargs):
    if not self.creator:
        if not getattr(self, "caller", None):
            # caller must be set when creating a vEG since it creates a slice
            raise XOSProgrammingError("VEGTenant's self.caller was not set")
        self.creator = self.caller
        if not self.creator:
            raise XOSProgrammingError("VEGTenant's self.creator was not set")

    super(VEGTenant, self).save(*args, **kwargs)
    model_policy_veg(self.pk)
    return True     # Indicate that we called super.save()

def delete(self, *args, **kwargs):
    self.cleanup_vrouter()
    self.cleanup_container()
    super(VEGTenant, self).delete(*args, **kwargs)

