
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


from xosapi.orm import ORMWrapper, register_convenience_wrapper

class ORMWrapperVEEServiceInstance(ORMWrapper):
    @property
    def veg(self):
        links = self.stub.ServiceInstanceLink.objects.filter(subscriber_service_instance_id = self.id)
        for link in links:
            # cast from ServiceInstance to VSGTenant
            vegs = self.stub.VEGTenant.objects.filter(id = link.provider_service_instance.id)
            if vegs:
                return vegs[0]
        return None

    # DEPRECATED
    @property
    def vcpe(self):
        return self.veg

    # DEPRECATED
    @property
    def vsg(Self):
        return self.veg

    @property
    def subscriber(self):
        links = self.stub.ServiceInstanceLink.objects.filter(provider_service_instance_id = self.id)
        for link in links:
            # assume the only thing that links to a VEE must be a subscriber
            if link.subscriber_service_instance:
                return link.subscriber_service_instance.leaf_model
        return None

register_convenience_wrapper("VEEServiceInstance", ORMWrapperVEEServiceInstance)
