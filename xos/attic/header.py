from django.db import models
from core.models import Service, PlCoreBase, Slice, Instance, Tenant, TenantWithContainer, Node, Image, User, Flavor, NetworkParameter, NetworkParameterType, Port, AddressPool, User
from core.models.plcorebase import StrippedCharField
import os
from django.db import models, transaction
from django.db.models import *

from django.forms.models import model_to_dict
from django.db.models import Q
from operator import itemgetter, attrgetter, methodcaller
from core.models import Tag
from core.models.service import LeastLoadedNodeScheduler
from services.vrouter.models import VRouterService, VRouterTenant
import traceback
from xos.exceptions import *
from xos.config import Config

class ConfigurationError(Exception):
    pass

VEG_KIND = "vEG"
CORD_SUBSCRIBER_KIND = "CordSubscriberRoot"
