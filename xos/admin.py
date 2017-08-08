
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


from django.contrib import admin

from services.veg.models import *
from django import forms
from django.utils.safestring import mark_safe
from django.contrib.auth.admin import UserAdmin
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.signals import user_logged_in
from django.utils import timezone
from django.contrib.contenttypes import generic
from suit.widgets import LinkedSelect
from core.admin import ServiceAppAdmin,SliceInline,ServiceAttrAsTabInline, ReadOnlyAwareAdmin, XOSTabularInline, ServicePrivilegeInline, TenantRootTenantInline, TenantRootPrivilegeInline
from core.middleware import get_request

from functools import update_wrapper
from django.contrib.admin.views.main import ChangeList
from django.core.urlresolvers import reverse
from django.contrib.admin.utils import quote

class VEGServiceAdmin(ReadOnlyAwareAdmin):
    model = VEGService
    verbose_name = "vEG Service"
    verbose_name_plural = "vEG Service"
    list_display = ("backend_status_icon", "name", "enabled")
    list_display_links = ('backend_status_icon', 'name', )
    fieldsets = [(None,             {'fields': ['backend_status_text', 'name','enabled','versionNumber', 'description', "view_url", "icon_url", "service_specific_attribute", "node_label"],
                                     'classes':['suit-tab suit-tab-general']}),
                 ("backend config", {'fields': ["url_filter_kind"],
                                     'classes':['suit-tab suit-tab-backend']}),
                 ("vEG config", {'fields': ["dns_servers", "docker_image_name", "docker_insecure_registry"],
                                     'classes':['suit-tab suit-tab-veg']}) ]
    readonly_fields = ('backend_status_text', "service_specific_attribute")
    inlines = [SliceInline,ServiceAttrAsTabInline,ServicePrivilegeInline]

    extracontext_registered_admins = True

    user_readonly_fields = ["name", "enabled", "versionNumber", "description"]

    suit_form_tabs =(('general', 'Service Details'),
        ('backend', 'Backend Config'),
        ('veg', 'vEG Config'),
        ('administration', 'Administration'),
        #('tools', 'Tools'),
        ('slices','Slices'),
        ('serviceattrs','Additional Attributes'),
        ('serviceprivileges','Privileges') ,
    )

    suit_form_includes = (('vegadmin.html', 'top', 'administration'),
                           ) #('hpctools.html', 'top', 'tools') )

    def get_queryset(self, request):
        return VEGService.get_service_objects_by_user(request.user)

class VEGTenantForm(forms.ModelForm):
    last_ansible_hash = forms.CharField(required=False)
    wan_container_ip = forms.CharField(required=False)
    wan_container_mac = forms.CharField(required=False)

    def __init__(self,*args,**kwargs):
        super (VEGTenantForm,self ).__init__(*args,**kwargs)
        self.fields['kind'].widget.attrs['readonly'] = True
        self.fields['provider_service'].queryset = VEGService.objects.all()
        if self.instance:
            # fields for the attributes
            self.fields['last_ansible_hash'].initial = self.instance.last_ansible_hash
            self.fields['wan_container_ip'].initial = self.instance.wan_container_ip
            self.fields['wan_container_mac'].initial = self.instance.wan_container_mac
        if (not self.instance) or (not self.instance.pk):
            # default fields for an 'add' form
            self.fields['kind'].initial = VEG_KIND
            self.fields['creator'].initial = get_request().user
            if VEGService.objects.exists():
               self.fields["provider_service"].initial = VEGService.objects.all()[0]

    def save(self, commit=True):
        self.instance.creator = self.cleaned_data.get("creator")
        self.instance.instance = self.cleaned_data.get("instance")
        self.instance.last_ansible_hash = self.cleaned_data.get("last_ansible_hash")
        return super(VEGTenantForm, self).save(commit=commit)

    class Meta:
        model = VEGTenant
        fields = '__all__'

class VEGTenantAdmin(ReadOnlyAwareAdmin):
    list_display = ('backend_status_icon', 'id', 'subscriber_tenant' )
    list_display_links = ('backend_status_icon', 'id')
    fieldsets = [ (None, {'fields': ['backend_status_text', 'kind', 'provider_service', 'subscriber_tenant', 'service_specific_id',
                                     'wan_container_ip', 'wan_container_mac', 'creator', 'instance', 'last_ansible_hash'],
                          'classes':['suit-tab suit-tab-general']})]
    readonly_fields = ('backend_status_text', 'service_specific_attribute', 'wan_container_ip', 'wan_container_mac')
    form = VEGTenantForm

    suit_form_tabs = (('general','Details'),)

    def get_queryset(self, request):
        return VEGTenant.get_tenant_objects_by_user(request.user)


admin.site.register(VEGService, VEGServiceAdmin)
admin.site.register(VEGTenant, VEGTenantAdmin)

