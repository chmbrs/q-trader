from plotly import tools
import plotly.offline as py
import plotly.graph_objs as go
import plotly.figure_factory as ff

from agent.agent import Agent
from functions import *
import sys

import pandas as pd

from datetime import datetime

if len(sys.argv) != 4:
    print("Usage: python3 train.py [stock] [window] [episodes]")
    exit()

stock_name, window_size, episode_count = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])

# stock_name='bit1'
df = pd.read_csv("./data/" + stock_name + ".csv")

data = df.loc[:, ~df.columns.isin(['Action', 'Timestamp'])]

#(window_size, columns)
state_shape = (window_size, len(data.columns))

agent = Agent(state_shape=state_shape)

data_lenght = len(data) - 1

batch_size = 32

last_higher_profit = 0

for episode in range(episode_count + 1):
    df['Action'] = ''

    print("Episode " + str(episode) + "/" + str(episode_count))

    state = getState2(data, 0, window_size)

    total_profit = 0
    agent.inventory = []

    previous_action = 0
    buy_action_count = 0
    no_action_count = 0

    for step in range(data_lenght):
        if step % 10:
            print(f'{step}/{data_lenght}')

        action = agent.act(state)

        if action == 1 and previous_action == 1:
            buy_action_count += 1
        if action == 0 and previous_action == 0:
            no_action_count += 1

        # no-action
        next_state = getState2(data, step + 1, window_size)
        reward = 0

        # Update the Action column with no-action
        df.iloc[step, -1] = 0

        if action == 1: # buy
            agent.inventory.append(data.iloc[step, 3]) #3 is the close column
            print("Buy: " + formatPrice(data.iloc[step, 3]))

            # Update the Action column with buy-action
            df.iloc[step, -1] = 1

        elif action == 2 and len(agent.inventory) > 0: # sell
            bought_price = agent.inventory.pop(0)

            reward = max(data.iloc[step, 3] - bought_price, 0)

            # if reward == 0:
            # 	reward = -1
            # 	print(f'0 gain penalty')

            total_profit += data.iloc[step, 3] - bought_price
            print("Sell: " + formatPrice(data.iloc[step, 3]) +
                " | Profit: " + formatPrice(data.iloc[step, 3] - bought_price))

            # Update the Action column with sell-action
            df.iloc[step, -1] = -1


        # # Check if there are 20 consecutives buys
        # if buy_action_count >= 20:
        # 	reward = -500
        # 	print(f'excess buys penalty')
        # 	buy_action_count = 0
        # # Check if there are 50 consecutives no-actions
        # if no_action_count >= 50:
        # 	reward = -500
        # 	no_action_count = 0
        # 	print(f'no-action penalty')

        done = True if step == data_lenght - 1 else False

        # if not step <= window_size:
        #     agent.memory.append((state, action, reward, next_state, done))

        state = next_state
        previous_action = action

        if done:
            print("--------------------------------")
            print("Total Profit: " + formatPrice(total_profit))
            print("--------------------------------")

        agent.expReplay2(state, action, reward, next_state, done)

        # if len(agent.memory) > batch_size + window_size:
        # 	agent.expReplay(batch_size)


    if episode % 5 == 0:
        #df.to_csv(f'df_ep{episode}.csv')
        price = go.Scatter(x=df.index,
                            y=df['Close'])
        action = go.Bar(x=df.index,
                        y=df['Action'])

        fig = tools.make_subplots(rows=2)

        fig.append_trace(price, 1, 1)
        fig.append_trace(action, 2, 1)

        profit = str(total_profit).split('.')

        py.plot(fig)#, filename=f'model_ep{episode}_profit{profit[0]}.html')

    # if e % 10 == 0:
    if total_profit > last_higher_profit:
        last_higher_profit = total_profit
        profit = str(total_profit).split('.')
        agent.model.save(f"models/model_ep{episode}_profit{profit[0]}")
