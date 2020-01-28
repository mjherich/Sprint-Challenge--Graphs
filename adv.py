from room import Room
from player import Player
from world import World
from util import Queue, Stack, Graph

import multiprocessing as mp
import os
import pdb
from datetime import datetime
import time
import random
from ast import literal_eval

# Load world
world = World()


# You may uncomment the smaller graphs for development and testing purposes.
# map_file = "maps/test_line.txt"
# map_file = "maps/test_cross.txt"
# map_file = "maps/test_loop.txt"
# map_file = "maps/test_loop_fork.txt"
map_file = "maps/main_maze.txt"

# Loads the map into a dictionary
room_graph=literal_eval(open(map_file, "r").read())
world.load_graph(room_graph)

# Print an ASCII map
world.print_rooms()

player = Player(world.starting_room)

# === USEFUL METHODS === #
# player.current_room.id                <- returns the room id
# player.current_room.get_exits()       <- returns the availble exits from the current room (['n', 's', ...])
# player.travel('n')                    <- Input a direction and move to that room
# room.get_room_in_direction('n')       <- Input a direction and get the room id that's connected or None

# Shape of the graph (based on test_cross map)
# {
#   0: {'n': 1, 's': 5, 'w': 7, 'e': 3},    <- Room 0 has 4 connected rooms
#   1: {'n': 2, 's': 0},                    <- Room 1 has 2 connected rooms
#   2: {'s': 1},                            <- Room 2 has 1 connected room
#   ...
#   8: {'e': 7}                             <- Room 8 has 1 connected room
# }

# FIRST: Explore all rooms and populate the graph
graph = Graph()
# Add starting room
starting_room = world.starting_room
# graph.add_vertex(starting_room.id)
stack = Stack()
stack.push(starting_room)
visited = set()
# Continue until we have seen all rooms and the stack is empty
while stack.size() > 0:
    room = stack.pop() # returns a <Room> class instance, not a room id
    room_id = room.id
    if room_id not in graph.vertices:
        graph.add_vertex(room_id)
    # Get connected rooms
    connected_rooms = room.get_exits()  # returns an array of directions
    for direction in connected_rooms:
        connected_room = room.get_room_in_direction(direction) # returns a <Room> class instance
        connected_room_id = connected_room.id
        if connected_room_id not in graph.vertices:
            graph.add_vertex(connected_room_id)
        graph.add_edge(room_id, connected_room_id, direction)
        # After making the connection in the graph add it to the stack
        if connected_room_id not in visited:
            stack.push(connected_room)
    visited.add(room_id)


# NEXT: Use the graph to find the most efficient route that visits all rooms at least once
def find_next_path(room_id, visited, g=graph):
    """
    Takes in a room id and a set of visited room ids

    returns a set of moves that the player can take to get to the nearest unvisited space.
    """
    rooms_with_moves = {} # [ ["LIST OF ROOM IDS"], ["LIST OF MOVES"] ]
    rooms_with_moves[room_id] = [[room_id], []]
    q = Queue()
    q.enqueue([[room_id], []])
    while q.size() > 0:
        rooms, moves = q.dequeue()
        last_room_id = rooms[-1]
        neighbors = g.get_neighbors(last_room_id)  # returns {'n': 2, 's': 0}
        neighbors_keys = list(neighbors.keys())
        random.shuffle(neighbors_keys)
        if len(neighbors_keys) == 1 and neighbors[neighbors_keys[0]] not in visited:
            # We are at the CLOSEST, UNEXPLORED DEAD END as soon as this condition is True
            shortest_path_to_unexplored_dead_end = list(moves) + [neighbors_keys[0]]
            return shortest_path_to_unexplored_dead_end
        else:
            # Keep going through the graph until we hit a dead end
            for direction in neighbors_keys:
                next_room = neighbors[direction]
                new_rooms = list(rooms) + [next_room]
                new_moves = list(moves) + [direction]
                if next_room not in rooms_with_moves:
                    q.enqueue([new_rooms, new_moves])
                    rooms_with_moves[next_room] = [new_rooms, new_moves]
                if next_room not in visited:
                    return new_moves

# Load persisted pathes
with open("shortest_traversal_path.txt", 'r') as f:
    shortest_traversal_str = f.read()
    if shortest_traversal_str != "":
        shortest_traversal_moves = shortest_traversal_str.split(",")
        shortest_traversal = len(shortest_traversal_moves)
    else:
        shortest_traversal = len(graph.vertices) * 50
print(f"Current best path: {shortest_traversal} moves")
target = int(input("Enter a target traversal length... "))
# Start
def brute_force(shared):
    # Initialize with persistence length
    shared_shortest_path_len = shortest_traversal
    # Begin brute force search loop
    while shared_shortest_path_len > target:
        # Reset path search variables
        player = Player(world.starting_room)
        traversal_path = []
        visited = set()
        visited.add(starting_room.id)
        current_room_id = starting_room.id
        while len(visited) < len(graph.vertices):
            # Find the nearest dead end
            moves = find_next_path(current_room_id, visited)
            # Traverse the returned list of moves
            for direction in moves:
                player.travel(direction)
                traversal_path.append(direction)
                visited.add(player.current_room.id)
            current_room_id = player.current_room.id
        traversal_length = len(traversal_path)

        if traversal_length < shared_shortest_path_len:
            shared.set_length(traversal_path)
        # Get most up to date shared_shortest_path_len
        shared_shortest_path_len = shared.value()

# Create session logging file
log_file_name = f"./logging/session-{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.txt"
with open(log_file_name, "w+") as f:
    f.write(f"Running brute force search on {mp.cpu_count()} cores with a target of {target}...\n")
print(f"Running brute force search on {mp.cpu_count()} cores...\n")

# === Multiprocessing ===
class Shortest_Path_Len(object):
    def __init__(self, initval=shortest_traversal):
        self.val = mp.Value('i', initval)
        self.lock = mp.Lock()

    def set_length(self, new_path):
        """
        Attempts to update the shared shortest path length.

        Input: new_path as list of moves

        Calculate the length from input and update the persistence file if it's less than the current val.
        """
        with self.lock:
            new_length = len(new_path)
            # Check if new path is still shorter than what is set
            if new_length < self.val.value:
                new_path_str = ",".join(new_path)
                # Updates the shared length val
                self.val.value = new_length
                message = f"New shortest path of {new_length} moves found on process {os.getpid()}"
                # Print message to console
                print(message)
                # Write message to log file
                with open(log_file_name, "a") as f:
                    f.write(f"{message}\n")
                # Write to persistence
                with open("shortest_traversal_path.txt", 'w') as f:
                    f.write(f"{new_path_str}")

    def value(self):
        with self.lock:
            return self.val.value

# Initialize shared shortest_path string to make sure we're always working on a better path
shared_shortest_path_len = Shortest_Path_Len()
# Create processes
processes = [mp.Process(target=brute_force, args=(shared_shortest_path_len,)) for _ in range(mp.cpu_count())]

for p in processes:
    p.start()

for p in processes:
    p.join(None)

# Get traversal from persistence
with open("shortest_traversal_path.txt", 'r') as f:
    shortest_traversal_str = f.read()
    shortest_traversal_moves = shortest_traversal_str.split(",")
    shortest_traversal = len(shortest_traversal_moves)
traversal_path = shortest_traversal_moves

# TRAVERSAL TEST
visited_rooms = set()
player.current_room = world.starting_room
visited_rooms.add(player.current_room)

for move in traversal_path:
    player.travel(move)
    visited_rooms.add(player.current_room)

if len(visited_rooms) == len(room_graph):
    print(f"TESTS PASSED: {len(traversal_path)} moves, {len(visited_rooms)} rooms visited")
else:
    print("TESTS FAILED: INCOMPLETE TRAVERSAL")
    print(f"{len(room_graph) - len(visited_rooms)} unvisited rooms")



#######
# UNCOMMENT TO WALK AROUND
#######
# player.current_room.print_room_description(player)
# while True:
#     cmds = input("-> ").lower().split(" ")
#     if cmds[0] in ["n", "s", "e", "w"]:
#         player.travel(cmds[0], True)
#     elif cmds[0] == "q":
#         break
#     else:
#         print("I did not understand that command.")
