
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


from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework import serializers
from rest_framework import generics
from rest_framework import status
from core.models import *
from django.forms import widgets
from services.veg.models import VEGTenant, VEGService
from xos.apibase import XOSListCreateAPIView, XOSRetrieveUpdateDestroyAPIView, XOSPermissionDenied
from api.xosapi_helpers import PlusModelSerializer, XOSViewSet, ReadOnlyField

def get_default_veg_service():
    VEG_services = VEGService.get_service_objects().all()
    if VEG_services:
        return VEG_services[0].id
    return None

class VEGTenantForAPI(VEGTenant):
    class Meta:
        proxy = True
        app_label = "cord"

    @property
    def related(self):
        related = {}
        if self.instance:
            related["instance_id"] = self.instance.id
        return related

class VEGTenantSerializer(PlusModelSerializer):
    id = ReadOnlyField()
    wan_container_ip = serializers.CharField()
    wan_container_mac = ReadOnlyField()
    related = serializers.DictField(required=False)

    humanReadableName = serializers.SerializerMethodField("getHumanReadableName")
    class Meta:
        model = VEGTenantForAPI
        fields = ('humanReadableName', 'id', 'wan_container_ip', 'wan_container_mac', 'related' )

    def getHumanReadableName(self, obj):
        return obj.__unicode__()

class VEGTenantViewSet(XOSViewSet):
    base_name = "veg"
    method_name = "veg"
    method_kind = "viewset"
    queryset = VEGTenantForAPI.get_tenant_objects().all()
    serializer_class = VEGTenantSerializer

    @classmethod
    def get_urlpatterns(self, api_path="^"):
        patterns = super(VEGTenantViewSet, self).get_urlpatterns(api_path=api_path)

        return patterns






