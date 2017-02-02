from services.veg.models import VEGService
from service import XOSService

class XOSVegService(XOSService):
    provides = "tosca.nodes.VEGService"
    xos_model = VEGService
    copyin_props = ["view_url", "icon_url", "enabled", "published", "public_key",
                    "private_key_fn", "versionNumber", "backend_network_label",
                    "dns_servers", "node_label", "docker_image_name", "docker_insecure_registry"]

