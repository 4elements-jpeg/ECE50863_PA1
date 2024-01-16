#!/usr/bin/env python

"""This is the Switch Starter Code for ECE50863 Lab Project 1
Author: Xin Du
Email: du201@purdue.edu
Last Modified Date: December 9th, 2021
"""

import sys
from datetime import date, datetime
import socket
import pickle
import signal
import time
import threading

def handler(signum, frame):
    res = input("Ctrl-c was pressed. Do you really want to exit? y/n ")
    # if res == 'y':
    exit(1)
signal.signal(signal.SIGINT, handler)

# Please do not modify the name of the log file, otherwise you will lose points because the grader won't be able to find your log file
LOG_FILE = "switch#.log" # The log file for switches are switch#.log, where # is the id of that switch (i.e. switch0.log, switch1.log). The code for replacing # with a real number has been given to you in the main function.

# Those are logging functions to help you follow the correct logging standard

# "Register Request" Format is below:
#
# Timestamp
# Register Request Sent

def register_request_sent():
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append(f"Register Request Sent\n")
    write_to_log(log)

# "Register Response" Format is below:
#
# Timestamp
# Register Response Received

def register_response_received():
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append(f"Register Response received\n")
    write_to_log(log) 

# For the parameter "routing_table", it should be a list of lists in the form of [[...], [...], ...]. 
# Within each list in the outermost list, the first element is <Switch ID>. The second is <Dest ID>, and the third is <Next Hop>.
# "Routing Update" Format is below:
#
# Timestamp
# Routing Update 
# <Switch ID>,<Dest ID>:<Next Hop>
# ...
# ...
# Routing Complete
# 
# You should also include all of the Self routes in your routing_table argument -- e.g.,  Switch (ID = 4) should include the following entry: 		
# 4,4:4

def routing_table_update(routing_table):
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append("Routing Update\n")
    for row in routing_table:
        log.append(f"{row[0]},{row[1]}:{row[2]}\n")
    log.append("Routing Complete\n")
    write_to_log(log)

# "Unresponsive/Dead Neighbor Detected" Format is below:
#
# Timestamp
# Neighbor Dead <Neighbor ID>

def neighbor_dead(switch_id):
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append(f"Neighbor Dead {switch_id}\n")
    write_to_log(log) 

# "Unresponsive/Dead Neighbor comes back online" Format is below:
#
# Timestamp
# Neighbor Alive <Neighbor ID>

def neighbor_alive(switch_id):
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append(f"Neighbor Alive {switch_id}\n")
    write_to_log(log) 

def write_to_log(log):
    with open(LOG_FILE, 'a+') as log_file:
        log_file.write("\n\n")
        # Write to log
        log_file.writelines(log)
        
        
class Switch:
    def __init__(self, switch_id, controller_addr):
        print(f'Creating switch with ID = {switch_id}')
        self.switch_id = int(switch_id)
        self.controller_addr = controller_addr
        self.live_neighbors = set()
        self.neighbor_statuses = {}
        self.connected_switches = {}
        self.routing_table = {}
        self.K = 2
        self.TIMEOUT = 3 * self.K
        self.switch_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    
    def send_register_request(self):
        # Send Register REQUESTS
        msg = ['Register_Request',self.switch_id]
        data = pickle.dumps(msg)
        self.switch_socket.sendto(data, self.controller_addr)
        register_request_sent()
        print('Switch sent register request to the controller')
    
    
    def send_keep_alive(self):
        '''This function is used to send a Keep_Alive message to each of the 
        neighboring switches it thinks is alive every K seconds.'''
        msg = ['Keep_Alive',self.switch_id]
        data = pickle.dumps(msg)
        while True:
            time.sleep(self.K)
            for neighbor in self.live_neighbors:
                if self.switch_id != neighbor:
                    self.switch_socket.sendto(data, self.connected_switches[neighbor])
                    print(f'Switch {self.switch_id} sending Keep_Alive to switch {self.connected_switches[neighbor]}')


    def send_topology_update(self):
        '''This function is used to send a Topology_Update message to the 
        controller every K seconds. The Topology Update message includes a set 
        of live neighbors.'''
        while True:
            time.sleep(self.K)
            msg = ['Topology_Update',self.switch_id,self.neighbor_statuses]
            data = pickle.dumps(msg)
            self.switch_socket.sendto(data,self.controller_addr)
            print(f'Switch {self.switch_id} sending Topology_Update to controller')
            print(f'Neighbor Statuses = {self.neighbor_statuses}')
                
            
    def handle_timeout(self,neighbor):
        while True:
            time.sleep(self.TIMEOUT)
            # Simulate checking for timeout
            if self.neighbor_statuses.get(neighbor, 0) < time.time() - self.TIMEOUT:
                neighbor_dead(neighbor)
                print(f"Timeout for Switch {neighbor} detected by Switch {self.switch_id}")
                # Mark the neighbor as down, update topology, and notify the controller
                self.live_neighbors.discard(neighbor)
                self.neighbor_statuses[neighbor] = False
                self.send_topology_update()
    
    def handle_recv_message(self,recvd_data, recvd_addr):
        # Check if the recvd addr is from the controller
        recvd_msg =  pickle.loads(recvd_data)
        
        request_type = recvd_msg[0]
        msg = recvd_msg[1]
        print(msg)
        
        if request_type == 'Register_Response':
            register_response_received()
            
            for line in msg.split('\n')[1:]:
                l = line.split()
                if l:
                    neighbor_id, addr, port = l
                    neighbor_id = int(neighbor_id)
                    self.connected_switches[neighbor_id] = (addr, port)
                    self.live_neighbors.add(neighbor_id)
                    self.neighbor_statuses[neighbor_id] = True
            print('Register Response')
            print(f'Connected Switches = {self.connected_switches}')
            print(f'Live Neighbors = {self.live_neighbors}')
            print(f'Neighbor Statuses = {self.neighbor_statuses}')
                
        elif request_type == 'Routing_Update':
            routing_table_update(msg)
            self.routing_table = msg
            print(f'Routing_Update = {self.routing_table}')
            
        # if a switch receives a keep alive message from a switch it previously 
        # considered unreachable it updates the host/post info and sends a 
        # topology update to the controller
        elif (request_type == 'Keep_Alive'):
            neighbor_id = int(msg)
            if neighbor_id not in self.live_neighbors:
                print(f'neighbor {neighbor_id} is alive again')
                neighbor_alive(neighbor_id)
                self.connected_switches[neighbor_id] = recvd_addr
                self.live_neighbors.add(neighbor_id)
                self.neighbor_statuses[neighbor_id] = time.time()
                self.send_topology_update()
            else:
                self.connected_switches[neighbor_id] = recvd_addr
                self.neighbor_statuses[neighbor_id] = time.time()
                
    def receive_messages(self):
        while True:
            recvd_data, addr = self.switch_socket.recvfrom(1024)
            self.handle_recv_message(recvd_data, addr)
            
                
                
    def run(self):
        # Start threads for Keep Alive, Topology Update, and Timeout Handling
        threading.Thread(target=self.receive_messages, daemon=True).start()
        
        threading.Thread(target=self.send_keep_alive, daemon=True).start()
        # threading.Thread(target=self.handle_timeout, daemon=True).start()

        threading.Thread(target=self.send_topology_update, daemon=True).start()
            


def main():

    global LOG_FILE

    #Check for number of arguments and exit if host/port not provided
    num_args = len(sys.argv)
    if num_args < 4:
        print ("switch.py <Id_self> <Controller hostname> <Controller Port>\n")
        sys.exit(1)

    my_id = int(sys.argv[1])
    LOG_FILE = 'switch' + str(my_id) + ".log" 

    # Write your code below or elsewhere in this file
    # run on computer from cmd line by python -m switch arguements...
    
    controller_hostname = sys.argv[2]
    controller_port = int(sys.argv[3])
    controller_addr = (controller_hostname, controller_port)

    # Process command line inputs for -f flag
    flag1 = False
    neighbor_id = None
    for arg in sys.argv[1:]:
        if arg == '-f':
            flag1 = True
            neighbor_id = int(sys.argv[-1])
    
    switch = Switch(my_id,controller_addr)
    switch.send_register_request()
    print("\nWaiting for response from controller...")
    recvd_data, controller_addr = switch.switch_socket.recvfrom(1024)
    switch.handle_recv_message(recvd_data, controller_addr)
    print('---> Received response from controller')
    
    print('Starting Threading')
    switch.run()


if __name__ == "__main__":
    main()