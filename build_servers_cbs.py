#!/usr/bin/python

import os
import sys
import pyrax
import time
import string

'''
Build Servers with attached CBS and CloudNetworks
'''

pyrax.set_setting("identity_type", "rackspace")
cred_file = os.path.expanduser('~/.ipython/profile_cbdteam/conf/.rackspace_cloud_credentials')
pyrax.set_credential_file(cred_file)

my_region = 'IAD'

cs = pyrax.connect_to_cloudservers(region=my_region)
cbs = pyrax.connect_to_cloud_blockstorage(region=my_region)
cnw = pyrax.connect_to_cloud_networks(region=my_region)

#| onmetal-compute1 | OnMetal Compute v1      | 32768     | 32   | 0         |         | 20    | 10000.0     | N/A       |
#| onmetal-io1      | OnMetal I/O v1          | 131072    | 32   | 3200      |         | 40    | 10000.0     | N/A       |
#| onmetal-memory1  | OnMetal Memory v1       | 524288    | 32   | 0         |         | 24    | 10000.0     | N/A       |
#| performance1-1   | 1 GB Performance        | 1024      | 20   | 0         |         | 1     | 200.0       | N/A       |
#| performance1-2   | 2 GB Performance        | 2048      | 40   | 20        |         | 2     | 400.0       | N/A       |
#| performance1-4   | 4 GB Performance        | 4096      | 40   | 40        |         | 4     | 800.0       | N/A       |
#| performance1-8   | 8 GB Performance        | 8192      | 40   | 80        |         | 8     | 1600.0      | N/A       |
#| performance2-120 | 120 GB Performance      | 122880    | 40   | 1200      |         | 32    | 10000.0     | N/A       |
#| performance2-15  | 15 GB Performance       | 15360     | 40   | 150       |         | 4     | 1250.0      | N/A       |
#| performance2-30  | 30 GB Performance       | 30720     | 40   | 300       |         | 8     | 2500.0      | N/A       |
#| performance2-60  | 60 GB Performance       | 61440     | 40   | 600       |         | 16    | 5000.0      | N/A       |
#| performance2-90  | 90 GB Performance
#OnMental i- Cent 6.5: a4a07273-6e5c-4092-a4bd-b3a2fc669a5f
#Cent 6.5 (PVHVM): a84b1592-6817-42da-a57c-3c13f3cfc1da
#CentOS 7 (PVHVM): 4da79ffd-46f0-4f7c-9ade-490f04cc8994
#OnMetal - CentOS 7: 11cffab8-9a65-4e9a-a242-a2bd25a4486d


#Needs to be fqdn and based on a domain associated with this account
clust_prefix='dgbm07-'
dn_name=clust_prefix  + 'datanode'
mn_name=clust_prefix  + 'masternode'
pvt_nets = []
cbs_ids = []
cbs_ids_dict = {}
mn_ids = []
dn_ids = []
nn_image = 'a84b1592-6817-42da-a57c-3c13f3cfc1da'
dn_image = 'a4a07273-6e5c-4092-a4bd-b3a2fc669a5f'
mn_flavor = 'performance2-15'
dn_flavor = 'onmetal-io1'
new_network_name = clust_prefix + 'hadoop_net'
new_network_cidr = "192.168.5.0/24"
datanodes = 3
datanode = 1
masternodes=2
masternode=1
vols_per_datanode=0
cbs_vol_type="SATA"
pubkey='dgmuse'

new_net = cnw.create(new_network_name, cidr=new_network_cidr)
print "New network:", new_net
networks = new_net.get_server_networks(public=True, private=True)

vol_end_range = vols_per_datanode + 1
while (datanode <= datanodes):
	for i in range(1, vol_end_range):
	    my_dn_name  = dn_name + str(datanode)
	    cbsname = my_dn_name + 'vol' + str(i)
	    vol = cbs.create(name=cbsname, size=500, volume_type=cbs_vol_type)
	    pyrax.utils.wait_until(vol,"status","available", interval=1)
            my_dn_name = my_dn_name + str(i)
	    cbs_ids_dict[my_dn_name] = vol.id
            print "name: %s dict: %s vol_id: %s" % (my_dn_name, cbs_ids_dict[my_dn_name], vol.id) 
	    print "vol %s: %s" % (cbsname, vol)
        datanode = datanode + 1

datanode=1
#myimage = [img for img in cs.images.list()
#                if imgname in img.name][0]
#myflavor = [flavor for flavor in cs.flavors.list()
#                if flavor.ram == size][0]

while (datanode <= datanodes):
	for i in range(1, 4):
	    server_name=dn_name + str(i)
	    server = cs.servers.create(server_name, myimage.id, dn_flavor, key_name=pubkey, nics=networks)
	    print "Name:", server.name
	    print "ID:", server.id
	    dn_ids.append(server.id)
	    adminpass = server.adminPass
	    print "Admin Password:", adminpass
	    print "Waiting for Network config.."
	    while not cs.servers.get(server.id).networks:
	      time.sleep(1)
	    pvt_net = str(cs.servers.get(server.id).networks['private'][0])
	    new_net = str(cs.servers.get(server.id).networks[new_network_name][0])
	    pub_net = [ ip for ip in cs.servers.get(server).networks['public']
			if len( ip.split(".") ) == 4 ]

	    pvt_nets.append(pvt_net)
	    print "Public Networks: %s" % str(pub_net[0])
	    print "Private Networks: %s" % pvt_net
	    print "Isolated Networks: %s" % new_net
	    datanode = datanode + 1

while (masternode <= masternodes):
	    server_name=mn_name + str(masternode)
	    server = cs.servers.create(server_name, myimage.id, mn_flavor, key_name=pubkey, nics=networks)
	    print "Name:", server.name
	    print "ID:", server.id
	    mn_ids.append(server.id)
	    adminpass = server.adminPass
	    print "Admin Password:", adminpass
	    print "Waiting for Network config.."
	    while not cs.servers.get(server.id).networks:
	      time.sleep(1)
	    pvt_net = str(cs.servers.get(server.id).networks['private'][0])
	    new_net = str(cs.servers.get(server.id).networks[new_network_name][0])
	    pub_net = [ ip for ip in cs.servers.get(server).networks['public']
			if len( ip.split(".") ) == 4 ]

	    pvt_nets.append(pvt_net)
	    print "Public Networks: %s" % str(pub_net[0])
	    print "Private Networks: %s" % pvt_net
	    print "Isolated Networks: %s" % new_net
            masternode = masternode + 1


#Broken Logic Needs to associate correct 3 cbs vols with datanodes
for i in dn_ids:
    cbs_vol_arr = list(string.ascii_lowercase)
    frst_place = 5 
    mysrv = cs.servers.get(i)
    pyrax.utils.wait_until(mysrv, "status", "ACTIVE", attempts=0,
                verbose=True)
    vol_end_range = vols_per_datanode + 1
    for n in range(1, vol_end_range):
      myvol= mysrv.name + str(n)
      vol = cbs.get(cbs_ids_dict[myvol]) 
      print "attaching vol: %s to srv: %s" % ( vol, mysrv )
      vol.attach_to_instance(mysrv, '/dev/hvd' +  str(cbs_vol_arr[frst_place + n]))

#    for id in cbs_ids:
#      vol = cbs.get(id)
#      print "attaching vol: %s to srv: %s" % ( vol, mysrv )
#      vol.attach_to_instance(mysrv, '/dev/zvd' + cbs_vol_arr.pop())
#      pyrax.utils.wait_until(vol, "status", "in-use", interval=3, attempts=0,
#        verbose=True)
#      print "Volume attachments:", vol.attachments
#      cbs_ids.pop()
#      break
