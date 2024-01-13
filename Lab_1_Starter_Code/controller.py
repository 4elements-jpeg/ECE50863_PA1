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

def create_graph(d):
    '''This function creates a graph from d that is passed into the function 
    dijkstra_algorithm().'''
    graph = []
    for self_id in d:
        l = []
        for cost in d[self_id].values():
            l.append(cost)
        graph.append(l)
    return graph

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

def dijkstra_algorithm(graph, source):
    '''Implement Dijkstra's algorithm'''

    # Get total number of nodes in the graph
    num_nodes = len(graph)

    # Initialize distance and visited arrays
    distances = [9999] * num_nodes
    visited = []
    
    next_hop = [-1] * num_nodes
    next_hop[source] = 0

    # Set distance at starting node to 0 and add to visited list 
    distances[source] = 0
    visited.append(source)

    # Loop through all nodes to find shortest path to each node
    for i in range(num_nodes):

        # Find minimum distance node that has not been visited yet
        current_node = min_distance(distances, visited)

        # Add current_node to list of visited nodes
        visited.append(current_node)
        

        # Loop through all neighboring nodes of current_node 
        for j in range(num_nodes):

            # Check if there is an edge from current_node to neighbor
            if graph[current_node][j] != 0:

                # Calculate the distance from start_node to neighbor, 
                # passing through current_node
                new_distance = distances[current_node] + graph[current_node][j]

                # Update the distance if it is less than previous recorded value 
                if new_distance < distances[j]:
                    print("Updating next hop")
                    distances[j] = new_distance
                    next_hop[j] = current_node
                    print(current_node)
                    
            else:
                print("ELSE ", i)
                next_hop[i] = i
                
    
    # Return the list of the shortest distances to all nodes
    return distances,next_hop

def dijkstra(graph, start_node):
    num_nodes = len(graph)

    distances = {node: float('inf') for node in range(num_nodes)}
    paths = {node: [] for node in range(num_nodes)}
    next_hop = {node: -1 for node in range(num_nodes)}
    visited = set()
    next_hop[start_node] = 0

    distances[start_node] = 0

    priority_queue = [(0, start_node)]

    while priority_queue:
        current_distance, current_node = heapq.heappop(priority_queue)

        if current_node in visited:
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

def create_routing_table(d,graph,num_switches):
    '''create_routing_table returns a list of the format of a nested list.
    For the parameter "routing_table", it should be a list of lists in the form 
    of [[...], [...], ...]. Within each list in the outermost list, 
    the first element is <Switch ID>. The second is <Dest ID>, 
    and the third is <Next Hop>, and the fourth is <Shortest distance>'''
    routing_table = []
    
    for i in range(num_switches):
        
        distances, paths, next_hop = dijkstra(graph, i)
        
        for key,value in distances.items():
            
            l = [i] # first element of the list is Switch_ID
            l.append(key) # second element of the list is Destination_ID
            
            # third element of list is the Next Hop
            if next_hop[key] == i:
                l.append(key)
            else:
                l.append(next_hop[key])
            
            l.append(distances[key]) # fourth element of the list is Shortest Distance
            routing_table.append(l)
    
    return routing_table

def generate_response_msg(connected_switches,num_switches):
    '''connected_switches is a dictionary where the Key=switch_id and 
    value=switch_addr where switch_addr is a tuple (addr,port_number) and
    creates a response message to be sent.'''
    
    msg = f'{num_switches} \n'
    count = 0
    
    for switch_id,switch_addr in connected_switches.items():
        addr, port_number = switch_addr
        msg += f'{switch_id} {addr} {port_number}'
        if count < num_switches:
            msg += '\n'
        count += 1
    
    return msg.encode('utf-8')

def send_message(socket, connected_switches, message):
    for switch_id,switch_addr in connected_switches.items():
        socket.sendto(message, switch_addr)
        register_response_sent(switch_id)
        print(f'Sent message to switch#{switch_id} @ {switch_addr}')

def main():
    #Check for number of arguments and exit if host/port not provided
    num_args = len(sys.argv)
    if num_args < 3:
        print ("Usage: python controller.py <port> <config file>\n")
        sys.exit(1)
    
    #Write your code below or elsewhere in this file
    controller_port = int(sys.argv[1])
    config_file = sys.argv[2]
    
    # Import and load config file
    d,num_switches = open_file(config_file)
    routing_table = create_routing_table(d)
    
    # Create controller socket for UDP
    controller_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    controller_host = socket.gethostname()
    controller_addr = (controller_host,controller_port)
    print(f'Controller Address is {controller_addr}')
    controller_socket.bind((controller_host,controller_port))
    
    # Key=switch_id | Value=switch_addr
    connected_switches = {}
    
    # wait for switches to come online
    print(f"Controller is listening on port {controller_port}")
    num_of_switches_online = 0
    while num_of_switches_online <= num_switches:
        print("Waiting for client...")
        data,switch_addr = controller_socket.recvfrom(1024)
        decoded_data = data.decode('utf-8')
        switch_id,request = decoded_data.split(' ')
        
        connected_switches[switch_id] = switch_addr
        register_request_received(switch_id)
        
        print("Recieved message from client")
        print(f"Switch address is {switch_addr}")
        print(f"Switch data is {switch_id} {request}")
        print()
        num_of_switches_online += 1
    
    # Send Register Response
    response_msg = generate_response_msg(connected_switches,num_switches)
    send_message(controller_socket, connected_switches, response_msg)



if __name__ == "__main__":
    # main()
    
    config_file = 'Config/graph_6.txt'

    d,num_switches = open_file(config_file)
    graph = create_graph(d)
    
    distances, paths, next_hop = dijkstra(graph, 0)

    routing_table = create_routing_table(d,graph,num_switches)
                