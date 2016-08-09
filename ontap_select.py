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

    def delete_host(self, host_id):
        '''
        Send delete host request
        :param host_id: str
        :return:
        '''
        service_path = 'hosts/' + host_id
        self._client.execute_delete(service_path)

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

    def add_host_config(self, host_id, host_config):
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

        data['internal_network']['name'] = host_config['internal_net_name']
        try:
            internal_net_vlan_id = host_config['internal_net_vlan_id']
        except:
            internal_net_vlan_id = None

        if internal_net_vlan_id:
            data['internal_network']['vlan_id'] = internal_net_vlan_id

        data['mgmt_network']['name'] = host_config['mgmt_net_name']

        try:
            mgmt_net_vlan_id = host_config['mgmt_net_vlan_id']
        except:
            mgmt_net_vlan_id = None


        if mgmt_net_vlan_id:
            data['mgmt_network']['vlan_id'] = mgmt_net_vlan_id

        data['location'] = host_config['location']
        data['storage_pool'] = host_config['storage_pool']
        try:
            serial_number =  host_config['serial_number']
        except:
            serial_number = None
        if serial_number:
            data['serial_number'] = serial_number

        try:
            storage_pdisks = host_config['storage_pdisks']
        except:
            storage_pdisks = None

        if storage_pdisks:
            data['storage_pdisks'] = storage_pdisks.split(',')

        self._client.execute_put(service_path, data)

    def get_clusters(self):
        return self._client.execute_get('clusters')

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
            try:
                mirror = node_config['mirror']
            except:
                mirror = None

            if mirror:
                node = {'host': host, 'name': node_name, 'mirror': mirror}
            else:
                node = {'host': host, 'name': node_name}

            nodes.append(node)
        #fix boolean values
        eval_str = cluster_config['eval']
        eval_bool = (eval_str.lower() == 'true')
        inhibit_rollback_str  = cluster_config['inhibit_rollback']
        inhibit_rollback_bool = (inhibit_rollback_str.lower() == 'true')

        data = {'admin_password':cluster_config['admin_password'],
                'dns_info':
                    {'dns_ips': cluster_config['dns_ips'].split(','),
                     'domains': cluster_config['domains'].split(',')
                     },
                'eval': eval_bool,
                'inhibit_rollback': inhibit_rollback_bool,
                'mgmt_ip_info':
                    {'gateway': cluster_config['gateway'],
                     'ip_addresses': cluster_config['ip_addresses'].split(','),
                     'netmask': cluster_config['netmask']
                     },
                'name': cluster_config['name'],
                'nodes': nodes,
                'ntp_servers': cluster_config['ntp_servers'].split(',')
                }
        self._client.execute_post(service_path, data)

    def delete_cluster(self, cluster_name):
        '''
        Send Delete cluster request
        :param cluster_name: str
        :return: None
        '''
        service_path = 'clusters/' + cluster_name
        self._client.execute_delete(service_path)

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

    def stop_node(self, cluster_name, node_name):
        '''
        send request to stop the cluster node
        :param cluster_name: str
        :param node_name: str
        :return:
        '''
        service_path = 'clusters/' + cluster_name + "/nodes/" + node_name + "/stop"
        return self._client.execute_post(service_path, '')

    def offline_cluster(self, cluster_name, force):
        '''
        check if cluster is online
        :param cluster_name: str
        :param force: bool
        :return:
        '''
        service_path = 'clusters/' + cluster_name + "/offline"
        data = {'force': False}
        if force:
            data = {'force': True}

        return self._client.execute_post(service_path, data)
