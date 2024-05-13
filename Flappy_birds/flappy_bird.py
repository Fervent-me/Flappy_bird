# coding=utf-8

import math
import os
from random import randint
from collections import deque

import sys
import pygame
from pygame.locals import *


FPS = 60
Animation_SPEED = 0.18  # pixels per millisecond
WIN_WIDTH = 284 * 2     # BG image size: 284x512 px; tiled twice
WIN_HEIGHT = 512


class Bird(pygame.sprite.Sprite):

    Width = Height = 32
    Sink_Speed = 0.1 #小鸟下沉速度
    Climb_Speed = 0.4 #爬升速度
    Climb_Duration = 100 #333.3  #爬升持续时间

    def __init__(self, x, y, msec_to_climb, images):

        super(Bird, self).__init__()
        self.x, self.y = x, y
        self.msec_to_climb = msec_to_climb
        self._img_wingup, self._img_wingdown = images
        '''self._mask_wingup = pygame.mask.from_surface(self._img_wingup)
        self._mask_wingdown = pygame.mask.from_surface(self._img_wingdown)'''

    def update(self, delta_frames=1):
        """更新鸟的位置。
            此函数使用余弦函数实现平滑爬升：
            在第一帧和最后几帧中，鸟儿爬得很少，在爬的中间，它爬得很多。
            一次完整的爬升持续时间毫秒，在此期间，鸟儿以平均爬升速度px/ms爬升。
            如果调用此方法时该Bird的msec_u to_u climb属性大于0，则该属性将自动相应地减小。

            delta_frames：自上次调用此方法以来经过的帧数。
        """
        if self.msec_to_climb > 0:
            frac_climb_done = 1 - self.msec_to_climb/Bird.Climb_Duration
            self.y -= (Bird.Climb_Speed * frames_to_msec(delta_frames) *
                       (1 - math.cos(frac_climb_done * math.pi)))
            self.msec_to_climb -= frames_to_msec(delta_frames)
        else:
            self.y += Bird.Sink_Speed * frames_to_msec(delta_frames)
        """
        """

    @property
    def image(self):
        if pygame.time.get_ticks() % 500 >= 250:
            """以毫秒为间隔"""
            return self._img_wingup
        else:
            return self._img_wingdown

    ''''@property
    def mask(self):

        if pygame.time.get_ticks() % 500 >= 250:
            return self._mask_wingup
        else:
            return self._mask_wingdown'''

    @property
    def rect(self):
        """Get the bird's position, width, and height, as a pygame.Rect."""
        return Rect(self.x, self.y, Bird.Width, Bird.Height)


class PipePair(pygame.sprite.Sprite):

    WIDTH = 80 # 管道的宽度
    PIECE_HEIGHT = 32 # 管道切片的高度
    ADD_INTERVAL = 3000  # 添加管道对的时间间隔，单位：毫秒

    def __init__(self, pipe_end_img, pipe_body_img):

        super(PipePair, self).__init__()
        self.x = float(WIN_WIDTH - 1)
        self.score_counted = False

        self.image = pygame.Surface((PipePair.WIDTH, WIN_HEIGHT), SRCALPHA)
        self.image.convert()   # speeds up blitting
        self.image.fill((0, 0, 0, 0))
        total_pipe_body_pieces = int(
            (WIN_HEIGHT -  # fill window from top to bottom
             3 * Bird.Height -  # make room for bird to fit through
             3 * PipePair.PIECE_HEIGHT) /  # 2 end pieces + 1 body piece
            PipePair.PIECE_HEIGHT          # to get number of pipe pieces
        )
        self.bottom_pieces = randint(1, total_pipe_body_pieces)
        self.top_pieces = total_pipe_body_pieces - self.bottom_pieces

        # bottom pipe
        for i in range(1, self.bottom_pieces + 1):#
            piece_pos = (0, WIN_HEIGHT - i*PipePair.PIECE_HEIGHT)
            self.image.blit(pipe_body_img, piece_pos)
        bottom_pipe_end_y = WIN_HEIGHT - self.bottom_height_px
        bottom_end_piece_pos = (0, bottom_pipe_end_y - PipePair.PIECE_HEIGHT)
        self.image.blit(pipe_end_img, bottom_end_piece_pos)

        # top pipe
        for i in range(self.top_pieces):
            self.image.blit(pipe_body_img, (0, i * PipePair.PIECE_HEIGHT))
        top_pipe_end_y = self.top_height_px
        self.image.blit(pipe_end_img, (0, top_pipe_end_y))

        # compensate for added end pieces
        self.top_pieces += 1
        self.bottom_pieces += 1

        # for collision detection
        self.mask = pygame.mask.from_surface(self.image)

    @property
    def top_height_px(self):
        """获取顶部管道的高度（以像素为单位）."""
        return self.top_pieces * PipePair.PIECE_HEIGHT

    @property
    def bottom_height_px(self):
        """获取底部管道的高度（以像素为单位）."""
        return self.bottom_pieces * PipePair.PIECE_HEIGHT

    @property
    def visible(self):
        """获取是否在屏幕上显示此管道对，对播放器可见."""
        return -PipePair.WIDTH < self.x < WIN_WIDTH

    @property
    def rect(self):
        """以pygame.Rect格式获取鸟的位置、宽度和高度。"""
        return Rect(self.x, 0, PipePair.WIDTH, PipePair.PIECE_HEIGHT)

    def update(self, delta_frames=1):
        """更新管道对的位置.
        delta_frames：自上次调用此方法以来经过的帧数。
        """
        self.x -= Animation_SPEED * frames_to_msec(delta_frames)

    def collides_with(self, bird):
        """弄清楚这只鸟是否与这对管子里的管子相撞.
        鸟：应测试是否与该管道发生碰撞的鸟.
        """
        return pygame.sprite.collide_mask(self, bird)


def load_images():
    '''加载游戏所需的所有图像并返回它们的dict。
        返回的dict具有以下键：
        背景：游戏的背景图片。
        鸟翼向上：鸟翼朝上的图像。
        用这个和鸟翼下降来创建一个拍打的鸟。
        鸟翼向下：鸟翼向下的图像。
        使用这个和鸟翅膀来创建一个拍打鸟。
        管道末端：管道末端的图像（略宽一点）。
        用这个和管体做管子。
        管道主体：管道主体切片的图像。用这个和管体做管子。
        '''

    def load_image(img_file_name):

        file_name = os.path.join(os.path.dirname(__file__),
                                 'images', img_file_name)
        img = pygame.image.load(file_name)
        '''img.convert()'''
        return img

    return {'background': load_image('background.png'),
            'pipe-end': load_image('pipe_end.png'),
            'pipe-body': load_image('pipe_body.png'),
            'bird-wingup': load_image('bird_wing_up.png'),
            'bird-wingdown': load_image('bird_wing_down.png')}


def frames_to_msec(frames, fps=FPS):
    """以指定的帧速率将帧转换为毫秒。
        帧数：要转换为毫秒的帧数。
        fps：用于转换的帧速率。默认值：FPS。
    """
    return 1000.0 * frames / fps


def msec_to_frames(milliseconds, fps=FPS):
    """以指定的帧速率将毫秒转换为帧。
        毫秒：转换为帧的毫秒数。
        fps：用于转换的帧速率。默认值：FPS。
    """
    return fps * milliseconds / 1000.0


def main():
    """
    初始化游戏
    应用程序的入口点。

    如果有人执行这个模块（例如，不是导入它），则调用这个函数.
    """
    pygame.init()
    screen = pygame.display.set_mode((284*2,512))
    pygame.display.set_caption("Flappy_bird") 
    cover = pygame.image.load(r"D:\appdownload\python\a_game\images\cover.jpg")
    flag = 1
    while flag:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    flag = 0 
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        screen.blit(cover,(0,0)) 
        pygame.display.update()
        
    pygame.init()

    pygame.mixer.init()
    pygame.mixer.music.load('Megalovania.mp3')
    pygame.mixer.music.play()
    """背景音乐"""

    display_surface = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    pygame.display.set_caption('Pygame Flappy Bird')
    """"设置游戏界面大小，标题"""

    clock = pygame.time.Clock()
    """创建时钟对象"""

    score_font = pygame.font.SysFont('arial', 32)
    """使用字体模块，第一个是字体名，第二个是字体大小"""

    images = load_images()

    # the bird stays in the same x position, so bird.x is a constant
    # center bird on screen
    bird = Bird(50, int(WIN_HEIGHT / 2 - Bird.Height / 2), 2,
                (images['bird-wingup'], images['bird-wingdown']))

    pipes = deque()

    frame_clock = 0  # this counter is only incremented if the game isn't paused
    score = 0
    done = paused = False
    while not done:
        clock.tick(FPS)

        # Handle this 'manually'.  If we used pygame.time.set_timer(),
        # pipe addition would be messed up when paused.
        if not (paused or frame_clock % msec_to_frames(PipePair.ADD_INTERVAL)):
            pp = PipePair(images['pipe-end'], images['pipe-body'])
            pipes.append(pp)

        for e in pygame.event.get():
            if e.type == QUIT or (e.type == KEYUP and e.key == K_ESCAPE):
                done = True
                break
            elif e.type == KEYUP and e.key in (K_PAUSE, K_p):
                paused = not paused
            elif e.type == MOUSEBUTTONUP or (e.type == KEYUP and
                    e.key in (K_UP, K_RETURN, K_SPACE)):
                bird.msec_to_climb = Bird.Climb_Duration

        if paused:
            continue  # don't draw anything

        # check for collisions #检测碰撞
        pipe_collision = any(p.collides_with(bird) for p in pipes)
        if pipe_collision or 0 >= bird.y or bird.y >= WIN_HEIGHT - Bird.Height:
            done = True

        for x in (0, WIN_WIDTH / 2):
            display_surface.blit(images['background'], (x, 0))

        while pipes and not pipes[0].visible:
            pipes.popleft()

        for p in pipes:
            p.update()
            display_surface.blit(p.image, p.rect)

        bird.update()
        display_surface.blit(bird.image, bird.rect)

        for p in pipes:
            if p.x + PipePair.WIDTH < bird.x and not p.score_counted:
                score += 1
                p.score_counted = True

        score_surface = score_font.render(str(score), True, (255, 255, 255))
        score_x = WIN_WIDTH/2 - score_surface.get_width()/2
        display_surface.blit(score_surface, (score_x, PipePair.PIECE_HEIGHT))
        """"标明游戏中通过管道数量，即得分"""

        pygame.display.flip()
        """更新整个待显示的Surface对象到屏幕上，更新得分"""

        frame_clock += 1
    print('Game over! Score: %i' % score)
    pygame.quit()


if __name__ == '__main__':
    # If this module had been imported, __name__ would be 'flappybird'.
    # It was executed (e.g. by double-clicking the file), so call main.
    main()