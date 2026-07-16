import random as rnd
import numpy as np

class Sorter:

    action = -1 ### 0: Place container to port 1, 1: Place container to port 2, 2: Place container to the temporary port, 3: Place container to the toxic port, 4+: Move between ports
    reward = 0

    cargo = [] ### The containers that are to be sorted
    ports = [[],[],[],[]] ### Port 1, Port 2, Temporary Port and Toxic Port

    port_capacity = 0 ### Number of containers that can be placed to a single port
    temp_port_capacity = 0 ### Number of containers that the temporary port can hold
    toxic_port_capacity = 0 ### Number of containers that the toxic port can hold
    number_of_containers = 0 ### Number of containers in the cargo at the start

    container_sizes = {} ### 0: S, 1: M, 2: L
    toxic_containers = set() ### Containers carrying toxic materials
    size_names = ["S", "M", "L"]
    toxic_chance = 0.25

    ### Hyperparameters
    learning_rate = 0.2
    discount_factor = 0.95
    epsilon = 0.95

    num_of_states = 0 ### 
    total_port_count = 4
    num_of_actions = total_port_count + total_port_count * (total_port_count - 1)
    q_table = {}
    ports_swapped = False ### Whether port 1 and port 2 were mirrored while calculating the current state

    def reset_q_table(number_of_containers):
        Sorter.number_of_containers = number_of_containers
        Sorter.port_capacity = (Sorter.number_of_containers + 1)//2 ### 3:2, 4:2, 5:3, 6:3, 7:4, 8:4
        Sorter.temp_port_capacity = (Sorter.port_capacity + 1)//2 ### 3:1, 4:1, 5:2, 6:2, 7:2, 8:2
        Sorter.toxic_port_capacity = (Sorter.number_of_containers + 1)//2 ### 3:2, 4:2, 5:3, 6:3, 7:4, 8:4

        incoming_states = 1 + Sorter.number_of_containers * 2 ### Empty cargo (1) + incoming container ID for non-toxic/toxic (n*2)
        exit_location_states = 4 ### Next-to-exit container: in cargo, on top, under one, under two or more
        main_port_states = 192 ### can_place (2) x relation (3) x top_urgent (2) x top_toxic (2) x fullness (4) x violation (2)
        temp_port_states = 18 ### can_place (2) x relation (3) x load (3)
        toxic_port_states = 96 ### can_place (2) x relation (3) x top_urgent (2) x fullness (4) x violation (2)

        Sorter.num_of_states = incoming_states * exit_location_states * main_port_states * main_port_states * temp_port_states * toxic_port_states

        Sorter.q_table = {}

    def generate_scenario(): ### Generate a guaranteed possible scenario
        containers = list(range(Sorter.number_of_containers))

        for container in containers:
            if rnd.uniform(0, 1) < Sorter.toxic_chance:
                Sorter.toxic_containers.add(container)

        while len(Sorter.toxic_containers) > Sorter.toxic_port_capacity:
            Sorter.toxic_containers.remove(rnd.choice(list(Sorter.toxic_containers)))

        if Sorter.toxic_chance > 0 and len(Sorter.toxic_containers) == 0:
            Sorter.toxic_containers.add(rnd.choice(containers))

        regular_containers = [container for container in containers if not Sorter.is_toxic(container)]
        toxic_containers = [container for container in containers if Sorter.is_toxic(container)]

        final_ports = [[],[],[],[]]

        ### Build valid final ports
        regular_containers.sort(reverse = True)
        for container in regular_containers:
            possible_ports = []

            for port_id in [0,1]:
                if len(final_ports[port_id]) < Sorter.port_capacity:
                    possible_ports.append(port_id)

            port_id = rnd.choice(possible_ports)
            final_ports[port_id].append(container)

        toxic_containers.sort(reverse = True)
        for container in toxic_containers:
            final_ports[3].append(container)

        for port_id in [0,1,3]:
            sizes = []

            for _ in range(len(final_ports[port_id])):
                sizes.append(rnd.randrange(3))

            sizes.sort(reverse = True)

            for i in range(len(final_ports[port_id])):
                container = final_ports[port_id][i]
                Sorter.container_sizes[container] = sizes[i]

        ### Start from the solved position
        Sorter.ports = [
            final_ports[0][:],
            final_ports[1][:],
            [],
            final_ports[3][:]
        ]

        reverse_move_count = rnd.randrange(10, 50)
        reverse_moves_done = 0
        cargo_moves_done = 0
        attempt_count = 0
        last_move = None

        while attempt_count < reverse_move_count * 50:
            occupied_ports = []

            for port_id in range(Sorter.total_port_count):
                if len(Sorter.ports[port_id]) > 0:
                    occupied_ports.append(port_id)

            if len(occupied_ports) == 0:
                break

            port_moves = []
            cargo_moves = []

            ### Legal port-to-port scrambling moves
            if reverse_moves_done < reverse_move_count:
                for source_id in range(Sorter.total_port_count):
                    if len(Sorter.ports[source_id]) == 0:
                        continue

                    container = Sorter.ports[source_id][-1]

                    for target_id in range(Sorter.total_port_count):
                        if source_id == target_id:
                            continue

                        if Sorter.can_place_to_port(container, target_id):
                            port_moves.append((source_id, target_id))

            ### Reverse cargo moves: move top container of a port back to cargo
            for source_id in range(Sorter.total_port_count):
                if len(Sorter.ports[source_id]) > 0:
                    cargo_moves.append(source_id)

            if len(port_moves) > 0 and rnd.uniform(0, 1) < 0.75:
                source_id, target_id = rnd.choice(port_moves)

                container = Sorter.ports[source_id].pop(-1)
                Sorter.ports[target_id].append(container)

                last_move = (source_id, target_id)
                reverse_moves_done += 1

            else:
                source_id = rnd.choice(cargo_moves)

                container = Sorter.ports[source_id].pop(-1)
                Sorter.cargo.insert(0, container)

                last_move = None
                cargo_moves_done += 1

            attempt_count += 1

        ### If anything is still left in ports, move it back to cargo safely
        while True:
            possible_ports = []

            for port_id in range(Sorter.total_port_count):
                if len(Sorter.ports[port_id]) > 0:
                    possible_ports.append(port_id)

            if len(possible_ports) == 0:
                break

            port_id = rnd.choice(possible_ports)
            container = Sorter.ports[port_id].pop(-1)
            Sorter.cargo.insert(0, container)
            cargo_moves_done += 1

        Sorter.ports = [[],[],[],[]]

    def start_scenario():
        Sorter.cargo = []
        Sorter.ports = [[],[],[],[]]
        Sorter.reward = 0
        Sorter.container_sizes = {}
        Sorter.toxic_containers = set()

        Sorter.generate_scenario()

        # for n in range(Sorter.number_of_containers): ### Place all the containers to the cargo
        #     Sorter.cargo.append(n)
        #     Sorter.container_sizes[n] = rnd.randrange(3)
        #     if rnd.uniform(0, 1) < Sorter.toxic_chance:
        #         Sorter.toxic_containers.add(n)
        
        # rnd.shuffle(Sorter.cargo) ### Randomize the cargo

    def container_size(container): ### The size value of a container
        return Sorter.container_sizes[container]

    def is_toxic(container): ### Whether a container has toxic material
        return container in Sorter.toxic_containers

    def port_limit(n): ### The capacity limit of a port
        return [Sorter.port_capacity, Sorter.port_capacity, Sorter.temp_port_capacity, Sorter.toxic_port_capacity][n]

    def is_sorted(n): ### If a port is arranged correctly (lower priority above higher priority)
        for i in range(len(Sorter.ports[n]) - 1):
            if Sorter.ports[n][i] < Sorter.ports[n][i + 1]:
                return False
        return True

    def is_size_sorted(n): ### If a port is arranged correctly by size (same or smaller above larger)
        for i in range(len(Sorter.ports[n]) - 1):
            if Sorter.container_size(Sorter.ports[n][i]) < Sorter.container_size(Sorter.ports[n][i + 1]):
                return False
        return True

    def is_toxic_sorted(n): ### If toxic containers are kept away from regular ports
        for container in Sorter.ports[n]:
            if n == 3 and not Sorter.is_toxic(container):
                return False
            if n != 3 and n != 2 and Sorter.is_toxic(container):
                return False
        return True

    def can_stack_on_port(container, port_id): ### If this container can be stacked on this port by size
        if len(Sorter.ports[port_id]) == 0:
            return True

        top_box = Sorter.ports[port_id][-1]
        return Sorter.container_size(container) <= Sorter.container_size(top_box)

    def can_place_to_port(container, port_id): ### If this container can legally be placed on this port
        if len(Sorter.ports[port_id]) >= Sorter.port_limit(port_id):
            return False
        elif not Sorter.can_stack_on_port(container, port_id):
            return False
        elif not Sorter.is_toxic(container) and port_id == 3: ### Don't allow normal containers into toxic port
            return False
        return True

    def all_containers():
        containers = list(Sorter.cargo)

        for port_id in range(Sorter.total_port_count):
            containers += Sorter.ports[port_id]

        return containers

    def incoming_state():
        if len(Sorter.cargo) == 0:
            return 0 ### Cargo empty

        container = Sorter.cargo[0]
        toxic_flag = int(Sorter.is_toxic(container))

        return 1 + toxic_flag * Sorter.number_of_containers + container

    def top_location():
        containers = Sorter.all_containers()

        if len(containers) == 0:
            return 0

        next_exit = min(containers)

        if next_exit in Sorter.cargo:
            return 0 ### Still in the cargo queue

        for port_id in range(Sorter.total_port_count):
            if next_exit in Sorter.ports[port_id]:
                depth = len(Sorter.ports[port_id]) - 1 - Sorter.ports[port_id].index(next_exit)

                if depth == 0:
                    return 1 ### On top of a port
                elif depth == 1:
                    return 2 ### Buried under one container
                return 3 ### Buried under two or more

        return 0

    def placement_relation(port_id): ### What placing the incoming container here would do to the exit order
        if len(Sorter.cargo) == 0 or len(Sorter.ports[port_id]) == 0:
            return 0 ### Nothing to compare against
        elif Sorter.cargo[0] < Sorter.ports[port_id][-1]:
            return 1 ### Safe, the incoming container leaves before the current top
        return 2 ### Buries a container that must leave earlier

    def top_is_next_exit(port_id): ### If the top container of this port must leave before everything else
        if len(Sorter.ports[port_id]) == 0:
            return 0

        return int(Sorter.ports[port_id][-1] == min(Sorter.all_containers()))

    def fullness_state(port_id):
        height = len(Sorter.ports[port_id])
        limit = Sorter.port_limit(port_id)

        if height == 0:
            return 0 ### Empty
        elif height == limit:
            return 3 ### Full
        elif height == limit - 1:
            return 2 ### One slot left
        return 1 ### Room to spare

    def can_place_cargo(port_id):
        return int(len(Sorter.cargo) > 0 and Sorter.can_place_to_port(Sorter.cargo[0], port_id))

    def main_port_state(port_id):
        can_place = Sorter.can_place_cargo(port_id)
        relation = Sorter.placement_relation(port_id)
        top_urgent = Sorter.top_is_next_exit(port_id)
        top_toxic = int(len(Sorter.ports[port_id]) > 0 and Sorter.is_toxic(Sorter.ports[port_id][-1]))
        fullness = Sorter.fullness_state(port_id)
        violation = int(not Sorter.is_sorted(port_id)) ### Wrong order

        return ((((can_place * 3 + relation) * 2 + top_urgent) * 2 + top_toxic) * 4 + fullness) * 2 + violation

    def toxic_port_state():
        can_place = Sorter.can_place_cargo(3)
        relation = Sorter.placement_relation(3)
        top_urgent = Sorter.top_is_next_exit(3)
        fullness = Sorter.fullness_state(3)
        violation = int(not Sorter.is_sorted(3)) ### Wrong order

        return (((can_place * 3 + relation) * 2 + top_urgent) * 4 + fullness) * 2 + violation

    def temp_port_state():
        can_place = Sorter.can_place_cargo(2)
        relation = Sorter.placement_relation(2)

        height = len(Sorter.ports[2])
        if height == 0:
            load = 0 ### Empty
        elif height == 1:
            load = 1 ### One container
        else:
            load = 2 ### Two or more containers

        return (can_place * 3 + relation) * 3 + load

    def get_current_state():
        incoming = Sorter.incoming_state()
        top_location = Sorter.top_location()

        port_1_state = Sorter.main_port_state(0)
        port_2_state = Sorter.main_port_state(1)

        Sorter.ports_swapped = port_2_state < port_1_state
        if Sorter.ports_swapped:
            port_1_state, port_2_state = port_2_state, port_1_state

        temp_state = Sorter.temp_port_state()
        toxic_state = Sorter.toxic_port_state()

        state = incoming
        state = state * 4 + top_location
        state = state * 192 + port_1_state
        state = state * 192 + port_2_state
        state = state * 18 + temp_state
        state = state * 96 + toxic_state

        return state

    def get_q_values(state): ### Get the Q-values for a state
        if state not in Sorter.q_table:
            Sorter.q_table[state] = np.zeros(Sorter.num_of_actions)
        return Sorter.q_table[state]
    
    def update_q_table(old_state, old_value, next_value, reward):
        Sorter.get_q_values(old_state)[Sorter.action] = (1 - Sorter.learning_rate) * old_value + Sorter.learning_rate * (reward + Sorter.discount_factor * next_value)

    def step(learn = False):
        old_state = Sorter.get_current_state()
        q_values = Sorter.get_q_values(old_state)
        
        if rnd.uniform(0, 1) < Sorter.epsilon:  ### Explore
            Sorter.action = rnd.randrange(Sorter.num_of_actions)
        else:                                   ### Exploit
            Sorter.action = np.argmax(q_values)

        reward = Sorter.act() ### Reward from the Sorter's action

        reward += Sorter.container_check() ### Reward from the current state of the ports
        Sorter.reward += reward

        terminated = (reward >= 200) ### Terminate if the sorting is complete

        if learn:
            if terminated:
                next_value = 0
            else:
                next_value = np.max(Sorter.get_q_values(Sorter.get_current_state()))

            Sorter.update_q_table(
                old_state=old_state,
                old_value=q_values[Sorter.action],
                next_value=next_value,
                reward=reward
            )

        return terminated
    
    def translate_action(action): ### Map an action chosen on a mirrored state back to the physical ports
        if not Sorter.ports_swapped:
            return action

        if action == 0: ### Place to port 1 becomes place to port 2
            return 1
        elif action == 1: ### Place to port 2 becomes place to port 1
            return 0
        elif action < 4: ### Temporary and toxic ports are unaffected
            return action

        move = action - 4
        source = move // (Sorter.total_port_count - 1)
        targets = [0,1,2,3]
        targets.remove(source)
        target = targets[move % (Sorter.total_port_count - 1)]

        swap = {0: 1, 1: 0, 2: 2, 3: 3}
        source = swap[source]
        target = swap[target]

        targets = [0,1,2,3]
        targets.remove(source)

        return 4 + source * (Sorter.total_port_count - 1) + targets.index(target)

    def act():
        action = Sorter.translate_action(Sorter.action) ### Convert the mirrored action into a physical one
        
        if action < 2: ### Move from cargo to ports
            return Sorter.place_to_port(action)
        elif action == 2: ### Move from cargo to temporary port
            return Sorter.place_to_temp_port()
        elif action == 3: ### Move from cargo to toxic port
            return Sorter.place_to_toxic_port()
        else: ### Move between ports
            action -= 4
            source = action // (Sorter.total_port_count - 1)
            ports = [0,1,2,3]
            ports.remove(source)
            target = ports[action % (Sorter.total_port_count - 1)]
            return Sorter.move_from_port(source, target)
    
    def place_to_port(port_id):
        if len(Sorter.cargo) > 0 and Sorter.can_place_to_port(Sorter.cargo[0], port_id):
            container = Sorter.cargo.pop(0)
            Sorter.ports[port_id].append(container) ### Takes the first element of cargo and places it into the port
            return -1
        else:
            return -10 ### Illegal move
    
    def place_to_temp_port():
        if len(Sorter.cargo) > 0 and Sorter.can_place_to_port(Sorter.cargo[0], 2):
            container = Sorter.cargo.pop(0)
            Sorter.ports[2].append(container) ### Takes the first element of cargo and places it into the port
            return -1
        else:
            return -10 ### Illegal move

    def place_to_toxic_port():
        if len(Sorter.cargo) > 0 and Sorter.can_place_to_port(Sorter.cargo[0], 3):
            container = Sorter.cargo.pop(0)
            Sorter.ports[3].append(container) ### Takes the first element of cargo and places it into the port
            return -1
        else:
            return -10 ### Illegal move
    
    def move_from_port(source_id, target_id):
        if len(Sorter.ports[source_id]) > 0 and Sorter.can_place_to_port(Sorter.ports[source_id][-1], target_id): 
            container = Sorter.ports[source_id].pop(-1)
            Sorter.ports[target_id].append(container) ### Takes the last element of a port and moves it to another port

            return -1
            # if target_id == 2:
            #     return -2 ### Discourage the temporary port
            # else:
            #     return -1
        else:
            return -10 ### Illegal move
        
    def container_check():
        reward = 0

        ### Penalize keeping cargo in the queue (encourage placing)
        reward -= len(Sorter.cargo)

        ### Penalize anything sitting in the temp port
        # reward -= len(Sorter.ports[2])

        ### If all the cargo are placed correctly
        if len(Sorter.cargo) == 0 and len(Sorter.ports[2]) == 0:
            if False not in [Sorter.is_sorted(n) and Sorter.is_size_sorted(n) and Sorter.is_toxic_sorted(n) for n in range(4)]:
                reward += 1000
        return reward

    def render_port(): ### Render the current state of the ports
        def show_box(box):
            size = Sorter.size_names[Sorter.container_size(box)]
            toxic = "T" if Sorter.is_toxic(box) else " "
            return f"[{box:02}-{size}{toxic}]"

        def show_slot(port, index):
            if index < len(port):
                return show_box(port[index])
            return "[     ]"

        print("\n" * 2)
        print("=" * 60)

        print("Remaining cargo:")
        if len(Sorter.cargo) > 0:
            print(" ".join(show_box(c) for c in Sorter.cargo))
        else:
            print("[empty]")

        print("-" * 60)
        print(f"{'Level':<8}{'Port 1':<12}{'Port 2':<12}{'Temp':<12}{'Toxic':<12}")
        print("-" * 60)

        max_capacity = max(Sorter.port_capacity, Sorter.temp_port_capacity, Sorter.toxic_port_capacity)

        for level in range(max_capacity - 1, -1, -1):
            port_1 = show_slot(Sorter.ports[0], level) if level < Sorter.port_capacity else ""
            port_2 = show_slot(Sorter.ports[1], level) if level < Sorter.port_capacity else ""
            temp = show_slot(Sorter.ports[2], level) if level < Sorter.temp_port_capacity else ""
            toxic = show_slot(Sorter.ports[3], level) if level < Sorter.toxic_port_capacity else ""

            label = ""
            if level == max_capacity - 1:
                label = "TOP"
            elif level == 0:
                label = "BOTTOM"

            print(f"{label:<8}{port_1:<12}{port_2:<12}{temp:<12}{toxic:<12}")

        print("=" * 60)
