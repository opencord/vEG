
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


tosca_definitions_version: tosca_simple_yaml_1_0

# compile this with "m4 veg.m4 > veg.yaml"

# include macros
include(macros.m4)

node_types:
    
    tosca.nodes.VEGService:
        description: >
            CORD: The vEG Service.
        derived_from: tosca.nodes.Root
        capabilities:
            xos_base_service_caps
        properties:
            xos_base_props
            xos_base_service_props
            backend_network_label:
                type: string
                required: false
                description: Label that matches network used to connect HPC and BBS services.
            dns_servers:
                type: string
                required: false
            node_label:
                type: string
                required: false
            docker_image_name:
                type: string
                required: false
                description: Name of docker image to pull for vEG
            docker_insecure_registry:
                type: boolean
                required: false
                description: If true, then the hostname:port specified in docker_image_name will be treated as an insecure registry