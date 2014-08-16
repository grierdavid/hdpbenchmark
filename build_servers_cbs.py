#!/usr/bin/env python

import os
import sys
import pyrax
import time

'''
Build Servers with attached CBS and CloudNetworks
'''

cred_file = os.path.expanduser('~/.rackspace_cloud_credentials')
pyrax.set_credential_file(cred_file)

cs = pyrax.cloudservers
cbs = pyrax.cloud_blockstorage
cnw = pyrax.cloud_networks


#Needs to be fqdn and based on a domain associated with this account
pvt_nets = []
cbs_ids = []
srv_ids = []
imgname = 'CentOS 6.5'
size = 512
new_network_name = "hadoop_net"
new_network_cidr = "192.168.0.0/24"


new_net = cnw.create(new_network_name, cidr=new_network_cidr)
print "New network:", new_net
networks = new_net.get_server_networks(public=True, private=True)

for i in range(1, 4):
    cbsname = 'mycbs' + str(i)
    sata_vol = cbs.create(name=cbsname, size=500, volume_type="SATA")
    pyrax.utils.wait_until(sata_vol,"status","available", interval=1)
    cbs_ids.append(sata_vol.id)
    print "vol %s: %s" % (cbsname, sata_vol)

myimage = [img for img in cs.images.list()
                if imgname in img.name][0]
myflavor = [flavor for flavor in cs.flavors.list()
                if flavor.ram == size][0]

for i in range(1, 4):
    server_name='web' + str(i)
    server = cs.servers.create(server_name, myimage.id, myflavor.id, nics=networks)
    print "Name:", server.name
    print "ID:", server.id
    srv_ids.append(server.id)
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


for i in srv_ids:
    mysrv = cs.servers.get(i)
    pyrax.utils.wait_until(server, "status", "ACTIVE", attempts=0,
                verbose=True)
    for id in cbs_ids:
      vol = cbs.get(id)
      print "attaching vol: %s to srv: %s" % ( vol, mysrv )
      vol.attach_to_instance(mysrv, mountpoint="/dev/xvdb")
      pyrax.utils.wait_until(vol, "status", "in-use", interval=3, attempts=0,
        verbose=True)
      print "Volume attachments:", vol.attachments
      cbs_ids.pop(0)
      break
