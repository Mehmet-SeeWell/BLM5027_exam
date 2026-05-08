import random as rnd
import numpy as np
import matplotlib.pyplot as plt
from container_sorter import Sorter

max_step_count = 500

def moving_average(data, window=500): ### Used to calculate the graph post-training
    data = np.convolve(np.asarray(data, dtype=float), np.ones(window) / window, mode="valid")
    return data

def train_sorter():
    epoch_count = 60000
    per = 2500 ### Number of episodes per report
    rewards = []

    Sorter.reset_q_table(10)
    print(f"Q-Table set - Container Amount: {Sorter.number_of_containers}, Port Capacity: {Sorter.port_capacity}, Temporary Port Capacity: {Sorter.temp_port_capacity}, Number of total states: {Sorter.num_of_states}")

    ### Set the map
    print("Training Started!")
    any_terminations = False
    for n in range(epoch_count):
        terminated = False
        Sorter.start_scenario()

        for _ in range(max_step_count):
            terminated = Sorter.step(learn = True)

            if terminated: ### Terminated
                if not any_terminations:
                    any_terminations = True
                break
        else:
            ... ### Truncated

        rewards.append(Sorter.reward)
        Sorter.epsilon = max(0.01, Sorter.epsilon * 0.99995) ### Epsilon decay

        if n==0 or (n+1) % per == 0: ### Report the current progress
            print(f"Epoch {n+1} - Average Reward: {np.mean(rewards[-per:]):.3f}, Epsilon value: {Sorter.epsilon:.3f}, Any Terminations?: {any_terminations}")
            if any_terminations:
                any_terminations = False

    print("Training Finished!")

    ### Display the graph ###
    avg_rewards = moving_average(rewards, per)

    plt.figure(figsize=(12, 6))
    plt.plot(rewards, label="Episode Reward", alpha=0.4)
    plt.plot(
        np.arange(per - 1, len(rewards)),
        avg_rewards,
        label=f"Moving Average (per {per})",
        linewidth=2
    )

    plt.title("Training Reward Over Time")
    plt.xlabel("Episode")
    plt.ylabel("Reward")
    plt.legend()
    plt.grid(True)
    plt.show()

def test_sorter():
    Sorter.start_scenario()
    Sorter.epsilon = 0 ### Using only exploited knowledge
    print("Starting Testing")
    Sorter.render_port()
    input() ### The user presses enter to advance
    for _ in range(max_step_count):
        terminated = Sorter.step()
        Sorter.render_port()
        input()
        if terminated:
            print("Testing successful!")
            break
    else:
        print("Testing failed")
        input()

train_sorter()
test_sorter()
