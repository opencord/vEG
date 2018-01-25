
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


def model_policy_veg(pk):
    # TODO: this should be made in to a real model_policy
    with transaction.atomic():
        veg = VEGTenant.objects.select_for_update().filter(pk=pk)
        if not veg:
            return
        veg = veg[0]
        veg.manage_container()
        veg.manage_vrouter()
        veg.cleanup_orphans()


