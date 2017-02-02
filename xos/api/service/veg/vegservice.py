from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework import serializers
from rest_framework import generics
from rest_framework import viewsets
from rest_framework import status
from rest_framework.decorators import detail_route, list_route
from rest_framework.views import APIView
from core.models import *
from django.forms import widgets
from django.conf.urls import patterns, url
from services.veg.models import VEGService
from api.xosapi_helpers import PlusModelSerializer, XOSViewSet, ReadOnlyField
from django.shortcuts import get_object_or_404
from xos.apibase import XOSListCreateAPIView, XOSRetrieveUpdateDestroyAPIView, XOSPermissionDenied
from xos.exceptions import *
import json
import subprocess
from django.views.decorators.csrf import ensure_csrf_cookie

class VEGServiceForApi(VEGService):
    class Meta:
        proxy = True
        app_label = "cord"

    def __init__(self, *args, **kwargs):
        super(VEGServiceForApi, self).__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        super(VEGServiceForApi, self).save(*args, **kwargs)

    def __init__(self, *args, **kwargs):
        super(VEGService, self).__init__(*args, **kwargs)

class VEGServiceSerializer(PlusModelSerializer):
        id = ReadOnlyField()
        humanReadableName = serializers.SerializerMethodField("getHumanReadableName")
        wan_container_gateway_ip = serializers.CharField(required=False)
        wan_container_gateway_mac = serializers.CharField(required=False)
        dns_servers = serializers.CharField(required=False)
        url_filter_kind = serializers.CharField(required=False)
        node_label = serializers.CharField(required=False)

        class Meta:
            model = VEGServiceForApi
            fields = ('humanReadableName',
                      'id',
                      'wan_container_gateway_ip',
                      'wan_container_gateway_mac',
                      'dns_servers',
                      'url_filter_kind',
                      'node_label')

        def getHumanReadableName(self, obj):
            return obj.__unicode__()

# @ensure_csrf_cookie
class VEGServiceViewSet(XOSViewSet):
    base_name = "VEGservice"
    method_name = None # use the api endpoint /api/service/veg/
    method_kind = "viewset"
    queryset = VEGService.get_service_objects().select_related().all()
    serializer_class = VEGServiceSerializer

    @classmethod
    def get_urlpatterns(self, api_path="^"):
        patterns = super(VEGServiceViewSet, self).get_urlpatterns(api_path=api_path)

        return patterns

    def list(self, request):
        object_list = self.filter_queryset(self.get_queryset())

        serializer = self.get_serializer(object_list, many=True)

        return Response(serializer.data)

