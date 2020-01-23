from room import Room
from player import Player
from world import World
from util import Queue, Stack, Graph

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
# Continue until we have seen all rooms and the stack is empty
counter = 0
visited = set()
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
        print(f"Pushing to the stack... {counter}")
        counter += 1
        if connected_room_id not in visited:
            stack.push(connected_room)
    visited.add(room_id)

print(f"Graph neighbors of room 2: {graph.get_neighbors(2)}")
# NEXT: Use the graph to find the most efficient route that visits all rooms at least once
# traversal_path = ['n', 'n']
traversal_path = []




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
