#!/usr/bin/env python

"""This is the Controller Starter Code for ECE50863 Lab Project 1
Author: Xin Du
Email: du201@purdue.edu
Last Modified Date: December 9th, 2021
"""

import sys
from datetime import date, datetime
import socket
import heapq
import pickle
import signal
import time
import threading

def handler(signum, frame):
    res = input("Ctrl-c was pressed. Do you really want to exit? y/n ")
    if res == 'y':
        exit(1)
signal.signal(signal.SIGINT, handler)

# Please do not modify the name of the log file, otherwise you will lose points because the grader won't be able to find your log file
LOG_FILE = "Controller.log"

# Those are logging functions to help you follow the correct logging standard

# "Register Request" Format is below:
#
# Timestamp
# Register Request <Switch-ID>

def register_request_received(switch_id):
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append(f"Register Request {switch_id}\n")
    write_to_log(log)

# "Register Responses" Format is below (for every switch):
#
# Timestamp
# Register Response <Switch-ID>

def register_response_sent(switch_id):
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append(f"Register Response {switch_id}\n")
    write_to_log(log) 

# For the parameter "routing_table", it should be a list of lists in the form of [[...], [...], ...]. 
# Within each list in the outermost list, the first element is <Switch ID>. The second is <Dest ID>, and the third is <Next Hop>, and the fourth is <Shortest distance>
# "Routing Update" Format is below:
#
# Timestamp
# Routing Update 
# <Switch ID>,<Dest ID>:<Next Hop>,<Shortest distance>
# ...
# ...
# Routing Complete
#
# You should also include all of the Self routes in your routing_table argument -- e.g.,  Switch (ID = 4) should include the following entry: 		
# 4,4:4,0
# 0 indicates ‘zero‘ distance
#
# For switches that can’t be reached, the next hop and shortest distance should be ‘-1’ and ‘9999’ respectively. (9999 means infinite distance so that that switch can’t be reached)
#  E.g, If switch=4 cannot reach switch=5, the following should be printed
#  4,5:-1,9999
#
# For any switch that has been killed, do not include the routes that are going out from that switch. 
# One example can be found in the sample log in starter code. 
# After switch 1 is killed, the routing update from the controller does not have routes from switch 1 to other switches.

def routing_table_update(routing_table):
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append("Routing Update\n")
    for row in routing_table:
        log.append(f"{row[0]},{row[1]}:{row[2]},{row[3]}\n")
    log.append("Routing Complete\n")
    write_to_log(log)

# "Topology Update: Link Dead" Format is below: (Note: We do not require you to print out Link Alive log in this project)
#
#  Timestamp
#  Link Dead <Switch ID 1>,<Switch ID 2>

def topology_update_link_dead(switch_id_1, switch_id_2):
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append(f"Link Dead {switch_id_1},{switch_id_2}\n")
    write_to_log(log) 

# "Topology Update: Switch Dead" Format is below:
#
#  Timestamp
#  Switch Dead <Switch ID>

def topology_update_switch_dead(switch_id):
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append(f"Switch Dead {switch_id}\n")
    write_to_log(log) 

# "Topology Update: Switch Alive" Format is below:
#
#  Timestamp
#  Switch Alive <Switch ID>

def topology_update_switch_alive(switch_id):
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append(f"Switch Alive {switch_id}\n")
    write_to_log(log) 

def write_to_log(log):
    with open(LOG_FILE, 'a+') as log_file:
        log_file.write("\n\n")
        # Write to log
        log_file.writelines(log)

def open_file(config_file):
    '''This function takes the filepath for a graph_n.txt file and returns a 
    dictionary where each key is a switch id/node and the number of switches. 
    The value is a nested dictionary that has a key-value pair for each 
    neighbor where key=neighbor_id and value=link cost. 
    ie. d = {node1:{node2:cost, node3:cost}, node2:{node3:cost}}'''
    d = {}
    
    with open(config_file, 'r') as f:
        f = f.readlines()
        num_switches = int(f[0]) 
          
        # Create initial empty dictionary where link cost is zero for self and 
        # 9999 otherwise
        for self_id in range(num_switches):
            d[self_id] = {}
            for neighbor_id in range(num_switches):
                if neighbor_id == self_id:
                    cost = 0
                else:
                    cost = 9999
                d[self_id][neighbor_id] = cost

        # Now update each cost based on the config file
        for line in f[1:]:
            line = line.split()
            self_id = int(line[0])
            neighbor_id = int(line[1])
            cost = int(line[2])
            
            # Update values
            d[self_id][neighbor_id] = cost
            d[neighbor_id][self_id] = cost
    
    return d,num_switches

def min_distance(distances, visited):
    '''Function to find the node with the smallest distance that has not been 
    visited yet'''
    # Initialize minimum distance for next node
    min_val = 9999
    min_index = -1

    # Loop through all nodes to find minimum distance
    for i in range(len(distances)):
        if distances[i] < min_val and i not in visited:
            min_val = distances[i]
            min_index = i
    return min_index

def dijkstra(graph, live_switches, start_node):
    num_nodes = len(graph)

    distances = {node: int(9999) for node in range(num_nodes)}
    paths = {node: [] for node in range(num_nodes)}
    next_hop = {node: -1 for node in range(num_nodes)}
    visited = set()
    
    if start_node in live_switches:
        next_hop[start_node] = start_node
        distances[start_node] = 0
    else:
        next_hop[start_node] = -1
        distances[start_node] = 9999

    priority_queue = [(0, start_node)]

    while priority_queue:
        current_distance, current_node = heapq.heappop(priority_queue)
        if current_node not in live_switches:
            continue
        
        elif current_node in visited:
            continue

        visited.add(current_node)

        for neighbor, weight in enumerate(graph[current_node]):
            if weight != 0 and neighbor not in visited:
                new_distance = distances[current_node] + weight

                if new_distance < distances[neighbor]:
                    distances[neighbor] = new_distance
                    paths[neighbor] = paths[current_node] + [current_node]
                    next_hop[neighbor] = current_node
                    heapq.heappush(priority_queue, (new_distance, neighbor))

    return distances, paths, next_hop

def generate_response_msg(connected_switches):
    '''connected_switches is a dictionary where the Key=switch_id and 
    value=switch_addr where switch_addr is a tuple (addr,port_number) and
    creates a response message to be sent. The response message has a format
    where it is a list [REPONSE_TYPE, message_body].'''
    
    l = ['Register_Response']
    num_switches = len(connected_switches)
    
    msg = f'{num_switches} \n'
    count = 0
    
    for switch_id,switch_addr in connected_switches.items():
        addr, port_number = switch_addr
        msg += f'{switch_id} {addr} {port_number}'
        if count < num_switches:
            msg += '\n'
        count += 1
    
    l.append(msg)
    return l

def generate_routing_table_msg(routing_table):
    '''This function creates the routing table message that is sent to all 
    switches. The response message has a format where it is a list 
    [REPONSE_TYPE, message_body] RESPONSE-TYPE == 'Routing_Update' '''
    l = ['Routing_Update']
    l.append(routing_table)
    return l

def send_message(socket, connected_switches, message):
    print(f'Send Message: \n{message}')
    message_type = message[0]
    print(f'Message Type: {message_type}')
    
    if message_type == 'Register_Response':
        message = pickle.dumps(message) # Pickle Message to be sent
        for switch_id,switch_addr in connected_switches.items():
            socket.sendto(message, switch_addr)
            register_response_sent(switch_id)
            print(f'Sent Register_Response to switch#{switch_id} @ {switch_addr}')
    
    elif message_type == 'Routing_Update':
        routing_table = message[1]
        for switch_id,switch_addr in connected_switches.items():
            switch_routing_table = ['Routing_Update']
            l = []
            for entry in routing_table:
                if entry[0] == switch_id:
                    l.append(entry[0:3])
            switch_routing_table.append(l)
            message = pickle.dumps(switch_routing_table) # Pickle Message to be sent
            socket.sendto(message, switch_addr)
            
        print('!!!Sent ALL Routing_Update')
        
class Controller:
    def __init__(self, controller_port, config_file):
        print(f'Creating controller with port number {controller_port}')
        self.controller_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.controller_hostname = socket.gethostname()
        self.controller_port = int(controller_port)
        self.controller_addr = (self.controller_hostname,self.controller_port)
        self.controller_socket.bind(self.controller_addr)
        
        self.config_file = config_file
        self.d = {}
        self.d_changes = None
        self.total_num_switches = int()
        self.switch_addresses = {}
        self.graph = None
        self.routing_table = None
        self.switch_statuses = {}
        self.live_switches = set()
        self.K = 2
        self.TIMEOUT = 3 * self.K
        
    def create_graph(self):
        '''This function creates a graph from d that is passed into the function 
        dijkstra_algorithm().'''
        self.graph = []
        for self_id in self.d:
            l = []
            for cost in self.d[self_id].values():
                l.append(cost)
            self.graph.append(l)
        print(self.graph)
        
    def create_routing_table(self):
        '''create_routing_table returns a list of the format of a nested list.
        For the parameter "routing_table", it should be a list of lists in the form 
        of [[...], [...], ...]. Within each list in the outermost list, 
        the first element is <Switch ID>. The second is <Dest ID>, 
        and the third is <Next Hop>, and the fourth is <Shortest distance>'''
        routing_table = []
        
        for node in range(len(self.graph)):
            
            print("NODE ",node)
            distances, paths, next_hop = dijkstra(self.graph, self.live_switches, node)
            
            print(f'DISTANCES = {distances}')
            print(f'PATHS = {paths}')
            print(f'NEXT_HOP = {next_hop}')
            for key,value in distances.items():
                switch_id = node
                dest_id = key
                hop = None
                shortest_distance = distances[key]
                
                # If the key (ie. node #n is in live switches act normally)
                if key in self.live_switches:
                    # Node is itself
                    if paths[key] == []:
                        print("Empty LIST")
                        hop = node
                    # Next path is 
                    elif shortest_distance == 9999:
                        hop = -1
                    elif len(paths[key]) == 1:
                        hop = key
                    else:
                        hop = paths[key][1]
                        
                # If the key (ie. node #n is not in live switches assign hop = -1 and distance to inf)      
                else:
                    hop = -1
                    shortest_distance = 9999
                        
                # only create routing table for live switches
                if node in self.live_switches:
                    l = [switch_id] # first element of the list is Switch_ID
                    l.append(dest_id) # second element of the list is Destination_ID
                    l.append(hop)
                    l.append(shortest_distance) # fourth element of the list is Shortest Distance
                    routing_table.append(l)
        self.routing_table = routing_table
        
    def recompute_paths_and_send_update(self):
        print("Controller recompute_paths_and_send_update()")
        self.create_routing_table()
        
        # LOG - Routing Table
        routing_table_update(self.routing_table)
        # Send Routing Table
        routing_table_msg = generate_routing_table_msg(self.routing_table)
        for switch_id in self.live_switches:
            l = []
            for entry in self.routing_table:
                if entry[0] == switch_id:
                    l.append(entry[0:3])
            routing_table_msg = generate_routing_table_msg(l)
            message = pickle.dumps(routing_table_msg) # Pickle Message to be sent
            self.controller_socket.sendto(message, self.switch_addresses[switch_id])
            
        
        print(f'Sent routing table {routing_table_msg}')
        
    def handle_register_request(self, switch_id, recvd_addr):
        # Handle Register Request from a switch that was previosly offline
        print(f"Controller received Register Request from Switch {switch_id}")
        
        hostname, port = recvd_addr
        port = int(port)
        self.switch_addresses[switch_id] = (hostname, port)
        self.switch_statuses[switch_id] = time.time()
        self.live_switches.add(switch_id)
        self.switch_addresses = dict(sorted(self.switch_addresses.items()))
        register_request_received(switch_id)

        # Perform recomputation of paths and send Route Update message
        self.recompute_paths_and_send_update()
    
    def wait_for_switches_to_come_online(self):
        self.d,self.total_num_switches = open_file(self.config_file)
        # Wait for all switches to come online
        print('Controller is waiting for all switches to come online')
        num_of_switches_online = 0
        while num_of_switches_online < self.total_num_switches:
            recvd_data, switch_addr = self.controller_socket.recvfrom(1024)
            recvd_msg =  pickle.loads(recvd_data)
            request_type = recvd_msg[0]
            switch_id = recvd_msg[1]
            
            if request_type == 'Register_Request':
                print(f'Received {request_type} from switch {switch_id}')
                hostname, port = switch_addr
                port = int(port)
                self.switch_addresses[switch_id] = (hostname, port)
                self.switch_statuses[switch_id] = time.time()
                self.live_switches.add(switch_id)
                register_request_received(switch_id)
                num_of_switches_online += 1
        print('All Switches are Online')
        self.switch_addresses = dict(sorted(self.switch_addresses.items())) # sort switch_addresses
        
        # Send Register Response
        response_msg = generate_response_msg(self.switch_addresses)
        send_message(self.controller_socket, self.switch_addresses, response_msg)
        
        # Initial Routing Table
        self.create_graph()
        self.create_routing_table()
        # LOG - Routing Table
        routing_table_update(self.routing_table)
        
        # Send Routing Table
        routing_table_msg = generate_routing_table_msg(self.routing_table)
        send_message(self.controller_socket, self.switch_addresses, routing_table_msg)
        print('Sent routing table')
        print('---Exit-- wait_for_switches_to_come_online()')

        
    def handle_topology_update(self,switch_id,neighbor_state,neighbor_status): 
        print(f"Controller received Topology Update from Switch {switch_id}")
            
        print(f'Neighbor State = {neighbor_state}')
        print(f'Neighbor Status = {neighbor_status}')
        # First update switch statuses from neighbor statuses
        for key,value in neighbor_state.items():
            if value == True:
                self.switch_statuses[key] = time.time()
                continue
            elif value == False:
                self.live_switches.discard(key)
                topology_update_switch_dead(switch_id)
                self.recompute_paths_and_send_update()
            
        self.switch_statuses[switch_id] = time.time()
        
        # Check if timeout
        for switch,value in self.switch_statuses.items():
            if value  < time.time() - self.TIMEOUT:
                print('Switch {switch_id} is dead')
                self.live_switches.discard(switch)
                topology_update_switch_dead(switch)

                # Perform recomputation of paths and send Route Update message
                self.recompute_paths_and_send_update()
                
    
    def handle_recv_message(self, recvd_data, recvd_addr):
        recvd_msg =  pickle.loads(recvd_data)
        request_type = recvd_msg[0]
        
        print(f'Recevied a {request_type} from {recvd_addr}')
        if request_type == 'Topology_Update':
            '''If a controller receives a Topology Update message from a switch 
            that indicates a neighbor is no longer reachable, then the controller 
            updates its topology to reflect that link as unusable.'''
            switch_id = int(recvd_msg[1])
            neighbor_state = recvd_msg[2] # dictionary with key as switch_id and Boolean as values
            neighbor_status = recvd_msg[3]
            self.handle_topology_update(switch_id,neighbor_state,neighbor_status)
        
        elif request_type == 'Register_Request':
            '''If a controller receives a Register Request message from a switch 
            it previously considered as ‘dead’, then it responds appropriately 
            and marks it as ‘alive’.'''
            switch_id = int(recvd_msg[1])
            self.handle_register_request(switch_id, recvd_addr)
        
    def receive_messages(self):
        while True:
            print('Waiting for Message..')
            recvd_data, addr = self.controller_socket.recvfrom(1024)
            self.handle_recv_message(recvd_data, addr)
    
    def run(self):
        # Start threads for Keep Alive, Topology Update, and Timeout Handling
        threading.Thread(target=self.receive_messages, args=(), daemon=False).start()
        

def main():
    #Check for number of arguments and exit if host/port not provided
    num_args = len(sys.argv)
    if num_args < 3:
        print ("Usage: python controller.py <port> <config file>\n")
        sys.exit(1)
    
    #Write your code below or elsewhere in this file
    controller_port = int(sys.argv[1])
    config_file = sys.argv[2]
    
    controller = Controller(controller_port,config_file)
    controller.wait_for_switches_to_come_online()
    
    controller.run()
    

if __name__ == "__main__":
    main()
    
    # config_file = 'Config/graph_6.txt'
    # controller = Controller(1088,config_file)
    
    # controller.d,controller.total_num_switches = open_file(controller.config_file)
    # for i in range(6):
    #     addr = ('localhost',2222+i)
    #     controller.handle_register_request(i, addr)
    
    # controller.create_graph()
    # print(controller.graph)
    # controller.live_switches.discard(0)
    # controller.create_routing_table()
    # print(controller.routing_table)
    # # distances, paths, next_hop = dijkstra(controller.graph, controller.live_switches, 0)

    
