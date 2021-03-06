import keras
from keras.models import Sequential
from keras.models import load_model
from keras.layers import Dense
from keras.optimizers import Adam

from keras.callbacks import TensorBoard

import tensorflow as tf
gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=0.48)
sess = tf.Session(config=tf.ConfigProto(gpu_options=gpu_options))

import numpy as np
import random
from collections import deque

import time

class Agent:
    def __init__(self, state_shape, is_eval=False, model_name=""):

        self.name = f'BitcoinDQNN-{int(time.time())}'

        self.state_shape = state_shape # normalized previous days
        self.action_size = 3 # sit, buy, sell
        self.memory = deque(maxlen=1000)
        self.inventory = []
        self.model_name = model_name
        self.is_eval = is_eval

        self.gamma = 0.95
        self.epsilon = 1.0
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.learning_rate = 0.001

        self.model = load_model("models/" + model_name) if is_eval else self._model()

    def _model(self):

        model = Sequential()

        model.add(Dense(units=64, input_shape=self.state_shape, activation="relu"))
        model.add(Dense(units=32, activation="relu"))
        model.add(Dense(units=8, activation="relu"))
        model.add(Dense(self.action_size, activation="linear"))

        model.compile(loss="mse", optimizer=Adam(lr=self.learning_rate),
                        metrics=['accuracy'])

        model.tensorboard = TensorBoard(log_dir=f'logs/{self.name}')

        return model

    def act(self, state):
        if not self.is_eval and random.random() <= self.epsilon:
            return random.randrange(self.action_size)

            options = self.model.predict(state)

            return np.argmax(options[0])


    def expReplay(self, batch_size):

        mini_batch = []
        memory_lenght = len(self.memory)

        for i in range(memory_lenght - batch_size + 1, memory_lenght):
        	mini_batch += self.memory[i]

        for state, action, reward, next_state, done in self.memory[batch_size]:
            target = reward
            if not done:
                target = reward + self.gamma * np.amax(self.model.predict(next_state)[0])

            target_future = self.model.predict(state)
            target_future[0][action] = target
            self.model.fit(state, target_future, epochs=1, verbose=0)

        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def expReplay2(self, state, action, reward, next_state, done):

        target = reward
        if not done:
            target = reward + self.gamma * np.amax(self.model.predict(next_state)[0])

        target_future = self.model.predict(state)
        target_future[0][action] = target
        self.model.fit(state, target_future, epochs=1, verbose=1, callbacks=[self.model.tensorboard])

        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
