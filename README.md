# ontap-select-deploy
This program talks to the NetApp ONTAP Select Install VM using REST API and deploys a new ONTAP Cluster


## Step1:
* Create your config file by copying the sample:
 * For 1 node Cluster
   * >mv ontap_select_sample.cfg ontap_select.cfg
 * For 4 node cluster
   * >mv ontap_select_sample_4node.cfg ontap_select.cfg 
 
* Edit the config file ontap_select.cfg to setup your deployment config

## Step 2:
Execute cluster.py

This script take 1 argument and i.e. operation. There are 4 possible operation values, as follows: 
* Create cluster
 * >python cluster.py create
* Destroy cluster
 * >python cluster.py destroy
* Destroy cluster before Create
 * >python cluster.py destroy:create
* Display Help
 * >python cluster.py help


## Notes:
* You can test the script with a dry run by setting no_execute flag to true in the config file
* log level is debug by default and can be configured in the config with log_level param

## Create workflow
1. Add Hosts
2. Configure Hosts
3. Add Clsuter

## Destroy Workflow
1. Stop all nodes
2. Offline cluster
3. Delete Cluster
