import random as rnd
import numpy as np

class Sorter:

    action = -1 ### 0: Place container to port 1, 1: Place container to port 2, 2: Place container to the temporary port, 3: Move from port 1 to port 2, 4: Move from port 1 to temporary port, 5: Move from port 2 to port 1, 6: Move from port 2 to temporary port, 7: Move from temporary port to port 1, 8: Move from temporary port to port 2
    reward = 0

    cargo = []
    ports = [[],[],[]]

    port_capacity = 0
    temp_port_capacity = 0
    number_of_containers = 0

    # Hyperparameters
    learning_rate = 0.2
    discount_factor = 0.95
    epsilon = 0.95

    num_of_states = 0
    num_of_actions = 9
    q_table = np.zeros([num_of_states, num_of_actions])

    def reset_q_table(number_of_containers):
        Sorter.number_of_containers = number_of_containers
        Sorter.port_capacity = (number_of_containers + 1) // 2
        Sorter.temp_port_capacity = Sorter.port_capacity // 2

        incoming_states = Sorter.number_of_containers + 1
        main_port_states = 1 + Sorter.number_of_containers * Sorter.port_capacity * 2
        temp_port_states = 1 + Sorter.number_of_containers * Sorter.temp_port_capacity * 2

        Sorter.num_of_states = incoming_states * main_port_states * main_port_states * temp_port_states

        Sorter.q_table = np.zeros([Sorter.num_of_states, Sorter.num_of_actions])

    def start_scenario():
        Sorter.cargo = []
        Sorter.ports = [[],[],[]]
        Sorter.reward = 0

        for n in range(Sorter.number_of_containers):
            Sorter.cargo.append(n)
        
        rnd.shuffle(Sorter.cargo)

    def port_is_sorted(port):
        for i in range(len(port) - 1):
            if port[i] < port[i + 1]:
                return False
        return True

    def port_state(port):
        if len(port) == 0:
            return 0

        height = len(port)
        top_box = port[-1]
        sorted_flag = int(Sorter.port_is_sorted(port))

        return 1 + (
            (height - 1) * Sorter.number_of_containers * 2
            + top_box * 2
            + sorted_flag
        )

    def get_current_state():
        incoming = Sorter.cargo[0] if len(Sorter.cargo) > 0 else Sorter.number_of_containers

        main_port_states = 1 + Sorter.number_of_containers * Sorter.port_capacity * 2
        temp_port_states = 1 + Sorter.number_of_containers * Sorter.temp_port_capacity * 2

        port_1_state = Sorter.port_state(Sorter.ports[0])
        port_2_state = Sorter.port_state(Sorter.ports[1])
        temp_state = Sorter.port_state(Sorter.ports[2])

        state = incoming
        state = state * main_port_states + port_1_state
        state = state * main_port_states + port_2_state
        state = state * temp_port_states + temp_state

        return state
    
    def update_q_table(old_state, old_value, next_value, reward):
        Sorter.q_table[old_state, Sorter.action] = (1 - Sorter.learning_rate) * old_value + Sorter.learning_rate * (reward + Sorter.discount_factor * next_value)

    def step(learn = False):
        old_state = Sorter.get_current_state()

        if rnd.uniform(0, 1) < Sorter.epsilon:
            Sorter.action = rnd.randrange(Sorter.num_of_actions)
        else:
            Sorter.action = np.argmax(Sorter.q_table[old_state])

        reward = Sorter.act()
        reward += Sorter.container_check()
        Sorter.reward += reward

        terminated = (reward >= 200)

        if learn:
            if terminated:
                next_value = 0
            else:
                next_value = np.max(Sorter.q_table[Sorter.get_current_state()])

            Sorter.update_q_table(
                old_state=old_state,
                old_value=Sorter.q_table[old_state,Sorter.action],
                next_value=next_value,
                reward=reward
            )

        return terminated

    def act():
        action = Sorter.action
        
        if action < 2: ### Move from cargo to ports
            return Sorter.place_to_port(action)
        elif action == 2: ### Move from cargo to temporary port
            return Sorter.place_to_temp_port()
        
        else: ### Move between ports
            source = ((action-3)//2)
            ports = [0,1,2]
            ports.remove(source)
            target = ports[1-(action%2)] ### Honestly hardcoding would've been preferrable to this monstrosity, jesus
            return Sorter.move_from_port(source, target)
    
    def place_to_port(port_id):
        if len(Sorter.cargo) > 0 and len(Sorter.ports[port_id]) < Sorter.port_capacity:
            container = Sorter.cargo.pop(0)
            Sorter.ports[port_id].append(container) ### Takes the first element of cargo and places it into the port
            return -1
        else:
            return -10 ### Illegal move
    
    def place_to_temp_port():
        if len(Sorter.cargo) > 0 and len(Sorter.ports[2]) < Sorter.temp_port_capacity:
            container = Sorter.cargo.pop(0)
            Sorter.ports[2].append(container) ### Takes the first element of cargo and places it into the port
            return -1
        else:
            return -10 ### Illegal move
    
    def move_from_port(source_id, target_id):
        if len(Sorter.ports[source_id]) > 0 and (
            (target_id == 2 and len(Sorter.ports[target_id]) < Sorter.temp_port_capacity) ### If moving to the temporary port
            or 
            (target_id < 2 and len(Sorter.ports[target_id]) < Sorter.port_capacity) ### If moving to the other two ports
            ): 
            
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

        # Penalize keeping cargo in the queue (encourage placing)
        reward -= len(Sorter.cargo)

        # Penalize anything sitting in the temp port
        # reward -= len(Sorter.ports[2])

        # Only evaluate terminal condition when all cargo is placed
        if len(Sorter.cargo) == 0 and len(Sorter.ports[2]) == 0:
            if Sorter.is_sorted():
                reward += 1000  # Win!
            # No partial pair bonuses — don't reward intermediate arrangements

        return reward

    def is_sorted():
        for port in Sorter.ports[:2]:
            for i in range(len(port) - 1):
                if port[i] < port[i + 1]:  # bottom should be HIGHER number, top should be LOWER
                    return False
        return True

    def render_port():
        def show_box(box):
            return f"[{box:02}]"

        def show_slot(port, index):
            if index < len(port):
                return show_box(port[index])
            return "[  ]"

        print("\n" * 2)
        print("=" * 36)

        print("Remaining cargo:")
        if len(Sorter.cargo) > 0:
            print(" ".join(show_box(c) for c in Sorter.cargo))
        else:
            print("[empty]")

        print("-" * 36)
        print(f"{'Level':<8}{'Port 1':<10}{'Port 2':<10}{'Temp':<10}")
        print("-" * 36)

        for level in range(Sorter.port_capacity - 1, -1, -1):
            port_1 = show_slot(Sorter.ports[0], level)
            port_2 = show_slot(Sorter.ports[1], level)
            temp = show_slot(Sorter.ports[2], level) if level < Sorter.temp_port_capacity else ""

            label = ""
            if level == Sorter.port_capacity - 1:
                label = "TOP"
            elif level == 0:
                label = "BOTTOM"

            print(f"{label:<8}{port_1:<10}{port_2:<10}{temp:<10}")

        print("=" * 36)