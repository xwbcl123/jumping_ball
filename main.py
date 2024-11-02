# 来自跳跃小球的注释
# 这个版本增加了无敌状态和透明度效果，以及游戏结束和通关的界面。
# 游戏结束和通关界面更加美观，并且增加了重新开始按钮。
# 游戏暂停和继续功能也得到了改进。
#感谢所有支持我的创友们。我会继续努力的！

import pgzrun
import random
import math
import os
from pgzero.actor import Actor
from pgzero.keyboard import keyboard
from pgzero.constants import keys
from pygame import Rect

# 设置窗口大小
WIDTH = 1280
HEIGHT = 720

# 设置字体路径
FONT_PATH = "msyh.ttc"

# 添加新的全局变量
initial_platform_timer = 0  # 在初始平台上的停留时间
SHOW_INPUT_HINT = False    # 是否显示输入法提示
HINT_DELAY = 300          # 停留5秒后显示提示 (60帧/秒 * 5)
has_moved = False         # 添加移动标记
show_scared = False
scared_timer = 0
SCARED_DURATION = 120  # 显示2秒 (60帧/秒 * 2)
SCARED_ROUNDS = [2, 4, 6, 8, 10]  # 可能出现scared的回合
scared_opacity = 255  # 控制闪烁的透明度
scared_fade_direction = -1  # 控制透度变化方向

# 设置口位置到屏幕中心
os.environ['SDL_VIDEO_CENTERED'] = '1'  # 这行代码会让窗口居显示

# 添加一些颜色常量，使界面更加美观
COLORS = {
    'background': (135, 206, 235),  # 天蓝色背景
    'platform': (46, 204, 113),     # 翠绿色平台
    'initial_platform': (230, 126, 34),  # 橙色初始平台
    'score_text': (255, 255, 255),  # 白色分数
    'invincible_text': (241, 196, 15),  # 金色无敌时间
    'panel_bg': (44, 62, 80),       # 深蓝色面板背景
    'panel_border': (52, 152, 219), # 蓝色边框
    'title_text': (231, 76, 60),    # 红色标题
    'score_value': (46, 204, 113),  # 绿色分数
    'hint_text': (241, 196, 15),    # 黄色提示
    'button_bg': (52, 152, 219),    # 蓝色按钮
    'button_text': (255, 255, 255)  # 白色按钮文字
}

# 创建平台的函数 - 移到前面来
def create_platform(y):
    """创建一个新平台"""
    min_x = 50  # 左边界
    max_x = WIDTH - PLATFORM_WIDTH - 50  # 右边界
    
    # 确保新平台与现有平台不重叠
    while True:
        x = random.randint(min_x, max_x)
        new_platform = Rect((x, y), (PLATFORM_WIDTH, PLATFORM_HEIGHT))
        
        # 检查是否与其他平台重叠
        overlapping = False
        for platform in platforms:
            if (abs(platform.y - y) < PLATFORM_HEIGHT * 2 and  # 垂直距离检
                abs(platform.centerx - x - PLATFORM_WIDTH/2) < PLATFORM_WIDTH * 1.2):  # 水平距离检
                overlapping = True
                break
        
        if not overlapping:
            return new_platform

# 初始化小球
class Ball:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 20
        self.base_color = (255, 64, 129)  # 初始粉色
        self.color = self.base_color      # 添加 color 属性
        self.opacity = 255
        self.fade_direction = -1

    def update_color_by_score(self, score):
        # 根据分数调整颜色的饱和度和亮度
        intensity = min(1.0 + score / 50.0, 2.0)  # 限制最大增益为2倍
        
        # 基础颜色
        base_r, base_g, base_b = 255, 64, 129
        
        # 增加颜色的鲜艳度，但保持在255以内
        r = min(255, int(base_r * intensity))
        g = min(255, int(base_g * intensity))
        b = min(255, int(base_b * intensity))
        
        # 添加彩虹效果
        if score > 50:
            # 使用正弦函数创建颜色循环
            time_factor = score / 10  # 控制颜色变化速度
            r = int((math.sin(time_factor) * 0.5 + 0.5) * 255)
            g = int((math.sin(time_factor + 2) * 0.5 + 0.5) * 255)
            b = int((math.sin(time_factor + 4) * 0.5 + 0.5) * 255)
        
        self.color = (r, g, b)

    def update_opacity(self):
        if is_invincible:
            self.opacity += self.fade_direction * 3
            if self.opacity <= 128:
                self.opacity = 128
                self.fade_direction = 1
            elif self.opacity >= 255:
                self.opacity = 255
                self.fade_direction = -1
        else:
            self.opacity = 255

    def draw(self):
        self.update_opacity()
        # 更新颜色
        self.update_color_by_score(score)
        
        color_with_alpha = (*self.color, self.opacity)
        screen.draw.filled_circle((self.x, self.y), self.radius, color_with_alpha)
        
        # 根据分数调整光晕效果
        glow_radius = self.radius + 5 + min(score // 10, 15)  # 分数越高光晕越大
        glow_opacity = int(self.opacity * (0.2 + min(score / 200, 0.4)))  # 分数越高光晕越亮
        screen.draw.circle((self.x, self.y), glow_radius, 
                         (*self.color, glow_opacity))

# 游戏变量
ball = None
ball_speed_y = 0
platforms = []
score = 0
game_over = False
initial_platform = None
initial_platform_opacity = 255  # 初始平台的透明度
has_left_initial_platform = False  # 用于跟玩家是否离开过初始平台
is_invincible = False  # 无敌状态
invincible_timer = 0   # 无敌时间计时器
INVINCIBLE_DURATION = 5 * 60  # 5秒 (60帧/秒)
is_paused = False  # 添加暂停状态变量
snowflakes = []

# 游戏常量
GRAVITY = 0.8
JUMP_SPEED = -25  # 从 -15 改为 -25，增加基础跳跃高度
PLATFORM_WIDTH = 100
PLATFORM_HEIGHT = 20
PLATFORM_COLOR = (0, 255, 0)
PLATFORM_SPEED = 2
MOVE_SPEED = 12  # 增加移动速度
PLATFORM_FADE_SPEED = 1  # 平台消失速度
PLATFORM_SPACING = 90  # 减小平台间距，从120改为90
INITIAL_PLATFORMS = 12  # 增加初始平台数量，从8改为12

# 添加雪花类
class Snowflake:
    def __init__(self):
        # 初始化时随机分布在整个屏幕上
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(0, HEIGHT)  # 直接在屏幕范围内随机位置
        self.size = random.randint(2, 4)
        self.active = True
        self.platform = None
        self.speed = random.uniform(2, 5)
        self.angle = random.uniform(0, 360)

    def reset(self):
        self.x = random.randint(0, WIDTH)
        self.y = -50
        self.speed = random.uniform(2, 5)
        self.angle = random.uniform(0, 360)
        self.active = True
        self.platform = None

    def check_platform_collision(self):
        # 检查是否在初始平台上
        if initial_platform_opacity > 0:
            if (self.x > initial_platform.left and 
                self.x < initial_platform.right and 
                self.y > initial_platform.top and 
                self.y < initial_platform.top + 5):
                self.y = initial_platform.top
                self.active = False
                self.platform = initial_platform
                return True

        # 检查是否在其他平台上
        for platform in platforms:
            if (self.x > platform.left and 
                self.x < platform.right and 
                self.y > platform.top and 
                self.y < platform.top + 5):
                self.y = platform.top
                self.active = False
                self.platform = platform
                return True
        return False

    def update(self):
        if not self.active:  # 如果雪花已经落在平台上
            if self.platform:
                # 跟随平台移动
                self.y = self.platform.top
                # 如果平台超出屏幕重置雪花
                if self.platform.top > HEIGHT:
                    self.reset()
            return

        self.y += self.speed
        self.angle += 2
        self.x += math.sin(self.angle * 0.05) * 0.5

        # 检查平台碰撞
        self.check_platform_collision()

        # 如果超出屏幕底部，重置
        if self.y > HEIGHT:
            self.reset()

    def draw(self):
        # 绘制雪花
        alpha = random.randint(150, 255) if self.active else 200
        screen.draw.filled_circle((self.x, self.y), 
                                self.size, (255, 255, 255, alpha))
        screen.draw.filled_circle((self.x, self.y), 
                                self.size - 1, (255, 255, 255, alpha))

# 初始化雪花时确保它们匀分布
def init_game():
    """初始游戏"""
    global ball, ball_speed_y, platforms, score, game_over, initial_platform
    global initial_platform_opacity, has_left_initial_platform, is_invincible, invincible_timer
    global is_paused, snowflakes, has_moved, show_scared, scared_timer, scared_opacity
    global initial_platform_timer, SHOW_INPUT_HINT, EFFECTS_ENABLED
    
    # 重置所有游戏状态
    game_over = False
    score = 0
    is_paused = False
    has_moved = False
    initial_platform_timer = 0
    SHOW_INPUT_HINT = False
    EFFECTS_ENABLED = False  # 一开始就关闭光影效果
    
    # 创建初始平台 - 提高初始位置
    initial_platform = Rect((WIDTH//2 - PLATFORM_WIDTH//2, HEIGHT - 50),  # 从 HEIGHT - 50 改为 HEIGHT - 150
                          (PLATFORM_WIDTH, PLATFORM_HEIGHT))
    initial_platform_opacity = 255
    has_left_initial_platform = False
    
    # 初始化小球在初始平台上方
    ball = Ball(WIDTH//2, initial_platform.top - 20)
    ball_speed_y = 0
    
    # 初始化其他平台
    platforms.clear()
    for i in range(INITIAL_PLATFORMS):
        y = i * PLATFORM_SPACING
        platforms.append(create_platform(y))
    
    # 设置开局无敌时间
    is_invincible = True
    invincible_timer = 3 * 60  # 3秒无敌时间（60帧/秒）

    # 确保小球透明度重置
    if hasattr(ball, 'opacity'):
        ball.opacity = 255

    # 重置提示相关变量
    initial_platform_timer = 0
    SHOW_INPUT_HINT = False
    has_moved = False

    # 修改雪花初始化逻辑
    if EFFECTS_ENABLED:
        snowflakes = [Snowflake() for _ in range(100)]  # 只在开启光影时创建雪花
    else:
        snowflakes = []  # 关闭光影时不创建雪花

    # 重置scared状态
    show_scared = False
    scared_timer = 0
    scared_opacity = 255

# 初始化游戏
init_game()

# 修改音频路径的处理方式
import os

# 使用简单的字符串拼接而不是 os.path.join
SOUND_PATH = 'sounds'
if not os.path.exists(SOUND_PATH):
    SOUND_PATH = 'jumping_ball/sounds'

# 确保音频目录存在
if not os.path.exists(SOUND_PATH):
    try:
        os.makedirs(SOUND_PATH)
    except Exception as e:
        print(f"无法创建音频目录: {e}")
        SOUND_ENABLED = False

SOUND_ENABLED = True  # 控制音频是否启用

def update():
    global ball_speed_y, score, game_over, initial_platform_opacity, has_left_initial_platform
    global is_invincible, invincible_timer, is_paused, has_moved, show_scared, scared_timer
    global scared_opacity, scared_fade_direction, SOUND_ENABLED, snowflakes  # 添加 snowflakes
    global initial_platform_timer, SHOW_INPUT_HINT
    
    # 检查是否通关
    if score >= 100:
        game_over = True
        return

    # 如果游戏暂停或结束，不更新游戏状态
    if is_paused or game_over:
        return

    # 更新小球速度和位置
    ball_speed_y += GRAVITY
    ball.y += ball_speed_y

    # 键盘控制
    if keyboard.left or keyboard.a:
        ball.x = max(ball.radius, ball.x - MOVE_SPEED)
        has_moved = True
    if keyboard.right or keyboard.d:
        ball.x = min(WIDTH - ball.radius, ball.x + MOVE_SPEED)
        has_moved = True

    # 检查是否在初始平台区域
    is_above_initial = (ball.x > initial_platform.left and 
                       ball.x < initial_platform.right and
                       ball.y < initial_platform.bottom + 50)  # 给一个高度缓冲区
    
    # 如果不在初始平台区域内，标记为已离开
    if not is_above_initial:
        has_left_initial_platform = True

    # 如果已经离开过初始平台，开始减少透明度
    if has_left_initial_platform and initial_platform_opacity > 0:
        initial_platform_opacity -= 2  # 控制消速度

    # 检查是碰到顶部或底部
    if ball.y < ball.radius:  # 碰到顶部
        ball.y = ball.radius
        # 根据速度调整反弹力度
        ball_speed_y = abs(ball_speed_y) * 0.9  # 增加反弹系数
    elif ball.y > HEIGHT:  # 碰到底部
        if is_invincible:  # 如果是无敌状态，回到始台
            ball.x = WIDTH//2
            ball.y = initial_platform.top - 20
            ball_speed_y = 0
        else:
            game_over = True

    # 检测小球是否落在初始平台上
    if initial_platform_opacity > 0:
        if (ball_speed_y > 0 and
            ball.x > initial_platform.left and 
            ball.x < initial_platform.right and
            ball.y > initial_platform.top and 
            ball.y < initial_platform.bottom + 20):
            # 根据下落高度调整弹跳高度
            fall_height = ball.y - initial_platform.top
            bounce_factor = min(1.0, fall_height / 300)
            ball_speed_y = JUMP_SPEED * (0.8 + bounce_factor * 0.4)

    # 检测小球是否落在其他平台上
    for platform in platforms:
        if (ball_speed_y > 0 and
            ball.x > platform.left and ball.x < platform.right and
            ball.y > platform.top and ball.y < platform.bottom + 20):
            # 据下落度调整弹跳高度
            fall_height = ball.y - platform.top
            bounce_factor = min(1.0, fall_height / 300)
            ball_speed_y = JUMP_SPEED * (0.8 + bounce_factor * 0.4)
            score += 1

    # 移动并更新平台
    platforms_to_remove = []
    for platform in platforms:
        platform.y += PLATFORM_SPEED
        if platform.top > HEIGHT:
            platforms_to_remove.append(platform)
    
    # 移除超出屏幕的平台并创建新平台
    for platform in platforms_to_remove:
        platforms.remove(platform)
        min_y = min([p.y for p in platforms]) if platforms else 0
        new_y = min_y - PLATFORM_SPACING
        platforms.append(create_platform(new_y))

    # 修改雪更新逻辑
    if EFFECTS_ENABLED:
        # 如果之前没有雪花但现在开启了效果，创建雪花
        if not snowflakes:
            snowflakes = [Snowflake() for _ in range(100)]
        
        # 更新现有雪花
        for snowflake in snowflakes:
            snowflake.update()

        # 当初始平台消失时，重置其上的雪花
        if initial_platform_opacity <= 0:
            for snowflake in snowflakes:
                if not snowflake.active and snowflake.platform == initial_platform:
                    snowflake.reset()
    else:
        # 如果关闭了效果，清空雪花列表
        if snowflakes:
            snowflakes.clear()

    # 更新无敌时间
    if is_invincible:
        invincible_timer -= 1
        if invincible_timer <= 0:
            is_invincible = False
            ball.opacity = 255

    # 检查是否在初始平台上
    on_initial_platform = (ball.x > initial_platform.left and 
                         ball.x < initial_platform.right and
                         abs(ball.y - initial_platform.top) < 30 and
                         not has_left_initial_platform)  # 确保只在第一次检测

    # 更新初始平台停留时间
    if on_initial_platform:
        initial_platform_timer += 1
        if initial_platform_timer >= HINT_DELAY:
            SHOW_INPUT_HINT = True
    else:
        initial_platform_timer = 0
        SHOW_INPUT_HINT = False

    # 更新scared显示和闪烁效果
    if show_scared:
        scared_timer -= 1
        
        # 更新闪烁效果
        scared_opacity += scared_fade_direction * 15
        if scared_opacity <= 100:
            scared_opacity = 100
            scared_fade_direction = 1
        elif scared_opacity >= 255:
            scared_opacity = 255
            scared_fade_direction = -1
            
        # 时间了就关闭显示
        if scared_timer <= 0:
            show_scared = False
            scared_opacity = 255
            scared_fade_direction = -1
            return  # 立即返回，不再执行下面的检测

    # 检测是否需要显示scared - 修改触发逻辑
    current_round = (score // 10) + 1  # 计算当前回合
    if current_round in SCARED_ROUNDS:  # 在指定回合
        if score % 10 == 0 and not show_scared and score >= 10:  # 在回合开始时且未显示
            if random.random() < 0.001:  # 0.001%的概率显示
                show_scared = True
                scared_timer = SCARED_DURATION  # 120帧 = 2秒
                scared_opacity = 255
                scared_fade_direction = -1
                if SOUND_ENABLED:
                    try:
                        if hasattr(sounds, 'jump_scared'):
                            if check_sound_file():  # 添加文件存在检查
                                sounds.jump_scared.play()
                            else:
                                print("找不到音效文件")
                                SOUND_ENABLED = False
                        else:
                            print("找不到音效文件")
                            SOUND_ENABLED = False
                    except Exception as e:
                        print(f"音频播放失败: {str(e)}")
                        SOUND_ENABLED = False

# 在使用音频的地方添加路径检查
def check_sound_file():
    """检查音频文件是否存在"""
    # 使用简单的字符串拼接而不是 os.path.join
    sound_file = SOUND_PATH + '/jump_scared.wav'
    exists = os.path.exists(sound_file)
    if not exists:
        print(f"音频文件不存在: {sound_file}")
    return exists

def draw():
    # 1. 绘制背景
    if EFFECTS_ENABLED:
        # 渐变背景
        for i in range(HEIGHT):
            color = (
                int(135 + (i/HEIGHT) * 20),
                int(206 + (i/HEIGHT) * 10),
                int(235 - (i/HEIGHT) * 30)
            )
            screen.draw.line((0, i), (WIDTH, i), color)
    else:
        # 简单的纯色背景 - 修改这行
        screen.draw.filled_rect(
            Rect(0, 0, WIDTH, HEIGHT),
            (135, 206, 235)
        )
    
    # 2. 绘制光影开关按钮
    button_width = 100
    button_height = 40
    button_x = WIDTH - button_width - 10  # 距离右边界10像素
    button_y = 10  # 距离顶部10像素
    
    # 按钮阴影（只在开启效果时显示）
    if EFFECTS_ENABLED:
        screen.draw.filled_rect(
            Rect(button_x + 2, button_y + 2, button_width, button_height),
            (0, 0, 0, 100)
        )
    
    # 按钮主体 - 修改这里的颜色逻辑
    screen.draw.filled_rect(
        Rect(button_x, button_y, button_width, button_height),
        (100, 100, 100) if EFFECTS_ENABLED else (52, 152, 219)  # 开启时灰色，关闭时蓝色
    )
    
    # 按钮文字
    screen.draw.text("关光影" if EFFECTS_ENABLED else "开光影",
                    center=(button_x + button_width//2, button_y + button_height//2),
                    color="white",
                    fontsize=20,
                    fontname=FONT_PATH)

    # 3. 绘制雪花（只在开启效果时）
    if EFFECTS_ENABLED:
        for snowflake in snowflakes:
            snowflake.draw()
    
    # 4. 绘制平台（根据效果状态决定是否显示阴影和高光
    if initial_platform_opacity > 0:
        # 平台主体
        screen.draw.filled_rect(initial_platform, 
                              (150, 75, 0, initial_platform_opacity))
        if EFFECTS_ENABLED:
            # 平台顶部高光
            highlight_rect = Rect(initial_platform.left, initial_platform.top, 
                                initial_platform.width, 5)
            screen.draw.filled_rect(highlight_rect, 
                                  (255, 255, 255, int(initial_platform_opacity * 0.3)))
    
    # 5. 绘制其他平台
    for platform in platforms:
        if EFFECTS_ENABLED:
            # 平台阴影
            shadow_rect = Rect(platform.left + 2, platform.top + 2, 
                             platform.width, platform.height)
            screen.draw.filled_rect(shadow_rect, (0, 0, 0, 100))
        
        # 平台主体
        screen.draw.filled_rect(platform, PLATFORM_COLOR)
        
        if EFFECTS_ENABLED:
            # 平台顶部高光
            highlight_rect = Rect(platform.left, platform.top, platform.width, 3)
            screen.draw.filled_rect(highlight_rect, (255, 255, 255, 77))
    
    # 6. 绘制小球
    ball.draw()
    
    # 7. 显示分数
    screen.draw.text(f"得分: {score}", 
                    (12, 12),  # 阴影位置
                    color=(0, 0, 0, 128),
                    fontsize=36,
                    fontname=FONT_PATH)
    screen.draw.text(f"得分: {score}", 
                    (10, 10), 
                    color="white",
                    fontsize=36,
                    fontname=FONT_PATH)
    
    # 8. 显示无敌时间
    if is_invincible:
        screen.draw.text(f"无敌时间: {invincible_timer // 60 + 1}秒", 
                        (12, 52),
                        color=(0, 0, 0, 128),
                        fontsize=36,
                        fontname=FONT_PATH)
        screen.draw.text(f"无敌时间: {invincible_timer // 60 + 1}秒", 
                        (10, 50),
                        color=(241, 196, 15),
                        fontsize=36,
                        fontname=FONT_PATH)

    # 9. 显示暂停界面
    if is_paused and not game_over:
        # 绘制半透明黑色背景
        screen.draw.filled_rect(
            Rect(0, 0, WIDTH, HEIGHT),
            (0, 0, 0, 128)
        )
        
        # 绘制暂停文本
        screen.draw.text("游戏暂停", 
                        center=(WIDTH//2, HEIGHT//2 - 30),
                        color="white", 
                        fontsize=48,
                        fontname=FONT_PATH)
        screen.draw.text("按 P 继续游戏", 
                        center=(WIDTH//2, HEIGHT//2 + 30),
                        color="white", 
                        fontsize=24,
                        fontname=FONT_PATH)

    # 10. 在最上层绘制scared图片（带闪烁效果）
    if show_scared and scared_timer > 0:  # 只在计时器大于0时显示
        # 创建一个全屏的半透明黑色背景
        screen.draw.filled_rect(
            Rect(0, 0, WIDTH, HEIGHT),
            (0, 0, 0, int(scared_opacity * 0.8))
        )
        
        # 只在透明度较高时显示图片，创造闪烁效果
        if scared_opacity > 150:
            screen.blit('scared', (0, 0))

    # 显示游戏结束/通关界面
    if game_over:
        # 绘制模糊背景
        for i in range(3):
            screen.draw.filled_rect(
                Rect(0, 0, WIDTH, HEIGHT),
                (0, 0, 0, 60)
            )
        
        # 绘制面板
        panel_width = 800
        panel_height = 350
        panel_x = WIDTH // 2 - panel_width // 2
        panel_y = HEIGHT // 2 - panel_height // 2
        
        # 面板阴影
        shadow_offset = 10
        screen.draw.filled_rect(
            Rect(panel_x + shadow_offset, panel_y + shadow_offset, 
                 panel_width, panel_height),
            (0, 0, 0, 100)
        )
        
        # 面板主体
        screen.draw.filled_rect(
            Rect(panel_x, panel_y, panel_width, panel_height),
            (44, 62, 80)
        )
        
        # 面板边框
        for i in range(3):
            screen.draw.rect(
                Rect(panel_x-i, panel_y-i, panel_width+i*2, panel_height+i*2),
                (52, 152, 219)
            )

        # 在面板右上角绘制图片，根据分数决定使用哪个图片
        if score < 50:
            # 如果分数小于50，使用翻转的图片
            screen.blit('good_flip', 
                       (panel_x + panel_width - 100, panel_y - 50))
        else:
            # 分数大于等于50，使用正常图片
            screen.blit('good', 
                       (panel_x + panel_width - 100, panel_y - 50))
        
        if score >= 100:  # 通关
            screen.draw.text("哥们你牛，通这个游戏的你是第一个。", 
                           center=(WIDTH//2, panel_y + 100),
                           color=(231, 76, 60),  # 红色
                           fontsize=36,
                           fontname=FONT_PATH)
            
            screen.draw.text("（结束）", 
                           center=(WIDTH//2, panel_y + 160),
                           color=(46, 204, 113),  # 绿色
                           fontsize=36,
                           fontname=FONT_PATH)
        else:
            screen.draw.text("游戏结束!", 
                           center=(WIDTH//2, panel_y + 80),
                           color=(231, 76, 60),
                           fontsize=48,
                           fontname=FONT_PATH)
            
            screen.draw.text(f"最终得分: {score}", 
                           center=(WIDTH//2, panel_y + 140),
                           color=(46, 204, 113),
                           fontsize=36,
                           fontname=FONT_PATH)
        
        # 重新开始按钮
        button_width = 200
        button_height = 50
        button_x = WIDTH//2 - button_width//2
        button_y = panel_y + 220
        
        # 按钮阴影
        screen.draw.filled_rect(
            Rect(button_x + 2, button_y + 2, button_width, button_height),
            (0, 0, 0, 100)
        )
        
        # 按钮主体
        screen.draw.filled_rect(
            Rect(button_x, button_y, button_width, button_height),
            (52, 152, 219)
        )
        
        # 按钮文字
        screen.draw.text("重新开始", 
                        center=(WIDTH//2, button_y + button_height//2),
                        color="white",
                        fontsize=24,
                        fontname=FONT_PATH)

def on_key_down(key):
    global is_paused, game_over, EFFECTS_ENABLED, snowflakes
    
    # 修改光影开关处理
    if key == keys.G:
        EFFECTS_ENABLED = not EFFECTS_ENABLED
        if EFFECTS_ENABLED:
            # 开启光影时创建雪花
            snowflakes = [Snowflake() for _ in range(100)]
        else:
            # 关闭光影时清空雪花
            snowflakes.clear()
        return
    
    # 处理暂停键
    if key == keys.P and not game_over:
        is_paused = not is_paused
        return
    
    # 处理重新开始
    if game_over and (key == keys.SPACE or key == keys.RETURN):
        init_game()

def on_mouse_down(pos):
    """处理鼠标点击"""
    global EFFECTS_ENABLED, snowflakes
    
    # 更新光影开关按钮的点击处理
    button_width = 100
    button_height = 40
    button_x = WIDTH - button_width - 10
    button_y = 10
    
    if (button_x <= pos[0] <= button_x + button_width and 
        button_y <= pos[1] <= button_y + button_height):
        EFFECTS_ENABLED = not EFFECTS_ENABLED
        if EFFECTS_ENABLED:
            # 开启光影时创建雪花
            snowflakes = [Snowflake() for _ in range(100)]
        else:
            # 关闭光影时清空雪花
            snowflakes.clear()
        return
    
    # 原有的游戏结束重启按钮检测
    if game_over:
        panel_width = 800
        panel_height = 350
        panel_x = WIDTH // 2 - panel_width // 2
        panel_y = HEIGHT // 2 - panel_height // 2
        
        button_width = 200
        button_height = 50
        button_x = WIDTH//2 - button_width//2
        button_y = panel_y + 220
        
        if (button_x <= pos[0] <= button_x + button_width and 
            button_y <= pos[1] <= button_y + button_height):
            init_game()

pgzrun.go()
