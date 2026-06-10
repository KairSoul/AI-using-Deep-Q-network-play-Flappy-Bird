import os
import random
import csv

import numpy as np
import pygame
from pygame.locals import *

from env import FlappyEnv
from agent import DQNAgent


pygame.init()

# Initialize CSV log file for Game/Train Mode
log_file = "train_log.csv"
if not os.path.exists(log_file):
    with open(log_file, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Write the headers for the columns
        writer.writerow(['Episode', 'Score', 'Steps', 'Epsilon'])

#seting fps
clock = pygame.time.Clock()
fps = 60

#size of the window
s_width = 888
s_height = 666

screen = pygame.display.set_mode((s_width, s_height))
pygame.display.set_caption('Flappy Bird')

#define fonts
font1 = pygame.font.SysFont('Arial', 50)
font2 = pygame.font.SysFont("Impact", 50)

#define colors
white = (255, 255, 255)
black = (0, 0, 0)


#game variables
ground_scroll = 0
scroll_speed = 4
flying = False
game_over = False
pipe_gap = 150
pipe_frequency = 1500  # milliseconds
last_pipe = pygame.time.get_ticks() - pipe_frequency
score = 0
passed_pipe = False
play_mode = None
game_state = "menu"

#background and images
bg = pygame.image.load('img/bg.png')
bg_ground = pygame.image.load('img/ground.png')
reset_img = pygame.image.load('img/restart.png')
manual_img = pygame.image.load('img/Manual_Play.png')
ai_img = pygame.image.load('img/AI_Play.png')
menu_img = pygame.image.load("img/Menu.png")

#define sound
flap_sound = pygame.mixer.Sound('sound/wing.wav')
hit_sound = pygame.mixer.Sound('sound/hit.wav')
score_sound = pygame.mixer.Sound('sound/point.wav')
die_sound = pygame.mixer.Sound('sound/die.wav')

pygame.mixer.music.load('sound/music.wav')
pygame.mixer.music.set_volume(0.4)

#text convert image
def draw_text(text, font, text_color, x, y):
    img = font.render(text, True, text_color)
    screen.blit(img, (x, y))


class Bird(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load('img/bird_mid.png')
        self.images = [
            pygame.image.load('img/bird_mid.png'),
            pygame.image.load('img/bird_up.png'),
            pygame.image.load('img/bird_down.png'),
        ]

        self.index = 0
        self.couter = 0
        self.image = self.images[self.index]
        self.rect = self.image.get_rect()
        self.rect.center = [x, y]
        self.velocity = 0
        self.clicked = False

    #animations
    def update(self):
        #gravity
        if flying == True and play_mode == "manual":
            self.velocity += 0.5
            if self.velocity > 8:
                self.velocity = 8

        if self.rect.bottom < 556 and play_mode == "manual":
            self.rect.y += int(self.velocity)

        if game_over == False and play_mode == "manual":
            #jump
            if play_mode == "manual":
                if pygame.mouse.get_pressed()[0] == 1 and self.clicked is False:
                    self.velocity = -8
                    self.rect.y += self.velocity
                    flap_sound.play()
                    self.clicked = True

                if pygame.mouse.get_pressed()[0] == 0 :
                    self.clicked = False

            #animation
            self.couter += 1
            flap_cooldown = 5
            if self.couter > flap_cooldown:
                self.couter = 0
                self.index += 1
                if self.index >= len(self.images):
                    self.index = 0
                self.image = self.images[self.index]
            #rotate the bird
            self.image = pygame.transform.rotate(self.images[self.index], -self.velocity * 2)
        else:
            self.image = pygame.transform.rotate(self.images[self.index], -90)


class Pipe(pygame.sprite.Sprite):
    def __init__(self, x, y, position):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load('img/pipe_green.png')
        self.rect = self.image.get_rect()
        self.rect.topleft = [x,y]
        self.passed = False

        #position 1 is backward, -1 is forward
        if position == 1:
            self.image = pygame.transform.flip(self.image, False, True)
            self.rect.bottomleft = [x, y - int(pipe_gap / 2)]

        if position == -1:
            self.rect.topleft = [x, y + int(pipe_gap / 2)]

    def update(self):
        self.rect.x -= scroll_speed
        if self.rect.right < 0:
            self.kill()


class Button:
    def __init__(self, x, y, image):
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)

    def draw(self):
        action = False
        pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(pos):
            if pygame.mouse.get_pressed()[0] == 1:
                action = True
        screen.blit(self.image, (self.rect.x, self.rect.y))
        return action

#manual reset
def reset_manual():
    global last_pipe, passed_pipe, flying, game_over
    pipe_group.empty()
    flappy.rect.x = 200
    flappy.rect.y = int(s_height / 2)
    flappy.velocity = 0
    flappy.clicked = True
    flying = False  
    game_over = False
    last_pipe = pygame.time.get_ticks() - pipe_frequency
    passed_pipe = False
    return 0

#ai reset
def reset_ai():
    global last_pipe, passed_pipe, flying, game_over, step_count, total_reward_current_inf
    pipe_group.empty()
    flappy.rect.x = 200
    flappy.rect.y = int(s_height / 2)
    flappy.velocity = 0
    flappy.clicked = False
    flying = True   
    game_over = False
    
    #Reset AI
    flappy_env.reset()
    #new pipe after 300milis
    flappy_env.last_pipe = pygame.time.get_ticks() - pipe_frequency + 300 
    
    #new HUD
    step_count = 0
    total_reward_current_inf = 0
    return 0

#groups and sprites
bird_group = pygame.sprite.Group()
pipe_group = pygame.sprite.Group()

flappy = Bird(200, int(s_height / 2))
bird_group.add(flappy)

#AI
flappy_env = FlappyEnv(flappy, pipe_group, s_width, s_height)
# Khởi tạo Agent với kích thước state là 6
agent = DQNAgent(state_size=6, action_size=2)

episode_count = 0
total_reward_current_inf = 0
step_count = 0
max_score = 0

if os.path.exists("flappy_dqn.pt"):
    agent.load("flappy_dqn.pt")

#state button
button_restart = Button(s_width // 2 - 70 , s_height // 2 - 20, reset_img)
button_manual = Button(s_width // 2 - 70 , s_height // 2 - 100, manual_img)
button_ai = Button(s_width // 2 - 70 , s_height // 2 + 20, ai_img)
menu_button = Button(10, 10, menu_img)

# Create a temporary buffer list in RAM to store AI match data
ai_lifecycle_buffer = []

run = True
while run:

    clock.tick(fps)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

        if event.type == pygame.MOUSEBUTTONDOWN and flying == False and game_over == False:
            if play_mode == "manual":
                flying = True
                flap_sound.play()

    #menu
    if game_state == "menu":

        screen.blit(bg, (0, 0))
        screen.blit(bg_ground, (0, 556))
        draw_text("FLAPPY BIRD",font1,white,s_width // 2 - 140,12)

        #menu sound
        if pygame.mixer.music.get_busy() == False:
            pygame.mixer.music.play(-1)

        #manual state
        if button_manual.draw() == True:

            play_mode = "manual"
            game_state = "game"
            flying = False
            game_over = False
            score = reset_manual()
            pygame.mixer.music.stop()

        #ai state
        if button_ai.draw() == True:

            play_mode = "ai"
            game_state = "game"
            flying = True
            game_over = False
            score = reset_ai()
            flappy_env.last_pipe = pygame.time.get_ticks() - pipe_frequency + 300
            step_count = 0
            total_reward_current_inf = 0
            pygame.mixer.music.stop()

        #event
        pygame.display.update()
        continue


    #draw background and ground
    screen.blit(bg, (0, 0))
    screen.blit(bg_ground, (0, 556))

    if play_mode == "manual" and game_over == False:
        #draw and update bird
        bird_group.draw(screen)
        bird_group.update()
        #update pipe
        pipe_group.update()
        #draw pipe
        pipe_group.draw(screen)

    elif play_mode == "ai":

        if game_state == "game" and game_over == False:
            current_state = flappy_env.get_state()
            action = agent.act(current_state)

            if action == 1:
                flap_sound.play()
            
            time_now = pygame.time.get_ticks()
            if time_now - flappy_env.last_pipe > flappy_env.pipe_frequency:
                pipe_height = random.randint(-115, 115)
                bottom_pipe = Pipe(s_width, int(s_height/2) + pipe_height, -1)
                top_pipe = Pipe(s_width, int(s_height/2) + pipe_height, 1)
                pipe_group.add(bottom_pipe)
                pipe_group.add(top_pipe)
                flappy_env.last_pipe = time_now

            next_state, reward, done = flappy_env.step(action)
            agent.remember(current_state, action, reward, next_state, done)
            agent.replay()
            
            if flappy_env.score > score: 
                score = flappy_env.score
                total_reward_current_inf += reward 
                score_sound.play()      
            
            step_count += 1
            
            flappy.couter += 1
            if flappy.couter > 5:
                flappy.couter = 0
                flappy.index = (flappy.index + 1) % len(flappy.images)
            flappy.image = pygame.transform.rotate(flappy.images[flappy.index], -flappy.velocity * 2)
            
            #Ép vẽ cả ỐNG và CHIM hiển thị đồng thời khi AI chơi
            pipe_group.draw(screen)
            bird_group.draw(screen)
            
            if done:
                game_over = True
    
    #draw ground and scroll
    screen.blit(bg_ground, (ground_scroll, 556))

    #menu button
    if menu_button.draw() == True:

        game_state = "menu"
        play_mode = None
        flying = False
        game_over = False
        score = reset_manual()
        pygame.mixer.music.play(-1)
    
    if play_mode == "manual" and game_over == False:
        #check bird hit ground
        if flappy.rect.bottom > 550:
            game_over = True
            flying = False
            die_sound.play()
        
        #check bird hit pipe
        if pygame.sprite.groupcollide(bird_group, pipe_group, False, False) or flappy.rect.top < 0:
            game_over = True

            #hit pipe and ground sound
            hit_sound.play()
            die_sound.play()
        
        #check sore
        if len(pipe_group) > 0:
            if bird_group.sprites()[0].rect.left > pipe_group.sprites()[0].rect.left and bird_group.sprites()[0].rect.right < pipe_group.sprites()[0].rect.right and passed_pipe == False: 
                passed_pipe = True
            
            if passed_pipe == True:
                if bird_group.sprites()[0].rect.left > pipe_group.sprites()[0].rect.right:
                    score +=1
                    score_sound.play()
                    passed_pipe = False
    
    #draw score
    draw_text("Score: " + str(score), font2, white, int(s_width/2) - 80, 20)

    if play_mode == "ai" and game_state == "game":
        font_stats = pygame.font.SysFont("Arial", 20)
        stats_bg = pygame.Surface((260, 160))
        stats_bg.set_alpha(150)  
        stats_bg.fill((0, 0, 0))
        screen.blit(stats_bg, (10, 70))
        draw_text(f"DQN TRAINING MONITOR", font_stats, (0, 255, 0), 20, 75)
        draw_text(f"Game: {episode_count + 1}", font_stats, white, 20, 100)
        draw_text(f"Max Score: {max_score}", font_stats, (255, 215, 0), 20, 125)
        draw_text(f"Steps: {step_count}", font_stats, white, 20, 150)
        draw_text(f"Epsilon: {agent.epsilon:.3f}", font_stats, white, 20, 175)
        draw_text(f"Total Reward: {total_reward_current_inf:.1f}", font_stats, white, 20, 200)

    #check state
    if game_over == False and flying == True:
        if play_mode == "manual":
            #new pipe
            time_now = pygame.time.get_ticks()
            if time_now - last_pipe > pipe_frequency:
                pipe_height = random.randint(-115,115)
                bottom_pipe = Pipe(s_width, int(s_height/2) + pipe_height, -1)
                top_pipe = Pipe(s_width, int(s_height/2) + pipe_height, 1)
                pipe_group.add(bottom_pipe)
                pipe_group.add(top_pipe)
                last_pipe = time_now

        #check and scroll ground
        ground_scroll -= scroll_speed
        if abs(ground_scroll) > 35:
            ground_scroll = 0
        
    #check game over and reset
    if game_over == True:
        if play_mode == "manual":
            if button_restart.draw() == True:
                game_over = False
                score = reset_manual()
            
        elif play_mode == "ai":

            hit_sound.play()
            die_sound.play()

            episode_count += 1
            if score > max_score:
                max_score = score
            print(f"--- TRẬN {episode_count} | Score: {score} (Max: {max_score}) | Epsilon: {agent.epsilon:.4f}")

            #add data csv
            with open(log_file, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([episode_count, score, step_count, agent.epsilon])

            if episode_count % 10 == 0:
                agent.save("flappy_dqn.pt")

            #reset
            score = reset_ai()  

    pygame.display.update()
pygame.quit()

  