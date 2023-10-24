
########################################################################################################################
#
#TOPOLOGY :
# 				  _____________      
#  				 |             |     
# 				 |             |     
#[Ixia]----------|             |----------[Ixia]
#  				 |UUT1(Fretta) |    
#|               |             |
#  				 |             |     
# 				 |_____________ |     
# 
# This script covers CSCwe22842 bug(PVLAN RACL doesn't work after certain reload.):-
#
#  topology requirement :- 1 Fretta switch
#                          2 links to Ixia
#    					   
########################################################################################################################



#!/usr/bin/env python

# import the aetest module
from ats import tcl
from ats import aetest
from ats.log.utils import banner
import time
import logging
import os
import sys
import re
import pdb
import json
import pprint
import socket
import struct
import inspect
#import acp_span_lib
#import ctsPortRoutines
import pexpect
#import span_lib
#libs_dir_path = os.path.join(cur_dir_path, 'libs')
import CSCwe32490_nr3f_lib as l3ptLib
import nxos.lib.nxos.util as util
#import nxos.lib.common.topo as topo


sys.path.append('/auto/dc3-india/hltapi_repository/ixia/IxOS_HLTAPI_8.40/8.40.1400.5/lib/PythonApi')
sys.path.append('/auto/dc3-india/hltapi_repository/ixia/IxOS_HLTAPI_8.40/8.40.1400.5/lib/hltapi/library/common/ixiangpf/python')
from ixiatcl import IxiaTcl
from ixiahlt import IxiaHlt
from ixiangpf import IxiaNgpf
from ixiaerror import IxiaError
from time import sleep

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
global uut1, tgen

global uut1_ixia_intf1, uut1_ixia_intf2
global ixia_uut1_1, ixia_uut1_2

global data_stream_ids
global traffic_stream_id_1,traffic_stream_id_2

def printDict(obj, nested_level=0, output=sys.stdout):
    spacing = '   '
    if type(obj) == dict:
       print('%s' % ((nested_level) * spacing))
       for k, v in list(obj.items()):
           if hasattr(v, '__iter__'):
               print('%s%s:' % ((nested_level + 1) * spacing, k))
               printDict(v, nested_level + 1)
           else:
               print('%s%s: %s' % ((nested_level + 1) * spacing, k, v))
       print('%s' % (nested_level * spacing))
    elif type(obj) == list:
       print('%s[' % ((nested_level) * spacing))
       for v in obj:
           if hasattr(v, '__iter__'):
               printDict(v, nested_level + 1)
           else:
               print('%s%s' % ((nested_level + 1) * spacing, v))
       print('%s]' % ((nested_level) * spacing))
    else:
       print('%s%s' % (nested_level * spacing, obj))


class ForkedPdb(pdb.Pdb):
    '''A Pdb subclass that may be used
    from a forked multiprocessing child1
    '''
    def interaction(self, *args, **kwargs):
        _stdin = sys.stdin
        try:
            sys.stdin = open('/dev/stdin')
            pdb.Pdb.interaction(self, *args, **kwargs)
        finally:
            sys.stdin = _stdin
################################################################################
####                       COMMON SETUP SECTION                             ####
################################################################################

class common_setup(aetest.CommonSetup):

    @aetest.subsection
    def span_topo_parse(self,testscript,testbed,R1):

        global uut1, tgen 

        global uut1_ixia_intf1, uut1_ixia_intf2
        global ixia_uut1_1, ixia_uut1_2
        global ixia_chassis_ip, ixia_tcl_server, ixia_ixnetwork_tcl_server,ixia_username, ixia_reset_flag
        
        global custom
        global device1
        
        
        uut1 = testbed.devices[R1]
        
        tgen = testbed.devices['ixia']
        testscript.parameters['tgen'] = tgen
        
        tgen_attributes = tgen.connections.hltapi
        ixia_chassis_ip = str(tgen_attributes.ip)
        ixia_tcl_server = tgen_attributes.tcl_server
        ixia_ixnetwork_tcl_server = tgen_attributes.ixnetwork_tcl_server
        ixia_username = tgen_attributes.username
        ixia_reset_flag = tgen_attributes.reset
        
        
        ###  UUT 1 INTERFACES  ####
        uut1_ixia_intf1 = testbed.devices[R1].interfaces['uut1_ixia_intf1']
        uut1_ixia_intf2 = testbed.devices[R1].interfaces['uut1_ixia_intf2']
        #uut1_dest_intf1 = testbed.devices[R1].interfaces['uut1_dest_intf1']

        testscript.parameters['uut1_ixia_intf1'] = uut1_ixia_intf1
        testscript.parameters['uut1_ixia_intf2'] = uut1_ixia_intf2
        #testscript.parameters['uut1_dest_intf1'] = uut1_dest_intf1
        
        testscript.parameters['uut1_ixia_intf1'].name = testscript.parameters['uut1_ixia_intf1'].intf
        testscript.parameters['uut1_ixia_intf2'].name = testscript.parameters['uut1_ixia_intf2'].intf
        #testscript.parameters['uut1_dest_intf1'].name = testscript.parameters['uut1_dest_intf1'].intf
        
        ###  Ixia interfaces  ####
        
        ixia_uut1_1 = testbed.devices['ixia'].interfaces['ixia_uut1_1']
        ixia_uut1_2 = testbed.devices['ixia'].interfaces['ixia_uut1_2']
        
        testscript.parameters['ixia_uut1_1'] = ixia_uut1_1
        testscript.parameters['ixia_uut1_2'] = ixia_uut1_2
        
        testscript.parameters['ixia_uut1_1'].name = testscript.parameters['ixia_uut1_1'].intf
        testscript.parameters['ixia_uut1_2'].name = testscript.parameters['ixia_uut1_2'].intf


        uut1_ixia_intf1 =uut1_ixia_intf1.intf
        uut1_ixia_intf2 =uut1_ixia_intf2.intf
        #uut1_dest_intf1 = uut1_dest_intf1.intf

        ixia_uut1_1 = ixia_uut1_1.intf
        ixia_uut1_2 = ixia_uut1_2.intf

        
        log.info("uut1_ixia_intf1=%s" % uut1_ixia_intf1)
        log.info("uut1_ixia_intf2=%s" % uut1_ixia_intf2)
        #log.info("uut1_dest_intf1=%s" % uut1_dest_intf1)
        log.info("ixia_uut1_1=%s" % ixia_uut1_1)
        log.info("ixia_uut1_2=%s" % ixia_uut1_2)
        
    @aetest.subsection
    def connect_to_devices(self, testscript, testbed, R1):
        
        log.info("\n************ Connecting to Device:%s ************" % uut1.name)
        try:
            uut1.connect()
            log.info("Connection to %s Successful..." % uut1.name)
        except Exception as e:
            log.info("Connection to %s Unsuccessful " \
                        "Exiting error:%s" % (uut1.name, e))
            self.failed(goto=['exit'])
    
    @aetest.subsection     
    def enable_feature(self,testscript, testbed,R1):
        log.info(banner("Check Feature private-vlan AND interface-vlan"))
        op = uut1.execute("sh feature | in private-vlan")
        if "enable" not in op:
            cmd = """feature private-vlan 
                    feature interface-vlan 
              """
            uut1.configure(cmd)
    
    @aetest.subsection     
    def configure_pvlan(self,testscript, testbed,R1):
        """configure vlans"""
        pri_vlan_1 = testbed.custom['pri_vlan_1']
        sec_vlan_1 = testbed.custom['sec_vlan_1']
        pri_vlan_2 = testbed.custom['pri_vlan_2']
        sec_vlan_2 = testbed.custom['sec_vlan_2']
        cmd = f"""vlan {pri_vlan_1}
                    private-vlan primary
                    no shut
                    vlan {sec_vlan_1}
                    private-vlan community
                    no shut
                    vlan {pri_vlan_1}
                    private-vlan association {sec_vlan_1}
                    interface vlan {pri_vlan_1}
                    private-vlan mapping {sec_vlan_1}
              """
        uut1.configure(cmd)
        cmd = f"""vlan {pri_vlan_2}
                    private-vlan primary
                    no shut
                    vlan {sec_vlan_2}
                    private-vlan community
                    no shut
                    vlan {pri_vlan_2}
                    private-vlan association {sec_vlan_2}
                    interface vlan {pri_vlan_2}
                    private-vlan mapping {sec_vlan_2}
              """
        uut1.configure(cmd)
         
    @aetest.subsection     
    def configure_interface(self,testscript, testbed,R1):
        pri_vlan_1 = testbed.custom['pri_vlan_1']
        sec_vlan_1 = testbed.custom['sec_vlan_1']
        pri_vlan_2 = testbed.custom['pri_vlan_2']
        sec_vlan_2 = testbed.custom['sec_vlan_2']
        """configure interface"""
        cmd = f"""interface %s
                    switchport 
                    switch mode private-vlan promiscuous
                    switchport private-vlan mapping {pri_vlan_1} {sec_vlan_1}
                    no shut
                    interface %s
                    switchport 
                    switch mode private-vlan promiscuous
                    switchport private-vlan mapping {pri_vlan_2} {sec_vlan_2}
                    no shut
              """%(uut1_ixia_intf1,uut1_ixia_intf2)
        uut1.configure(cmd)
         
    @aetest.subsection     
    def configure_vlan_interface_ip(self,testscript, testbed,R1):
        """configure interface vlans"""
        pri_vlan_1 = testbed.custom['pri_vlan_1']
        sec_vlan_1 = testbed.custom['sec_vlan_1']
        pri_vlan_2 = testbed.custom['pri_vlan_2']
        sec_vlan_2 = testbed.custom['sec_vlan_2']
        g_ip1 = testbed.custom['gateway_ip1']
        g_ip2 = testbed.custom['gateway_ip2']
        cmd = f"""interface vlan {pri_vlan_1}
                    no shutdown
                    no ip redirects
                    private-vlan mapping {sec_vlan_1}
                    ip address {g_ip1}
                    interface vlan {pri_vlan_2}
                    no shutdown
                    no ip redirects
                    private-vlan mapping {sec_vlan_2}
                    ip address {g_ip2}    
              """
        uut1.configure(cmd)
        ForkedPdb().set_trace()
    @aetest.subsection
    def connect_to_ixia(self, testscript, testbed):
       """Connect Ixia and get port handles"""
       #ixia_port_list = [ixia_hdl1, ixia_hdl2]
       ixia_port_list = [ixia_uut1_1, ixia_uut1_2]
       global ixia_
       global ixia_port_1_handle,ixia_port_2_handle
       
       status,port_handle = l3ptLib.connect_ixia(ixia_chassis_ip, ixia_tcl_server, ixia_ixnetwork_tcl_server, \
                                                       ixia_port_list, ixia_reset_flag, ixia_username)
       if status != True:
           log.error("\nFail to Connect Ixia!!")
           self.failed(goto=['exit'])
       else:
           # ForkedPdb().set_trace()
           ixia_port_1_handle = port_handle.split(' ')[0]
           ixia_port_2_handle = port_handle.split(' ')[1]
           log.info("\nixia_port_1_handle = {}".format(ixia_port_1_handle))
           log.info("\nixia_port_2_handle = {}".format(ixia_port_2_handle))
           self.passed("Connected Ixia and got port handles!!")
          
        ##############################################################
        # config the parameters for IXIA stream
        ##############################################################
    @aetest.subsection
    def configure_ixia_interfaces(self, testscript, testbed):
        """Configure IPs to ixia interfaces"""
        global protocol_intf_handle_9,protocol_intf_handle_20,protocol_intf_handle_30,protocol_intf_handle_40
        global ixia_port_list
        intf_handle_list = []
        ixia_port_list = [ixia_port_1_handle, ixia_port_2_handle]
        #ForkedPdb().set_trace()
        
        status,interface_handle = l3ptLib.config_ixia_L3_interfaces(ixia_port_2_handle, '200.2.12.2', '200.2.12.50', '255.255.255.0', '00:15:ac:bc:7a:2a', '1500', '0')
        if status != True:
            log.error("\n Fail to configure mac address to port 1")
            self.failed(goto=['exit'])
        else:
            intf_handle_list.append(interface_handle)
            log.info("\nSuccessfully configured mac address to port 1")
        
        status,interface_handle = l3ptLib.config_ixia_L3_interfaces(ixia_port_2_handle, '200.2.12.2', '200.2.12.60', '255.255.255.0', '00:15:ac:bc:7a:3b', '1500', '0')
        if status != True:
            log.error("\n Fail to configure mac address to port 1")
            self.failed(goto=['exit'])
        else:
            intf_handle_list.append(interface_handle)
            log.info("\nSuccessfully configured mac address to port 1")
            
        status,interface_handle = l3ptLib.config_ixia_L3_interfaces(ixia_port_1_handle, '100.1.11.1', '100.1.11.50', '255.255.255.0', '00:15:ac:bc:7a:ba', '1500', '0')
        if status != True:
            log.error("\n Fail to configure mac address to port 2")
            self.failed(goto=['exit'])
        else:
            intf_handle_list.append(interface_handle)
            log.info("\nSuccessfully configured mac address to port 2")
        
        status,interface_handle = l3ptLib.config_ixia_L3_interfaces(ixia_port_1_handle, '100.1.11.1', '100.1.11.60', '255.255.255.0', '00:15:ac:bc:7a:cd', '1500', '0')
        if status != True:
            log.error("\n Fail to configure mac address to port 2")
            self.failed(goto=['exit'])
        else:
            intf_handle_list.append(interface_handle)
            log.info("\nSuccessfully configured mac address to port 2")
        
        protocol_intf_handle_9 = intf_handle_list[0]
        protocol_intf_handle_20 = intf_handle_list[1]
        protocol_intf_handle_30 = intf_handle_list[2]
        protocol_intf_handle_40 = intf_handle_list[3]
        
        log.info("\n\nConfigured interface handles:")
        log.info("protocol_intf_handle_9: {}".format(protocol_intf_handle_9))
        log.info("protocol_intf_handle_20: {}".format(protocol_intf_handle_20))
        log.info("protocol_intf_handle_30: {}".format(protocol_intf_handle_30))
        log.info("protocol_intf_handle_40: {}".format(protocol_intf_handle_40))
        
        self.passed("IP configuration  to ixia interfaces Successful!!")    
    
    
    @aetest.subsection
    def configure_ixia_traffic_streams(self, testscript, testbed):
        """Configure regular traffic streams on ixia ports"""

        global traffic_stream_id_1, traffic_stream_id_2
        stream_handle_list = []
        ForkedPdb().set_trace()
        intf_handle_list = [protocol_intf_handle_9, protocol_intf_handle_20, protocol_intf_handle_30, protocol_intf_handle_40]

        #####traffic stream Isolated to trunk secondary via trunk promiscous port ##########
        status,stream_handle = l3ptLib.config_traffic_stream1(protocol_intf_handle_30,protocol_intf_handle_9,'stream1','1000','ipv4')
        
        if status != True:
            log.error("\n Fail to create first traffic stream")
            self.failed(goto=['exit'])
        else:
            stream_handle_list.append(stream_handle)
            log.info("\nSuccessfully created 1st traffic stream")
                    

        traffic_stream_id_1 = stream_handle_list[0]
        testscript.parameters['traffic_stream_id_1'] = traffic_stream_id_1
        
        log.info("traffic_stream_id_1: {}".format(traffic_stream_id_1))
        
        status,stream_handle = l3ptLib.config_traffic_stream1(protocol_intf_handle_40,protocol_intf_handle_20,'stream2','1000','ipv4')  ##Second Traffic
        
        if status != True:
            log.error("\n Fail to create second traffic stream")
            self.failed(goto=['exit'])
        else:
            stream_handle_list.append(stream_handle)
            log.info("\nSuccessfully created second traffic stream")
                    

        traffic_stream_id_2 = stream_handle_list[1]
       
        
        log.info("traffic_stream_id_2: {}".format(traffic_stream_id_2))
       
        
        self.passed("Regular Ixia streams are configured Successfully!!")
        
    @aetest.subsection
    def start_traffic_streams(self, testscript, testbed):
        """Start all ixia traffic streams and validate counters"""
        
        global data_stream_ids
        global traffic_stream_id_1
        
        data_stream_ids = [traffic_stream_id_1] 
        
        l3ptLib.run_traffic_stream1(traffic_stream_id_1)
        time.sleep(30)
        
        ForkedPdb().set_trace()
        self.passed("No issues seen in starting ixia streams and fetching stats!!")    
       
   ################################################################################################################# 
    #ForkedPdb().set_trace()
class CSCwe22842(aetest.Testcase):
    """KR5M|| Fretta || PVLAN RACL doesn't work after certain reload."""
    @aetest.test
    def verify_traffic(self, testscript, testbed):
        cmd = """show interface %s, %s """%(uut1_ixia_intf1,uut1_ixia_intf2)
        op = uut1.execute(cmd)
        
        log.info("verify TX and RX counters on UUT1")
        output = l3ptLib.get_traffic_stream('traffic_item','TI0-stream1')
        log.info(output)
        #ForkedPdb().set_trace()
        status,tx_packet_rate,rx_packet_rate = l3ptLib.get_traffic_stream('traffic_item','TI0-stream1')
         ##Check Second stream status
        
        tx_packet_rate = tx_packet_rate.get('total_pkt_rate')
        rx_packet_rate = rx_packet_rate.get('total_pkt_rate')
        
        log.info(tx_packet_rate)
        log.info(rx_packet_rate)
        
        if float(990) < float(tx_packet_rate) < float(1100) :
           log.info("tx rate is %s \n"%(tx_packet_rate))
           if float(990) > float(rx_packet_rate) < float(1100) :
               log.info("rx rate is %s \n"%(rx_packet_rate))
               log.info("Traffic is forwarding correctly to destination")
           else:
                self.passed("no traffic forwarded to destination")
        else:
            self.failed("tx rate is %s ,expected 990 to 1100\n"%(tx_packet_rate))
        
    @aetest.test 
    def configure_RACL(self,testscript, testbed,R1):
        """Configure RACL"""
        
        log.info("Hardware Cli")
        cmd = """hardware profile acl-stats module all"""
        uut1.configure(cmd)
        
        uut1.execute("copy r s")
        
        ForkedPdb().set_trace()
        pri_vlan_1 = testbed.custom['pri_vlan_1']
        cmd = f"""ip access-list test1
                statistics per-entry
                10 deny ip 100.1.11.50/32 200.2.12.50/32 
                20 permit ip any any
                interface vlan {pri_vlan_1}
                ip access-group test1 in
             """
        uut1.configure(cmd)
        op=uut1.execute("sh ip access-lists test1")
        matches = re.findall(r'\[match=(\d+)\]', op)
        l = matches[0]
        log.info(l)
        for match in matches:
            if int(l) > 0:
                log.info(f"Match value {match} - Passed")
            else:
                log.info(f"Match value {match} - Failed")
                # self.failed(goto=['common_cleanup'])
           
        cmd = f"""interface vlan {pri_vlan_1}
                 ip access-group test1 in
              """
        uut1.configure(cmd)
        ForkedPdb().set_trace()
          
        log.info("verify TX and RX counters on UUT1 after applying racl")
        output = l3ptLib.get_traffic_stream('traffic_item','TI0-stream1')
        log.info(output)
        #ForkedPdb().set_trace()
        status,tx_packet_rate,rx_packet_rate = l3ptLib.get_traffic_stream('traffic_item','TI0-stream1')
        
        tx_packet_rate = tx_packet_rate.get('total_pkt_rate')
        rx_packet_rate = rx_packet_rate.get('total_pkt_rate')
        
        log.info(tx_packet_rate)
        log.info(rx_packet_rate)
        
        if float(990) < float(tx_packet_rate) < float(1100) :
           log.info("tx rate is %s \n"%(tx_packet_rate))
           if float(990) < float(rx_packet_rate) < float(1100) :
               log.info("rx rate is %s \n"%(rx_packet_rate))
               self.failed("RX rate is not Zero as acl is applied in ingress, which is not expected")
           else:
                log.info("RACL is applied correctly")
        else:
            self.failed("tx rate is %s ,expected 990 to 1100\n"%(tx_packet_rate))
        
        
        cmd = """show interface %s, %s """%(uut1_ixia_intf1,uut1_ixia_intf2)
        op = uut1.execute(cmd)
        match = re.search(r'RX\n(.+?)TX', op, re.DOTALL)
        if match:
           rx_section = match.group(1).strip()
           # Extract "1101868 unicast" from the section
           rx_value = re.search(r'(\d+ unicast)', rx_section)
           # print(rx_value)
           if rx_value:
               result = rx_value.group(1)
               x = result.split(" ")
               o = x[0]
               log.info(f"Packets Value is {o}")
               if o > "0":
                   log.info("Pass")
               else:
                   log.error("Fail")
                   

                   # self.failed(goto=['exit'])
                   
         
         
             
class reload_switch(aetest.Testcase):
    """Reloading the box"""
    @aetest.test
    def reload_setup(self,testbed,testscript ):
        log.info(banner(f"Reloading {uut1} device"))
        l3ptLib.reload(uut1)

class verify_match_after_reload(aetest.Testcase):
    """Verifing match in traffic after switch reload"""
    @aetest.test
    def verify_match_after_reload(self,testbed,testscript):
        op=uut1.execute("sh ip access-lists test1")
        matches = re.findall(r'\[match=(\d+)\]', op)
        # v = matches.split(",")
        l = matches[0]
        log.info(l)
        for match in matches:
            if int(l) > 0:
                log.info(f"Match value {match} - Passed")
            else:
                log.error(f"Match value {match} - Failed")
                # self.failed(goto=['exit'])
                
                
#######################################################################
# class CSCwe48583(aetest.Testcase):
#     """fretta pvlan || unmactch acl traffic gets blocked on after applying RACL on SVI"""
#     
#     @aetest.setup
#     def verify_acl(self,testscript,testbed):
#         cmd = "sh ip access-lists test1"
#         uut1.execute(cmd)
#         
#     
#     @aetest.test
#     def start_and_verify_traffic(self, testscript, testbed):
#         
#         """Start all ixia traffic streams and validate counters"""
#         
#         global data_stream_ids
#         global traffic_stream_id_1,traffic_stream_id_2
#         
#         data_stream_ids = [traffic_stream_id_2] 
#         
#         l3ptLib.run_traffic_stream1(traffic_stream_id_2)
#         time.sleep(30)
#         
#         log.info("verify TX and RX counters on UUT1")
#         output = l3ptLib.get_traffic_stream('traffic_item','TI0-stream2')
#         log.info(output)
#         #ForkedPdb().set_trace()
#         status,tx_packet_rate,rx_packet_rate = l3ptLib.get_traffic_stream('traffic_item','TI0-stream2')
#          ##Check Second stream status
#         
#         tx_packet_rate = tx_packet_rate.get('total_pkt_rate')
#         rx_packet_rate = rx_packet_rate.get('total_pkt_rate')
#         
#         log.info(tx_packet_rate)
#         log.info(rx_packet_rate)
#         
#         if float(990) < float(tx_packet_rate) < float(1100) :
#            log.info("tx rate is %s \n"%(tx_packet_rate))
#            if float(990) > float(rx_packet_rate) < float(1100) :
#                log.info("rx rate is %s \n"%(rx_packet_rate))
#                log.info("Traffic is forwarding correctly to destination")
#            else:
#                 self.passed("no traffic forwarded to destination")
#         else:
#             self.failed("tx rate is %s ,expected 990 to 1100\n"%(tx_packet_rate))
#         
#     @aetest.test 
#     def verify_RACL(self,testscript, testbed,R1):
#         pri_vlan_1 = testbed.custom['pri_vlan_1']
#         op=uut1.execute("sh ip access-lists test1")
#         matches = re.findall(r'\[match=(\d+)\]', op)
#         l = matches[1]
#         log.info(l)
#         for match in matches:
#             if int(l) > 0:
#                 log.info(f"Match value {match} - Passed")
#             else:
#                 log.info(f"Match value {match} - Failed")
#                 # self.failed(goto=['common_cleanup'])
#            
#         cmd = f"""interface vlan {pri_vlan_1}
#                  ip access-group test1 in
#               """
#         uut1.configure(cmd)
#         #ForkedPdb().set_trace()
#           
#         log.info("verify TX and RX counters on UUT1 after applying racl")
#         output = l3ptLib.get_traffic_stream('traffic_item','TI0-stream2')
#         log.info(output)
#         #ForkedPdb().set_trace()
#         status,tx_packet_rate,rx_packet_rate = l3ptLib.get_traffic_stream('traffic_item','TI0-stream2')
#         
#         tx_packet_rate = tx_packet_rate.get('total_pkt_rate')
#         rx_packet_rate = rx_packet_rate.get('total_pkt_rate')
#         
#         log.info(tx_packet_rate)
#         log.info(rx_packet_rate)
#         
#         if float(990) < float(tx_packet_rate) < float(1100) :
#            log.info("tx rate is %s \n"%(tx_packet_rate))
#            if float(990) < float(rx_packet_rate) < float(1100) :
#                log.info("rx rate is %s \n"%(rx_packet_rate))
#                self.failed("RX rate is not Zero as acl is applied in ingress, which is not expected")
#            else:
#                 log.info("RACL is applied correctly")
#         else:
#             self.failed("tx rate is %s ,expected 990 to 1100\n"%(tx_packet_rate))
#         
#         
#         
#         
#         cmd = """show interface %s, %s """%(uut1_ixia_intf1,uut1_ixia_intf2)
#         op = uut1.execute(cmd)
#         match = re.search(r'RX\n(.+?)TX', op, re.DOTALL)
#         if match:
#            rx_section = match.group(1).strip()
#            # Extract "1101868 unicast" from the section
#            rx_value = re.search(r'(\d+ unicast)', rx_section)
#            # print(rx_value)
#            if rx_value:
#                result = rx_value.group(1)
#                x = result.split(" ")
#                o = x[0]
#                log.info(f"Packets Value is {o}")
#                if o > "0":
#                    log.info("Pass")
#                else:
#                    log.error("Fail")
#                    # self.failed(goto=['exit'])
#         ForkedPdb().set_trace()
#          
#          
#              
# class reload_switch(aetest.Testcase):
#     """Reloading the box"""
#     @aetest.test
#     def reload_setup(self,testbed,testscript ):
#         log.info(banner(f"Reloading {uut1} device"))
#         l3ptLib.reload(uut1)
# 
# class verify_match_after_reload(aetest.Testcase):
#     """Verifing match in traffic after switch reload"""
#     @aetest.test
#     def verify_match_after_reload(self,testbed,testscript):
#         op=uut1.execute("sh ip access-lists test1")
#         matches = re.findall(r'\[match=(\d+)\]', op)
#         # v = matches.split(",")
#         l = matches[0]
#         log.info(l)
#         for match in matches:
#             if int(l) > 0:
#                 log.info(f"Match value {match} - Passed")
#             else:
                # log.error(f"Match value {match} - Failed")
                # self.failed(goto=['exit'])
########################################################################################################################
################################################################################
####                       COMMON CLEANUP SECTION                           ####
################################################################################


class common_cleanup(aetest.CommonCleanup):

    @aetest.subsection
    def remove_configuration(self,testbed,testscript):
    
        #############################################################
        #clean up the session, release the ports reserved and cleanup the dbfile
        #############################################################
        pri_vlan_1 = testbed.custom['pri_vlan_1']
        sec_vlan_1 = testbed.custom['sec_vlan_1']
        pri_vlan_2 = testbed.custom['pri_vlan_2']
        sec_vlan_2 = testbed.custom['sec_vlan_2']
        log.info('remove vlans')
        cmd = f""" no vlan {pri_vlan_1}
                  no vlan {sec_vlan_1}
                  no vlan {pri_vlan_2}
                  no vlan {sec_vlan_2}
                  no int vlan {pri_vlan_1}
                  no int vlan {pri_vlan_2}
              """
        uut1.configure(cmd)
        
        log.info('remove the acl config')
        cmd = """no ip access-list test1"""
        uut1.configure(cmd)
        log.info('remove configuration in {0}'.format(uut1))
        cmd = """ default interface %s """%(uut1_ixia_intf1)
        uut1.configure(cmd)
        cmd = """ default interface %s """%(uut1_ixia_intf2)
        uut1.configure(cmd)
        
        log.info('Remove Feature private-vlan AND interface-vlan')
        cmd = """no feature private-vlan 
                   no feature interface-vlan 
              """
        uut1.configure(cmd)

if __name__ == '__main__': # pragma: no cover
    import argparse
    from ats import topology
    parser = argparse.ArgumentParser(description='standalone parser')
    parser.add_argument('--testbed', dest='testbed', type=topology.loader.load)
    parser.add_argument('--R1', dest='R1', type=str)
    parser.add_argument('--mode',dest = 'mode',type = str)
    args = parser.parse_known_args()[0]
    aetest.main(testbed=args.testbed,
                R1_name=args.R1,
                mode = args.mode,
                pdb = True)
