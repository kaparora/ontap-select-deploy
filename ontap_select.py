#!/usr/bin/env python
"""
This script is the container for OntapSelect class
This class implements all the methods required to deploy an Ontap Select instance
Author: Kapil Arora
Github: @kapilarora
"""
from client import WebServicesClient
class OntapSelect(object):

    def __init__(self, config):
        '''

        :param config: dict
        '''
        self._host_ip = config['ontap_select_mgmt_vm_ip_host']
        self._api_version = config['ontap_select_mgmt_api_version']
        self._username = config['ontap_select_mgmt_user']
        self._password = config['ontap_select_mgmt_password']
        self._url = 'https://'+self._host_ip+'/api/'+self._api_version+'/'
        no_execute_str = config['no_execute']
        if no_execute_str.lower() == 'true':
            self._no_execute = True
        else:
            self._no_execute = False

        self._client = self.create_web_service_client()

    def create_web_service_client(self):
        return WebServicesClient(self._url, self._username, self._password, self._no_execute)

    def get_hosts(self):
        return self._client.execute_get('hosts')

    def get_host(self, host_id):
        service_path = 'hosts/' + host_id
        return self._client.execute_get(service_path)


    def delete_host(self, host_id, force):
        '''
        Send delete host request
        :param host_id: str
        :return:
        '''
        service_path = 'hosts/' + host_id
        data = get_force_data(force)
        self._client.execute_delete(service_path, data)

    # def get_host(self, host_id):
    #     service_path = 'hosts/' + host_id
    #     return self._client.execute_get(service_path)

    def add_host(self, host_id, host_config):
        '''
        Send add host request
        :param host_id: str
        :param host_config: dict
        :return:
        '''
        service_path = 'hosts/'+ host_id
        data = {'username' : host_config['username'], 'password' : host_config['password'],
                'vcenter': host_config['vcenter']}
        self._client.execute_put(service_path, data)

    def get_host_config(self, host_id):
        service_path = 'hosts/' + host_id + '/configuration'
        return self._client.execute_get(service_path)

    def add_host_config(self, host_id, host_config, storage_pool_configs):
        '''
        Send add host config  request
        :param host_id: str
        :param host_config: dict
        :return: None
        '''
        service_path = 'hosts/' + host_id + '/configuration'

        data = {'data_network':{},'internal_network':{}, 'mgmt_network':{}}

        data['data_network']['name'] = host_config['data_net_name']
        try:
            data_net_vlan_id = host_config['data_net_vlan_id']
        except:
            data_net_vlan_id = None
        if data_net_vlan_id:
            data['data_network']['vlan_id'] = data_net_vlan_id


        try:
            internal_net_name = host_config['internal_net_name']
        except:
            internal_net_name = None

        if internal_net_name:
            data['internal_network']['name'] = internal_net_name
            try:
                internal_net_vlan_id = host_config['internal_net_vlan_id']
            except:
                internal_net_vlan_id = None

            if internal_net_vlan_id:
                data['internal_network']['vlan_id'] = internal_net_vlan_id
        else:
            #remove internal network if not set
            data.pop('internal_network')


        data['mgmt_network']['name'] = host_config['mgmt_net_name']

        try:
            mgmt_net_vlan_id = host_config['mgmt_net_vlan_id']
        except:
            mgmt_net_vlan_id = None


        if mgmt_net_vlan_id:
            data['mgmt_network']['vlan_id'] = mgmt_net_vlan_id

        data['location'] = host_config['location']

        storage_pool = []

        storage_pools = host_config['storage_pool'].split(',')
        for pool in storage_pools:
            pool_config_dict = storage_pool_configs[pool]
            name = pool_config_dict['name']
            try:
                capacity = pool_config_dict['capacity']
            except:
                capacity = None

            if capacity:
                pool_config = {'name': name, 'capacity': capacity}
            else:
                pool_config = {'name': name}

            storage_pool.append(pool_config)

        data['storage_pool'] = storage_pool

        try:
            serial_number = host_config['serial_number']
        except:
            serial_number = None
        if serial_number:
            data['serial_number'] = serial_number

        try:
            instance_type = host_config['instance_type']
        except:
            instance_type = None

        if instance_type:
            data['instance_type'] = instance_type

        try:
            eval_str = host_config['eval']
        except:
            eval_str = None

        if eval_str:
            eval_bool = (eval_str.lower() == 'true')
            data['eval'] = eval_bool

        self._client.execute_put(service_path, data)

    def get_clusters(self):
        return self._client.execute_get('clusters')

    def get_cluster(self, cluster_name):
        '''
        Gets the cluster info
        :type cluster_name: str
        :param cluster_name: str
        :return: cluster details
        '''
        service_path = 'clusters/' + cluster_name
        return self._client.execute_get(service_path)


    def add_cluster(self, cluster_config, node_configs):
        '''
        Send add cluster request. With the expected data structure.
        :param cluster_config: dict
        :param node_configs: dict
        :return: None
        '''
        service_path = 'clusters'
        nodes = []
        for node_name, node_config in node_configs.iteritems():
            host = node_config['host']
            node_mgmt_ip = node_config['node_mgmt_ip']
            try:
                mirror = node_config['mirror']
            except:
                mirror = None

            if mirror:
                node = {'host': host, 'name': node_name, 'mirror': mirror, 'node_mgmt_ip':node_mgmt_ip }
            else:
                node = {'host': host, 'name': node_name, 'node_mgmt_ip':node_mgmt_ip}

            nodes.append(node)
        #fix boolean values
        eval_str = cluster_config['eval']
        eval_bool = (eval_str.lower() == 'true')
        inhibit_rollback_str  = cluster_config['inhibit_rollback']
        inhibit_rollback_bool = (inhibit_rollback_str.lower() == 'true')

        data = {'admin_password':cluster_config['admin_password'],
                'cluster_mgmt_ip':cluster_config['cluster_mgmt_ip'],
                'dns_info':
                    {'dns_ips': cluster_config['dns_ips'].split(','),
                     'domains': cluster_config['domains'].split(',')
                     },
                'eval': eval_bool,
                'inhibit_rollback': inhibit_rollback_bool,
                'gateway': cluster_config['gateway'],
                'netmask': cluster_config['netmask'],
                'name': cluster_config['name'],
                'nodes': nodes,
                'ntp_servers': cluster_config['ntp_servers'].split(',')
                }
        self._client.execute_post(service_path, data)

    def delete_cluster(self, cluster_name, force):
        '''
        Send Delete cluster request
        :param cluster_name: str
        :return: None
        '''
        data = get_force_data(force)
        service_path = 'clusters/' + cluster_name
        self._client.execute_delete(service_path, data)

    # def get_cluster(self, cluster_name):
    #     '''
    #     get cluster information
    #     :param cluster_name: str
    #     :return:
    #     '''
    #     service_path = 'clusters/' + cluster_name
    #     return self._client.execute_get(service_path)

    def get_cluster_nodes(self, cluster_name):
        '''
        Gets the list of nodes including status and host
        :param cluster_name: str
        :return: list of nodes(dict)
        '''
        service_path = 'clusters/' + cluster_name + '/nodes'
        return self._client.execute_get(service_path)

    def stop_node(self, cluster_name, node_name, force):
        '''
        send request to stop the cluster node
        :param cluster_name: str
        :param node_name: str
        :return:
        '''
        service_path = 'clusters/' + cluster_name + "/nodes/" + node_name + "/stop"
        data = get_force_data(force)
        return self._client.execute_post(service_path, data)

    def offline_cluster(self, cluster_name, force):
        '''
        check if cluster is online
        :param cluster_name: str
        :param force: bool
        :return:
        '''
        service_path = 'clusters/' + cluster_name + "/offline"
        data = get_force_data(force)

        return self._client.execute_post(service_path, data)

def get_force_data(force):
    data = {'force': False}
    if force:
        data = {'force': True}
    return data

