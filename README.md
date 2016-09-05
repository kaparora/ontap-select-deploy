# ontap-select-deploy
This program talks to the NetApp ONTAP Select Install VM using REST API and deploys a new ONTAP Cluster


## Step1:
* Create your config file by copying the sample:
 * >mv ontap_select_sample.cfg ontap_select.cfg
* Edit the config file ontap_select.cfg to setup your deployment config

## Step 2:
Execute build_cluster.py

## Notes:
* You can test the script with a dry run by setting no_execute flag to true in the config file
* log level is debug by default and can be configured in the config with log_level param
* Script can do three operations, which can be configured in the config file
  * create : create new cluster
  * destroy: destroy the cluster
  * destroy:create : destroy the cluster before creating it

## Create workflow
1. Add Hosts
2. Configure Hosts
3. Add Clsuter

## Destroy Workflow
1. Stop all nodes
2. Offline cluster
3. Delete Cluster
