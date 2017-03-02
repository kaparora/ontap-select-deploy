#!/usr/bin/env python
"""
This is the main python script for our Ontap Select Deployment.
This script will read the ontap_select.cfg and perform create cluster and destroy cluster
operations.
Create clsuter workflow:
1) Add hosts
2) Configure Hosts
3) Add Cluster
Destroy cluster workflow:
1) Stop all nodes
2) offline Cluster
3) Delete cluster
4) Delete Hosts

Author: Kapil Arora
Github: @kapilarora
"""
import ConfigParser
from ontap_select import OntapSelect
import io
import time
import sys
import logging
from time import strftime


def main():
    config = ConfigParser.ConfigParser()
    # reading config file ontap_select.cfg
    config.read(io.BytesIO('ontap_select.cfg'))

    default_config = dict(config.items('default'))

    # getting log level from the config file
    log_level = default_config['log_level']
    level = _get_Log_level(log_level)
    # initializing logger
    log_filename = strftime("ontap_select_%Y%m%d%H%M%S.log")
    logging.basicConfig(filename=log_filename,
                        level=level, format='%(asctime)s - %(levelname)s - %(message)s')
    operation = None
    try:
        operation = sys.argv[1]
    except IndexError:
        print 'This script needs an operation as argument.'

    if operation == 'create' or operation == 'destroy' or operation == 'destroy:create':
        logging.info('Requested operation is : %s', operation)
    else:
        if operation == None:
            print 'No operation provided!'
        elif operation != 'help':
            print 'Invalid operation: ' + operation
        print_help()
        exit

    cluster_config = dict(config.items('cluster'))
    host_ids_str = default_config['hosts']
    host_ids = host_ids_str.split(',')
    host_configs = {}
    for host_id in host_ids:
        host_configs[host_id] = dict(config.items(host_id))

    storage_pool_configs = {}
    for host_id, host_config in host_configs.iteritems():
        storage_pools = host_config['storage_pool'].split(',')
        for storage_pool in storage_pools:
            storage_pool_configs[storage_pool] = dict(config.items(storage_pool))

    node_name_str = cluster_config['nodes']
    node_names = node_name_str.split(',')
    node_configs = {}
    for node_name in node_names:
        node_configs[node_name] = dict(config.items(node_name))

    force = False
    force_str = default_config['force']
    if force_str.lower() == 'true':
        force = True

    # @TODO change no-execute to env variable
    # no-execute? checking if no_execute is set. We won't execute any apis..just list the operations
    no_execute_str = default_config['no_execute']
    if no_execute_str.lower() == 'true':
        no_execute = True
    else:
        no_execute = False

    sleep_time = int(default_config['sleep_time_in_seconds_for_status_checks'])
    logging.debug('Configured sleep time for status checks is %s', sleep_time)

    logging.info('no_execute is set to %s', no_execute_str)
    if no_execute:
        logging.info('This is a dry run, No APIs will be executed.')

    logging.info('ONTAP Management VM IP:user/pass %s:%s/**** and with API version %s will be used',
                 default_config['ontap_select_mgmt_vm_ip_host'], default_config['ontap_select_mgmt_user'],
                 default_config['ontap_select_mgmt_api_version'])
    logging.debug('Initializing ONTAP select class')
    # Instantiating OntapSelect class
    ontap_select = OntapSelect(default_config)

    #operation = default_config['operation']

    cluster_name = cluster_config['name']
    logging.info('Cluster name is %s', cluster_name)

    if operation == 'create':
        create_cluster(cluster_config, host_configs, storage_pool_configs, node_configs, ontap_select, sleep_time)
    elif operation == 'destroy:create':
        destroy_cluster(ontap_select, cluster_name, host_ids, sleep_time, no_execute, force)
        create_cluster(cluster_config, host_configs, storage_pool_configs, node_configs, ontap_select, sleep_time)
    elif operation == 'destroy':
        destroy_cluster(ontap_select, cluster_name, host_ids, sleep_time, no_execute, force)
    else:
        logging.error('Unknown Operation %s , valid values : create, destroy and destroy:create', operation)


def print_help():
    print '###### HELP ######'
    print 'Valid Operations:'
    print '1. create - Creates a new cluster'
    print '2. destroy - Destroy the cluster'
    print '3. destroy:create - Destroy the cluster before creation'
    print '###### Sample Commands ######'
    print 'python cluster.py create'
    print 'python cluster.py destroy'
    print 'python cluster.py create:destroy'


def create_cluster(cluster_config, host_configs, storage_pool_configs, node_configs, ontap_select, sleep_time):
    '''

    :param cluster_config: dict of cluster config params
    :param host_configs: dict of host config params
    :param node_configs: dict of node config params
    :param ontap_select: OntapSelect class object
    :param sleep_time: int time in seconds for recursive wait functions
    :return: None
    '''
    logging.info('Starting ONTAP Select Cluster Deployment')
    add_hosts(host_configs, ontap_select, sleep_time)
    configure_hosts(host_configs, storage_pool_configs, ontap_select, sleep_time)
    add_cluster(cluster_config, node_configs, ontap_select, sleep_time)


def destroy_cluster(ontap_select, cluster_name, host_ids, sleep_time, no_execute, force):
    '''

    :param ontap_select: OntapSelect class obj
    :param cluster_name: name of the cluster
    :param host_ids: list of host ids
    :param sleep_time: int time in seconds for recursive wait functions
    :return: None
    '''
    logging.info('Checking if cluster  %s exists', cluster_name)
    if cluster_exists(ontap_select, cluster_name):
        #stop_all_nodes(ontap_select, cluster_name, sleep_time, force)
        cluster_offline(ontap_select, cluster_name, sleep_time, force)
        cluster_delete(ontap_select, cluster_name, sleep_time, no_execute, force)
    for host_id in host_ids:
        if host_exists(ontap_select, host_id):
            delete_host(ontap_select, host_id, sleep_time, True, no_execute)
    logging.info('Cluster %s destroy workflow completed!', cluster_name)
    print "Cluster destroy workflow completed.!"


def add_hosts(host_configs, ontap_select, sleep_time):
    '''
    :param host_configs: dict of host config params
    :param ontap_select: OntapSelect class object
    :param sleep_time: int time in seconds for recursive wait functions
    :return: None
    '''
    logging.info('Reading hosts config')

    for host_id, host_config in host_configs.iteritems():
        logging.info('Adding host %s with username/password: %s/***** and vcenter: %s',
                     host_id, host_config['username'], host_config['vcenter'])
        # Sending host add request
        ontap_select.add_host(host_id, host_config)
        logging.info('Waiting for host %s to be added and authenticated.',host_id)
        #Wait for host to be added
        host_authenticated = False
        while not host_authenticated:
            logging.info('Sleeping for %s seconds before next status check.', sleep_time)
            time.sleep(sleep_time)
            host_authenticated = True
            logging.info('Getting Status for  host %s.',host_id)
            output_host = ontap_select.get_host(host_id)
            status = output_host['status']
            logging.info('Status of Host %s is %s', host_id, status)
            if status == "authentication_in_progress":
                host_authenticated = False
            elif status == "authentication_failed":
                logging.error('Authentication failed for Host %s', host_id)
                logging.error('Stopping Execution, check host credentials')
                sys.exit('Authentication failed for  host ' + host_id)
            logging.debug('Get host result %s', output_host)
        logging.info('Host %s has been added and authenticated',host_id)


def configure_hosts(host_configs, storage_pool_configs, ontap_select, sleep_time):
    '''
    :param host_configs: dict of host config params
    :param ontap_select: OntapSelect class object
    :param sleep_time: int time in seconds for recursive wait functions
    :return: None
    '''
    for host_id, host_config in host_configs.iteritems():
        # Read host config
        logging.info('Reading configuration params for host %s', host_id)
        # Send configure Host request
        logging.debug('Host Configuration: %s', host_config)
        logging.info('Sending add configuration request for host %s', host_id)

        ontap_select.add_host_config(host_id, host_config, storage_pool_configs)
        # wait for hosts to be configured
        logging.info('Wait for configuration of host %s to complete',host_id)
        host_configured = False
        while not host_configured:
            logging.info('Sleeping for %s seconds before next status check.', sleep_time)
            time.sleep(sleep_time)
            host_configured = True
            logging.info('Sending request to get status of host %s', host_id)
            output_host = ontap_select.get_host(host_id)
            logging.debug('Status result for host: %s', host_id)
            status = output_host['status']
            logging.info('Status of Host %s is %s', host_id, status)
            if status == 'configuration_in_progress':
                host_configured = False
            elif status == 'configuration_failed':
                logging.error('Configuration failed for Host %s', host_id)
                logging.error('Stopping Execution, check host configuration options.')
                sys.exit('Configuration failed for  host ' + host_id)


def add_cluster(cluster_config, node_configs, ontap_select, sleep_time):
    '''
    :param cluster_config: dict of cluster config params
    :param node_configs: dict of node config params
    :param ontap_select: OntapSelect class object
    :param sleep_time: int time in seconds for recursive wait functions
    :return: None
    '''
    logging.info('Reading Cluster config parameters')
    logging.debug('Cluster config : %s', cluster_config)
    logging.debug('Nodes configs : %s', node_configs)
    logging.info('Sending add cluster request for cluster name: %s', cluster_config['name'])
    ontap_select.add_cluster(cluster_config, node_configs)

    # wait for cluster to be online
    logging.info('Waiting for Cluster creation and setup to complete')
    cluster_online = False
    while not cluster_online:
        logging.info('Sleeping for %s seconds before next status check.', sleep_time)
        time.sleep(sleep_time)
        cluster_online = True
        logging.info('Requesting status of all clusters')
        output_clusters = ontap_select.get_clusters()
        clusters = output_clusters['clusters']
        # if cluster create fails, the cluster disappears. Hence we need to check if clusters list is empty
        if len(clusters) < 1:
            logging.error('Cluster creation failed, cluster %s does not exist.', cluster_config['name'])
        for cluster in clusters:
            cluster_name = cluster['name']
            logging.debug('Cluster name: %s', cluster_name)
            if cluster_name == cluster_config['name']:
                state = cluster['state']
                logging.info('State of cluster %s is %s', cluster_name, state)
                if state == 'creating':
                    cluster_online = False
                elif state == 'deploying_nodes':
                    cluster_online = False
                elif state == 'post_deploy_setup':
                    cluster_online = False
                elif state == 'online_setup_failed':
                    logging.error('Online setup failed for Cluster %s', cluster_name)
                    logging.error('Stopping Execution, check cluster configuration options.')
                    sys.exit('Online setup failed for cluster  ' + cluster_name)
                elif state == 'online_failed':
                    logging.error('Online operation failed for Cluster %s', cluster_name)
                    logging.error('Stopping Execution, check cluster configuration options.')
                    sys.exit('Online  failed for cluster  ' + cluster_name)
                elif state == 'create_failed':
                    logging.error('Creation failed for Cluster %s', cluster_name)
                    logging.error('Stopping Execution, check cluster configuration options.')
                    sys.exit('Creation failed for  cluster ' + cluster_name)
    logging.info('Cluster %s creation workflow completed!', cluster_name)
    print "Cluster creation workflow completed.!"


def cluster_exists(ontap_select, cluster_name):
    '''
    :param ontap_select: OntapSelect class object
    :param cluster_name: str
    :return: None
    '''
    logging.info('Getting List of Clusters.')
    clusters_output = ontap_select.get_clusters()
    clusters = clusters_output['clusters']
    logging.debug('Cluster get result %s', clusters)
    for cluster in clusters:

        if cluster['name'] == cluster_name:
            logging.info('Cluster %s exists', cluster_name)
            return True
    logging.info('Cluster %s does not exist.', cluster_name)
    return False


def host_exists(ontap_select, host_id):
    '''

    :param ontap_select: OntapSelect class object
    :param host_id: str
    :return:
    '''
    logging.info('Getting List of Hosts.')
    output_hosts = ontap_select.get_hosts()
    hosts = output_hosts['hosts']
    logging.debug('Hosts get result %s', hosts)
    for host in hosts:

        if host['host'] == host_id:
            logging.info('Host %s exists', host_id)
            return True
    logging.info('Host %s does not exist.', host_id)
    return False


def delete_host(ontap_select, host_id, sleep_time, force, no_execute):
    '''

    :param ontap_select: OntapSelect class object
    :param host_id: str
    :param sleep_time: int time in seconds for recursive wait functions
    :return:
    '''
    logging.info('Deleting Hosts %s', host_id)
    hosts = ontap_select.delete_host(host_id, force)
    if no_execute:
        print "Not waiting for deletion to complete as not real execution"
    else:#waiting for deletion to complete
        while host_exists(ontap_select, host_id):
            logging.info('Sleeping for %s seconds before next status check.', sleep_time)
            time.sleep(sleep_time)



def stop_all_nodes(ontap_select, cluster_name, sleep_time, force):
    '''

    :param ontap_select: OntapSelect class object
    :param cluster_name: str
    :param sleep_time: int time in seconds for recursive wait functions
    :return: None
    '''
    logging.info('Stopping all cluster nodes for Cluster name: %s', cluster_name)
    nodes = ontap_select.get_cluster_nodes(cluster_name)
    for node in nodes:
        node_name = node['name']
        node_state = node['state']
        logging.info('State of node %s is %s', node_name, node_state)
        if (node_state == 'powered_on' or node_state == 'powering_off_failed' or
                    node_state == 'powering_on' or node_state == 'suspended'):
            logging.info('Sending request to stop node %s', node_name)
            ontap_select.stop_node(cluster_name, node_name, force)
            logging.info('Wait for all nodes to stop')
            node_stopped = False
            logging.info('Wait for node %s to stop', node_name)
            while not node_stopped:
                logging.info('Sleeping for %s seconds before next status check.', sleep_time)
                time.sleep(sleep_time)
                node_stopped = True
                logging.info('Sending request to get status of node %s', node_name)
                nodes = ontap_select.get_cluster_nodes(cluster_name)
                logging.debug('Status result for all nodes: %s', nodes)
                for node in nodes:
                    name = node['name']
                    if node_name == name:
                        node_state = node['state']
                        logging.info('State of Node %s is %s', node_name, node_state)
                        if node_state == 'powering_off':
                            node_stopped = False
                        elif node_state == 'powering_off_failed':
                            logging.error('Powering failed for Node %s', node_name)
                            logging.error('Stopping Execution, check vmware env')
                            sys.exit('Powering off failed for  node ' + node_name)



def cluster_offline(ontap_select, cluster_name, sleep_time, force):
    '''

    :param ontap_select: OntapSelect class object
    :param cluster_name: str
    :param sleep_time: int time in seconds for recursive wait functions
    :return: None
    '''
    logging.info('Making cluster %s offline', cluster_name)
    # @TODO check if cluster is already offline
    ontap_select.offline_cluster(cluster_name, force)
    # wait for cluster to be offline
    logging.info('Waiting for Cluster offline to finish')
    is_cluster_offline = False
    while not is_cluster_offline:
        logging.info('Sleeping for %s seconds before next status check.', sleep_time)
        time.sleep(sleep_time)
        is_cluster_offline = True
        logging.info('Requesting status of all clusters')
        output_clusters = ontap_select.get_clusters()
        clusters = output_clusters['clusters']
        for cluster in clusters:
            name = cluster['name']
            logging.debug('Cluster name: %s', cluster_name)
            if cluster_name == name:
                state = cluster['state']
                logging.info('State of cluster %s is %s', cluster_name, state)
                if state == 'online':
                    is_cluster_offline = False
                if state == 'offline_in_progress':
                    is_cluster_offline = False
                elif state == 'offline_failed':
                    logging.error('Offline  failed for Cluster %s', cluster_name)
                    logging.error('Stopping Execution, retry!')
                    sys.exit('Offline  failed for cluster  ' + name)
    logging.info('Cluster %s successfully offlined ', name)


def cluster_delete(ontap_select, cluster_name, sleep_time, no_execute, force):
    '''

    :param ontap_select: OntapSelect class object
    :param cluster_name: str
    :param sleep_time: int time in seconds for recursive wait functions
    :return: None
    '''
    logging.info('Deleting cluster %s ', cluster_name)
    ontap_select.delete_cluster(cluster_name, force)
    logging.info('Waiting for Cluster deletion to finish')
    if no_execute:
        print "Not waiting for deletion to complete"
    else:#wait for cluster to delete
        while cluster_exists(ontap_select, cluster_name):
            logging.info('Sleeping for %s seconds before next status check.', sleep_time)
            time.sleep(sleep_time)



def _get_Log_level(log_level):
    '''

    :param log_level: str info/error/warn/debug
    :return: logging.level
    '''
    if log_level == 'info':
        level = logging.INFO
    elif log_level == 'error':
        level = logging.ERROR
    elif log_level == 'warn':
        level = logging.WARN
    else:
        level = logging.DEBUG
    return level


if __name__ == '__main__':
    main()
