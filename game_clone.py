import os
import random

import numpy as np
import pygame
from pygame.locals import *


pygame.mixer.init()
pygame.init()

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

-
#game variables
ground_scroll = 0
scroll_speed = 4
flying = False
game_over = False
pipe_gap = 140
pipe_frequency = 1500  # milliseconds
last_pipe = pygame.time.get_ticks() - pipe_frequency
score = 0
passed_pipe = False

#define sound
flap_sound = pygame.mixer.Sound('sound/wing.wav')
hit_sound = pygame.mixer.Sound('sound/hit.wav')
score_sound = pygame.mixer.Sound('sound/point.wav')
die_sound = pygame.mixer.Sound('sound/die.wav')
bg_sound = pygame.mixer.Sound('sound/music.wav')

#background and images
bg = pygame.image.load('img/bg.png')
bg_ground = pygame.image.load('img/ground.png')
button_img = pygame.image.load('img/restart.png')

#timing ai die
ai_death_time = 0
ai_delay_duration = 1000   
ai_waiting_for_reset = False

#induce time bg music
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
        if flying == True:
            self.velocity += 0.5
            if self.velocity > 10:
                self.velocity = 10

        if self.rect.bottom < 556:
            self.rect.y += int(self.velocity)

        if game_over == False:
            #jump
            if pygame.mouse.get_pressed()[0] == 1 and self.clicked is False:
                self.velocity = -8
                self.rect.y += self.velocity
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
        gap = random.randint(-15,15)
        pipe_gap_rand = pipe_gap + gap
        if position == 1:
            self.image = pygame.transform.flip(self.image, False, True)
            self.rect.bottomleft = [x, y - int(pipe_gap_rand / 2)]

        if position == -1:
            self.rect.topleft = [x, y + int(pipe_gap_rand / 2)]

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

#reset game
def reset_game():
    global last_pipe, passed_pipe
    pipe_group.empty()
    flappy.rect.x = 200
    flappy.rect.y = int(s_height / 2)
    flappy.velocity = 0
    flappy.clicked = True
    last_pipe = pygame.time.get_ticks() - pipe_frequency
    passed_pipe = False
    return 0

#groups and sprites
bird_group = pygame.sprite.Group()
pipe_group = pygame.sprite.Group()

flappy = Bird(200, int(s_height / 2))
bird_group.add(flappy)

button_restart = Button(s_width // 2 - 70 , s_height // 2 - 20, button_img)

run = True
while run:

    clock.tick(fps)
    #draw background and ground
    screen.blit(bg, (0, 0))
    screen.blit(bg_ground, (0, 556))


    #draw and update bird
    bird_group.draw(screen)
    bird_group.update()

    #draw pipe
    pipe_group.draw(screen)

    #draw ground and scroll
    screen.blit(bg_ground, (ground_scroll, 556)) 

    #check bird hit ground
    if flappy.rect.bottom > 550:
        game_over = True
        flying = False
    
    #check bird hit pipe
    if pygame.sprite.groupcollide(bird_group, pipe_group, False, False) or flappy.rect.top < 0:
        game_over = True
    
    #check sore
    if len(pipe_group) > 0:
        if bird_group.sprites()[0].rect.left > pipe_group.sprites()[0].rect.left and bird_group.sprites()[0].rect.right < pipe_group.sprites()[0].rect.right and passed_pipe == False: 
            passed_pipe = True
        
        if passed_pipe == True:
            if bird_group.sprites()[0].rect.left > pipe_group.sprites()[0].rect.right:
                score +=1
                passed_pipe = False
    
    #draw score
    draw_text("Score: " + str(score), font2, white, int(s_width/2) - 80, 20)

    #check state
    if game_over == False and flying == True:
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
    
        #update pipe
        pipe_group.update()

    #check game over and reset
    if game_over == True:
        if button_restart.draw() == True:
            game_over = False
            score = reset_game()



    # new line
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

        if event.type == pygame.MOUSEBUTTONDOWN and flying == False and game_over == False:
            flying = True

    pygame.display.update()
pygame.quit()

  