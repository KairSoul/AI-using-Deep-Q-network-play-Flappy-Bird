# train.py
import random
import pygame
import numpy as np
import torch

from agent import DQNAgent
from env import FlappyEnv

# Khởi tạo Mock/Kịch bản ảo tương thích Form gốc dựa theo Pygame
pygame.init()
s_width, s_height = 888, 666
pipe_gap = 150

# Định nghĩa các Mockup Object gọn nhẹ để nhúng vào môi trường độc lập khi Train
class MockBird:
    def __init__(self):
        self.rect = pygame.Rect(200, s_height // 2, 34, 24) # SỬA: Đưa X từ 400 về lại 200 theo đúng yêu cầu
        self.velocity = 0

class MockPipe(pygame.sprite.Sprite):
    def __init__(self, x, y, position):
        super().__init__()
        self.rect = pygame.Rect(x, y, 52, 320)
        self.passed = False
        if position == 1:
            self.rect.bottomleft = [x, y - int(pipe_gap/2)]
        else:
            self.rect.topleft = [x, y - int(pipe_gap/2)]
    def update(self):
        self.rect.x -= 4

flappy_mock = MockBird()
pipe_group_mock = pygame.sprite.Group()

# Khởi tạo môi trường huấn luyện
env = FlappyEnv(flappy_mock, pipe_group_mock, s_width, s_height)
state_size = 6 # (y_chim, v_chim, x_ong, y_ong, khoang_cach_x)

agent = DQNAgent(state_size=state_size, action_size=2)
EPISODES = 10000
max_score = 0

# Tạo một clock ảo để tính thời gian sinh ống trong môi trường không UI
clock = pygame.time.Clock()

for episode in range(EPISODES):
    state = env.reset()
    state = np.reshape(state, [1, agent.state_size])

    total_reward = 0
    step = 0

    while True:
        # Tự động đồng bộ thời gian giả lập tạo ống khi training loop chạy không UI
        time_now = pygame.time.get_ticks()
        if time_now - env.last_pipe > env.pipe_frequency:
            gap = random.randint(-115, 115)
            bottom = MockPipe(s_width, s_height // 2 + gap, -1)
            top = MockPipe(s_width, s_height // 2 + gap, 1)
            pipe_group_mock.add(bottom)
            pipe_group_mock.add(top)
            env.last_pipe = time_now

        # ---------------- ACTION ----------------
        action = agent.act(state)

        # ---------------- STEP ENV ----------------
        next_state, reward, done = env.step(action)
        next_state = np.reshape(next_state, [1, agent.state_size])

        # ---------------- STORE MEMORY ----------------
        agent.remember(state, action, reward, next_state, done)

        state = next_state
        total_reward += reward
        step += 1

        # ---------------- TRAIN ----------------
        agent.replay()

        # THÊM: Chặn cứng trần nhà ảo để chim không bị bay lọt lên trời vô tận trong lúc chạy ngầm
        if flappy_mock.rect.top < 0:
            flappy_mock.rect.top = 0
            flappy_mock.velocity = 0

        if done:
            print(f"Episode: {episode} | Score: {env.score} | Steps: {step} | Epsilon: {agent.epsilon:.4f}")
            break

    # ---------------- SAVE MODEL OVER RECORD ----------------
    # Lưu mô hình khi phá kỷ lục ngay trong lúc train ngầm, hoặc định kỳ mỗi 50 trận nếu đạt điểm khá
    if env.score > max_score and env.score > 0:
        max_score = env.score
        agent.save("flappy_dqn.pt")
        print(f"--> [TRAIN RECORD] Saved new model with Max Score: {max_score}")
    elif episode % 50 == 0 and episode > 0:
        agent.save("flappy_dqn.pt")

print("Training finished")