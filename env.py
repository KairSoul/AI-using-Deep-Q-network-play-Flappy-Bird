# env.py
import pygame
import random
import numpy as np

class FlappyEnv:
    def __init__(self, flappy, pipe_group, s_width, s_height):
        self.flappy = flappy
        self.pipe_group = pipe_group
        self.s_width = s_width
        self.s_height = s_height

        self.pipe_gap = 150
        self.scroll_speed = 4
        self.pipe_frequency = 1500

        self.last_pipe = pygame.time.get_ticks()
        self.score = 0
        self.game_over = False

    def reset(self):
        self.pipe_group.empty()
        self.flappy.rect.x = 200
        self.flappy.rect.y = self.s_height // 2
        self.flappy.velocity = 0

        self.score = 0
        self.game_over = False
        self.last_pipe = pygame.time.get_ticks()

        return self.get_state()

    def get_state(self):
        target_pipes = []
        for pipe in self.pipe_group.sprites():
            if pipe.rect.right > self.flappy.rect.left:
                target_pipes.append(pipe)

        if len(target_pipes) < 2:
            pipe_x = self.s_width
            pipe_y = self.s_height // 2
        else:
            pipe_bottom = target_pipes[0] if target_pipes[0].rect.y > target_pipes[1].rect.y else target_pipes[1]
            pipe_x = pipe_bottom.rect.x
            pipe_y = pipe_bottom.rect.y - 75  # Tâm khoảng trống giữa 2 ống

        # TÍNH TOÁN SAI LỆCH GÓC: Hiệu số độ cao giữa chim và tâm ống đích
        # Giá trị âm nghĩa là chim đang bay cao hơn ống, dương là thấp hơn ống
        target_y_diff = (pipe_y - self.flappy.rect.y) / self.s_height

        # NÂNG CẤP VECTOR TRẠNG THÁI LÊN 6 CHIỀU (Thêm thông tin góc lệch trục Y trực tiếp)
        return [
            float(self.flappy.rect.y / self.s_height),
            float(self.flappy.velocity / 10.0),
            float(pipe_x / self.s_width),
            float(pipe_y / self.s_height),
            float((pipe_x - self.flappy.rect.x) / self.s_width),
            float(target_y_diff) # Trạng thái thứ 6 giúp nhận biết cao độ random
        ]

    def step(self, action):
        reward = 0.1  # Thưởng sống sót cơ bản

        # jump
        if action == 1:
            self.flappy.velocity = -6 

        # gravity
        self.flappy.velocity += 0.5
        if self.flappy.velocity > 10:
            self.flappy.velocity = 10

        self.flappy.rect.y += int(self.flappy.velocity)

        # Di chuyển ống
        for pipe in self.pipe_group:
            pipe.rect.x -= self.scroll_speed

        for pipe in self.pipe_group.copy():
            if pipe.rect.right < 0:
                pipe.kill()

        # REWARD SHAPING NÂNG CAO - ÉP CHIM LẦN THEO ĐƯỜNG ỐNG RANDOM
        target_pipes = []
        for pipe in self.pipe_group.sprites():
            if pipe.rect.right > self.flappy.rect.left:
                target_pipes.append(pipe)

        if len(target_pipes) >= 2:
            pipe_bottom = target_pipes[0] if target_pipes[0].rect.y > target_pipes[1].rect.y else target_pipes[1]
            pipe_center_y = pipe_bottom.rect.y - 75
            
            # Tính khoảng cách chuẩn hóa từ chim tới tâm ống (từ 0.0 đến 1.0)
            distance_to_center = abs(self.flappy.rect.y - pipe_center_y) / self.s_height
            
            # KỸ THUẬT PHẠT LŨY TIẾN MŨ 2: Càng bay xa tâm ống random, điểm thưởng càng sụt giảm nghiêm trọng
            # Giúp bẻ gãy hành vi thích bay cao cố định của mạng Neural
            reward += (1.0 - (distance_to_center ** 2)) * 1.0  

        # Kiểm tra va chạm sàn / trần nhà -> Chết ăn phạt rất nặng
        if self.flappy.rect.bottom > 550 or self.flappy.rect.top < 0:
            return self.get_state(), -100.0, True

        # Kiểm tra va chạm ống
        for pipe in self.pipe_group:
            if self.flappy.rect.colliderect(pipe.rect):
                return self.get_state(), -100.0, True

        # Thưởng lớn bứt phá khi luồn thành công qua khe hở
        for pipe in self.pipe_group:
            if pipe.rect.right < self.flappy.rect.left and not getattr(pipe, "passed", False):
                for p in self.pipe_group:
                    if p.rect.x == pipe.rect.x:
                        p.passed = True
                reward += 30.0  # Tăng lên 30 để AI thèm muốn việc vượt ống
                self.score += 1
                break

        return self.get_state(), reward, False