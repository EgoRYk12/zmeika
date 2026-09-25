import pygame
import random
import sys
import math
import time

# ===== БАЗОВЫЕ РАЗМЕРЫ (для окна) =====
DEFAULT_W, DEFAULT_H = 900, 650

# ===== ГЛОБАЛЬНЫЕ (меняются в зависимости от режима) =====
WIDTH, HEIGHT = DEFAULT_W, DEFAULT_H

# ===== НАСТРОЙКИ =====
FPS = 60
SPEED_PER_SEC = 156
SEGMENT_DIST = 14
START_LENGTH = 8
FOOD_RADIUS = 10
MAX_HP = 100
BULLET_SPEED_PER_SEC = 540
FIRE_COOLDOWN = 0.2
TURN_RATE_PER_SEC = 420
MELEE_COOLDOWN = 0.5
MELEE_ACTIVE = 0.2
MELEE_RANGE = 45
MELEE_DAMAGE = 3

# ===== СЛОЖНОСТИ =====
DIFFICULTIES = {
    "easy":   {"name": "ЛЕГКИЙ",  "boss_interval": 50.0, "hp_mult": 0.7, "speed_mult": 0.7, "shoot_mult": 1.3},
    "medium": {"name": "СРЕДНИЙ", "boss_interval": 30.0, "hp_mult": 1.0, "speed_mult": 1.0, "shoot_mult": 1.0},
    "hard":   {"name": "СЛОЖНЫЙ", "boss_interval": 20.0, "hp_mult": 1.5, "speed_mult": 1.3, "shoot_mult": 0.75},
}

# ===== ЦВЕТА =====
BG_TOP = (12, 20, 30)
BG_BOTTOM = (25, 40, 55)
SNAKE_HEAD = (30, 230, 130)
SNAKE_BODY_1 = (0, 200, 110)
SNAKE_BODY_2 = (0, 150, 80)
EYE_WHITE = (255, 255, 255)
EYE_BLACK = (10, 10, 10)
TONGUE = (255, 60, 90)
FOOD_OUTER = (255, 60, 60)
FOOD_INNER = (255, 140, 140)
FOOD_LEAF = (60, 180, 60)
TEXT_COLOR = (240, 240, 240)
BUTTON_COLOR = (30, 180, 100)
BUTTON_HOVER = (40, 220, 130)
BUTTON_TEXT = (255, 255, 255)
HP_BG = (60, 20, 20)
HP_FG = (220, 50, 50)
HP_SNAKE = (40, 200, 90)
BOSS_COLOR = (180, 40, 180)
BOSS_EYE = (255, 255, 0)
BOSS_BULLET = (255, 100, 255)
PLAYER_BULLET = (100, 240, 255)
PLAYER_BULLET_GLOW = (200, 255, 255)
MELEE_COLOR = (255, 255, 100)

# ===== СОСТОЯНИЕ =====
screen = None
game_surface = None
fullscreen = True
background_cache = None


def build_background():
    global background_cache
    surf = pygame.Surface((WIDTH, HEIGHT))
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        r = int(BG_TOP[0] * (1 - ratio) + BG_BOTTOM[0] * ratio)
        g = int(BG_TOP[1] * (1 - ratio) + BG_BOTTOM[1] * ratio)
        b = int(BG_TOP[2] * (1 - ratio) + BG_BOTTOM[2] * ratio)
        pygame.draw.line(surf, (r, g, b), (0, y), (WIDTH, y))
    background_cache = surf
    return surf


def get_background():
    if background_cache is None:
        return build_background()
    return background_cache


def apply_display_mode():
    global screen, game_surface, fullscreen, WIDTH, HEIGHT, background_cache
    try:
        if fullscreen:
            screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            screen = pygame.display.set_mode((DEFAULT_W, DEFAULT_H))

        WIDTH, HEIGHT = screen.get_size()
        game_surface = screen

        background_cache = None
        build_background()

        pygame.event.pump()
        pygame.event.clear()
        screen.fill((0, 0, 0))
        pygame.display.flip()
        pygame.time.wait(80)

        print(f"[{'FULLSCREEN' if fullscreen else 'WINDOWED'}] {WIDTH}x{HEIGHT}")
    except pygame.error as e:
        print(f"Ошибка переключения: {e}")
        fullscreen = not fullscreen
        WIDTH = DEFAULT_W
        HEIGHT = DEFAULT_H
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        game_surface = screen
        background_cache = None
        build_background()


def present():
    pygame.display.flip()


def to_game_coords(pos):
    return pos


# ===== КНОПКА =====
class Button:
    def __init__(self, x, y, w, h, text, action):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.action = action
        self.hovered = False
        self.font = pygame.font.SysFont("Arial", 28, bold=True)

    def draw(self, surface):
        color = BUTTON_HOVER if self.hovered else BUTTON_COLOR
        pygame.draw.rect(surface, color, self.rect, border_radius=14)
        pygame.draw.rect(surface, (255, 255, 255), self.rect, 2, border_radius=14)
        text_surf = self.font.render(self.text, True, BUTTON_TEXT)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def check_hover(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)

    def check_click(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)


# ===== ПУЛИ =====
class PlayerBullet:
    def __init__(self, x, y, dx, dy):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.radius = 6
        self.alive = True
        self.trail = []

    def update(self, dt):
        self.trail.append((self.x, self.y))
        if len(self.trail) > 6:
            self.trail.pop(0)
        self.x += self.dx * dt
        self.y += self.dy * dt
        if self.x < -20 or self.x > WIDTH + 20 or self.y < -20 or self.y > HEIGHT + 20:
            self.alive = False

    def draw(self, surface):
        for i, (tx, ty) in enumerate(self.trail):
            alpha = (i + 1) / len(self.trail)
            r = int(self.radius * alpha)
            if r > 0:
                pygame.draw.circle(surface, PLAYER_BULLET, (int(tx), int(ty)), r)
        pygame.draw.circle(surface, PLAYER_BULLET_GLOW, (int(self.x), int(self.y)), self.radius + 3)
        pygame.draw.circle(surface, PLAYER_BULLET, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, (255, 255, 255), (int(self.x) - 2, int(self.y) - 2), 2)


class BossBullet:
    def __init__(self, x, y, dx, dy):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.radius = 8
        self.alive = True
        self.trail = []

    def update(self, dt):
        self.trail.append((self.x, self.y))
        if len(self.trail) > 5:
            self.trail.pop(0)
        self.x += self.dx * dt
        self.y += self.dy * dt
        if self.x < -20 or self.x > WIDTH + 20 or self.y < -20 or self.y > HEIGHT + 20:
            self.alive = False

    def draw(self, surface):
        for i, (tx, ty) in enumerate(self.trail):
            alpha = (i + 1) / len(self.trail)
            r = int(self.radius * alpha * 0.8)
            if r > 0:
                pygame.draw.circle(surface, BOSS_BULLET, (int(tx), int(ty)), r)
        pygame.draw.circle(surface, (255, 180, 255), (int(self.x), int(self.y)), self.radius + 2)
        pygame.draw.circle(surface, BOSS_BULLET, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, (255, 255, 255), (int(self.x) - 2, int(self.y) - 2), 3)


# ===== БОСС =====
class Boss:
    def __init__(self, level, diff):
        side = random.choice(["left", "right", "top", "bottom"])
        if side == "left":
            self.x, self.y = -50, random.randint(100, HEIGHT - 100)
        elif side == "right":
            self.x, self.y = WIDTH + 50, random.randint(100, HEIGHT - 100)
        elif side == "top":
            self.x, self.y = random.randint(100, WIDTH - 100), -50
        else:
            self.x, self.y = random.randint(100, WIDTH - 100), HEIGHT + 50

        self.level = level
        base_hp = 5 + (level - 1) * 3
        self.max_hp = max(3, int(base_hp * diff["hp_mult"]))
        self.hp = self.max_hp
        self.speed = (50 + level * 9) * diff["speed_mult"]
        self.radius = 35 + level * 3
        self.shoot_timer = 0
        self.shoot_cooldown = max(0.35, (1.5 - level * 0.15) * diff["shoot_mult"])
        self.hit_flash = 0

    def update(self, snake_pos, bullets, dt):
        sx, sy = snake_pos
        dx = sx - self.x
        dy = sy - self.y
        dist = math.hypot(dx, dy) or 1
        self.x += dx / dist * self.speed * dt
        self.y += dy / dist * self.speed * dt

        self.shoot_timer += dt
        if self.shoot_timer >= self.shoot_cooldown:
            self.shoot_timer = 0
            bdx = dx / dist * 240
            bdy = dy / dist * 240
            bullets.append(BossBullet(self.x, self.y, bdx, bdy))

        if self.hit_flash > 0:
            self.hit_flash -= 1

    def draw(self, surface):
        color = (255, 100, 100) if self.hit_flash > 0 else BOSS_COLOR
        pygame.draw.circle(surface, (0, 0, 0), (int(self.x) + 3, int(self.y) + 4), self.radius)
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, (255, 200, 255), (int(self.x), int(self.y)), self.radius, 3)
        eye_r = self.radius // 4
        pygame.draw.circle(surface, BOSS_EYE, (int(self.x) - self.radius // 3, int(self.y) - 5), eye_r)
        pygame.draw.circle(surface, BOSS_EYE, (int(self.x) + self.radius // 3, int(self.y) - 5), eye_r)
        pygame.draw.circle(surface, (0, 0, 0), (int(self.x) - self.radius // 3, int(self.y) - 5), eye_r // 2)
        pygame.draw.circle(surface, (0, 0, 0), (int(self.x) + self.radius // 3, int(self.y) - 5), eye_r // 2)
        pygame.draw.arc(surface, (0, 0, 0),
                        (self.x - self.radius // 2, self.y, self.radius, self.radius // 2),
                        3.14, 6.28, 3)

        bar_w = self.radius * 2
        bar_h = 8
        bar_x = self.x - bar_w // 2
        bar_y = self.y - self.radius - 20
        pygame.draw.rect(surface, HP_BG, (bar_x, bar_y, bar_w, bar_h), border_radius=4)
        ratio = max(0, self.hp / self.max_hp)
        pygame.draw.rect(surface, HP_FG, (bar_x, bar_y, int(bar_w * ratio), bar_h), border_radius=4)


# ===== ЗМЕЙКА =====
class Snake:
    def __init__(self):
        self.x = WIDTH // 2
        self.y = HEIGHT // 2
        self.angle = 0
        self.body = [[self.x - i * SEGMENT_DIST, self.y] for i in range(START_LENGTH)]
        self.length = START_LENGTH
        self.tongue_timer = 0
        self.tongue_out = False
        self.hp = MAX_HP
        self.hurt_flash = 0
        self.fire_cooldown = 0
        self.melee_cooldown = 0
        self.melee_active = 0
        self.melee_hit_done = False

    def handle_input(self, keys):
        dx = 0
        dy = 0
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy += 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy -= 1
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += 1
        if dx == 0 and dy == 0:
            return None
        return math.degrees(math.atan2(dy, dx))

    def update(self, target_angle, dt):
        if self.fire_cooldown > 0:
            self.fire_cooldown -= dt
        if self.melee_cooldown > 0:
            self.melee_cooldown -= dt
        if self.melee_active > 0:
            self.melee_active -= dt
            if self.melee_active <= 0:
                self.melee_active = 0
                self.melee_hit_done = False

        if target_angle is not None:
            diff = (target_angle - self.angle + 180) % 360 - 180
            max_turn = TURN_RATE_PER_SEC * dt
            if diff > max_turn:
                diff = max_turn
            elif diff < -max_turn:
                diff = -max_turn
            self.angle = (self.angle + diff) % 360

        rad = math.radians(self.angle)
        move_dist = SPEED_PER_SEC * dt
        self.x += math.cos(rad) * move_dist
        self.y -= math.sin(rad) * move_dist

        if self.x < 0:
            self.x = WIDTH
            for seg in self.body:
                seg[0] += WIDTH
        elif self.x > WIDTH:
            self.x = 0
            for seg in self.body:
                seg[0] -= WIDTH
        if self.y < 0:
            self.y = HEIGHT
            for seg in self.body:
                seg[1] += HEIGHT
        elif self.y > HEIGHT:
            self.y = 0
            for seg in self.body:
                seg[1] -= HEIGHT

        self.body[0] = [self.x, self.y]

        while len(self.body) < self.length:
            tail = self.body[-1]
            prev = self.body[-2] if len(self.body) > 1 else [tail[0] - SEGMENT_DIST, tail[1]]
            ddx = tail[0] - prev[0]
            ddy = tail[1] - prev[1]
            d = math.hypot(ddx, ddy) or 1
            self.body.append([tail[0] + ddx / d * SEGMENT_DIST,
                              tail[1] + ddy / d * SEGMENT_DIST])

        while len(self.body) > self.length:
            self.body.pop()

        for i in range(1, len(self.body)):
            prev = self.body[i - 1]
            cur = self.body[i]
            ddx = cur[0] - prev[0]
            ddy = cur[1] - prev[1]
            d = math.hypot(ddx, ddy)
            if d > 0:
                ratio = SEGMENT_DIST / d
                cur[0] = prev[0] + ddx * ratio
                cur[1] = prev[1] + ddy * ratio

        head = self.body[0]
        for i in range(5, len(self.body)):
            seg = self.body[i]
            if math.hypot(head[0] - seg[0], head[1] - seg[1]) < SEGMENT_DIST * 0.55:
                return False

        self.tongue_timer += 1
        if self.tongue_timer > 60:
            self.tongue_out = not self.tongue_out
            self.tongue_timer = 0

        if self.hurt_flash > 0:
            self.hurt_flash -= 1

        return True

    def grow(self):
        self.length += 1

    def take_damage(self, dmg):
        self.hp -= dmg
        self.hurt_flash = 20
        if self.hp < 0:
            self.hp = 0

    def heal(self, amount):
        self.hp = min(MAX_HP, self.hp + amount)

    def fire(self, target_pos=None):
        if self.fire_cooldown > 0:
            return None
        head = self.body[0]
        rad = math.radians(self.angle)
        fwd_x = math.cos(rad)
        fwd_y = -math.sin(rad)
        start_x = head[0] + fwd_x * (SEGMENT_DIST + 4)
        start_y = head[1] + fwd_y * (SEGMENT_DIST + 4)

        if target_pos is not None:
            dx = target_pos[0] - start_x
            dy = target_pos[1] - start_y
            dist = math.hypot(dx, dy) or 1
            bdx = dx / dist * BULLET_SPEED_PER_SEC
            bdy = dy / dist * BULLET_SPEED_PER_SEC
        else:
            bdx = fwd_x * BULLET_SPEED_PER_SEC
            bdy = fwd_y * BULLET_SPEED_PER_SEC

        self.fire_cooldown = FIRE_COOLDOWN
        return PlayerBullet(start_x, start_y, bdx, bdy)

    def melee_attack(self):
        if self.melee_cooldown > 0:
            return False
        self.melee_cooldown = MELEE_COOLDOWN
        self.melee_active = MELEE_ACTIVE
        self.melee_hit_done = False
        return True

    def check_melee_hit(self, tx, ty):
        if self.melee_active <= 0 or self.melee_hit_done:
            return False
        head = self.body[0]
        rad = math.radians(self.angle)
        fwd_x = math.cos(rad)
        fwd_y = -math.sin(rad)
        punch_x = head[0] + fwd_x * 25
        punch_y = head[1] + fwd_y * 25
        if math.hypot(punch_x - tx, punch_y - ty) < MELEE_RANGE:
            self.melee_hit_done = True
            return True
        return False

    def draw(self, surface):
        for i in range(len(self.body) - 1, 0, -1):
            seg = self.body[i]
            ratio = i / max(1, len(self.body))
            r = int(SNAKE_BODY_1[0] * (1 - ratio) + SNAKE_BODY_2[0] * ratio)
            g = int(SNAKE_BODY_1[1] * (1 - ratio) + SNAKE_BODY_2[1] * ratio)
            b = int(SNAKE_BODY_1[2] * (1 - ratio) + SNAKE_BODY_2[2] * ratio)
            radius = int(SEGMENT_DIST * 0.9 * (1 - ratio * 0.5)) + 2
            pygame.draw.circle(surface, (r, g, b), (int(seg[0]), int(seg[1])), radius)
            pygame.draw.circle(surface, (180, 255, 210),
                             (int(seg[0]) - radius // 3, int(seg[1]) - radius // 3),
                             max(1, radius // 3))

        head = self.body[0]
        head_radius = SEGMENT_DIST + 2
        head_color = (255, 80, 80) if self.hurt_flash > 0 else SNAKE_HEAD
        pygame.draw.circle(surface, head_color, (int(head[0]), int(head[1])), head_radius)
        pygame.draw.circle(surface, (200, 255, 220),
                         (int(head[0]) - 4, int(head[1]) - 4), 5)

        rad = math.radians(self.angle)
        perp_x = math.sin(rad)
        perp_y = math.cos(rad)
        fwd_x = math.cos(rad)
        fwd_y = -math.sin(rad)

        for side in (1, -1):
            ex = head[0] + fwd_x * 6 + perp_x * 7 * side
            ey = head[1] + fwd_y * 6 + perp_y * 7 * side
            pygame.draw.circle(surface, EYE_WHITE, (int(ex), int(ey)), 5)
            pygame.draw.circle(surface, EYE_BLACK,
                             (int(ex + fwd_x * 2), int(ey + fwd_y * 2)), 3)

        if self.tongue_out:
            tongue_len = 14
            tx = head[0] + fwd_x * (head_radius + tongue_len)
            ty = head[1] + fwd_y * (head_radius + tongue_len)
            pygame.draw.line(surface, TONGUE,
                           (int(head[0] + fwd_x * head_radius), int(head[1] + fwd_y * head_radius)),
                           (int(tx), int(ty)), 3)
            pygame.draw.line(surface, TONGUE, (int(tx), int(ty)),
                           (int(tx + perp_x * 5), int(ty + perp_y * 5)), 2)
            pygame.draw.line(surface, TONGUE, (int(tx), int(ty)),
                           (int(tx - perp_x * 5), int(ty - perp_y * 5)), 2)

    def draw_melee(self, surface):
        if self.melee_active <= 0:
            return
        head = self.body[0]
        rad = math.radians(self.angle)
        fwd_x = math.cos(rad)
        fwd_y = -math.sin(rad)
        punch_x = head[0] + fwd_x * 25
        punch_y = head[1] + fwd_y * 25
        progress = 1 - (self.melee_active / MELEE_ACTIVE)
        radius = int(20 + progress * 25)
        alpha = int(255 * (1 - progress))

        surf = pygame.Surface((120, 120), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*MELEE_COLOR, alpha), (60, 60), radius, 4)
        pygame.draw.circle(surf, (255, 255, 200, alpha), (60, 60), max(2, radius // 3))
        surface.blit(surf, (int(punch_x) - 60, int(punch_y) - 60))

    def get_head_pos(self):
        return self.body[0]


# ===== ЕДА =====
class Food:
    def __init__(self, snake):
        self.position = self.random_position(snake)
        self.pulse = 0

    def random_position(self, snake):
        while True:
            x = random.randint(FOOD_RADIUS + 20, WIDTH - FOOD_RADIUS - 20)
            y = random.randint(FOOD_RADIUS + 20, HEIGHT - FOOD_RADIUS - 20)
            head = snake.get_head_pos()
            if math.hypot(x - head[0], y - head[1]) > 100:
                return [x, y]

    def respawn(self, snake):
        self.position = self.random_position(snake)

    def draw(self, surface):
        self.pulse = (self.pulse + 0.1) % 6.28
        size = FOOD_RADIUS + math.sin(self.pulse) * 1.5
        x, y = self.position
        pygame.draw.circle(surface, (0, 0, 0), (int(x) + 2, int(y) + 3), int(size))
        pygame.draw.circle(surface, FOOD_OUTER, (int(x), int(y)), int(size))
        pygame.draw.circle(surface, FOOD_INNER, (int(x) - 3, int(y) - 3), int(size) // 2)
        pygame.draw.circle(surface, (255, 220, 220), (int(x) - 4, int(y) - 4), 3)
        pygame.draw.ellipse(surface, FOOD_LEAF,
                          (int(x) + 4, int(y) - int(size) - 6, 10, 6))


# ===== МЕНЮ =====
def menu_screen(clock):
    global fullscreen
    font_title = pygame.font.SysFont("Arial", 80, bold=True)
    font_hint = pygame.font.SysFont("Arial", 18)

    pygame.mouse.set_visible(True)

    cy = HEIGHT // 2
    btn_w, btn_h = 280, 70
    cx = WIDTH // 2 - btn_w // 2

    play_btn = Button(cx, cy - 130, btn_w, btn_h, "ИГРАТЬ", "play")
    settings_btn = Button(cx, cy - 30, btn_w, btn_h, "НАСТРОЙКИ", "settings")
    exit_btn = Button(cx, cy + 70, btn_w, btn_h, "ВЫХОД", "exit")
    buttons = [play_btn, settings_btn, exit_btn]

    show_settings = False
    fs_btn = Button(cx, cy - 30, btn_w, 60, "", "fullscreen")
    back_btn = Button(cx, HEIGHT - 110, btn_w, 60, "НАЗАД", "back")

    while True:
        raw_mouse = pygame.mouse.get_pos()
        mouse_pos = to_game_coords(raw_mouse)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if show_settings:
                    if fs_btn.check_click(mouse_pos):
                        fullscreen = not fullscreen
                        apply_display_mode()
                        cy = HEIGHT // 2
                        cx = WIDTH // 2 - btn_w // 2
                        play_btn = Button(cx, cy - 130, btn_w, btn_h, "ИГРАТЬ", "play")
                        settings_btn = Button(cx, cy - 30, btn_w, btn_h, "НАСТРОЙКИ", "settings")
                        exit_btn = Button(cx, cy + 70, btn_w, btn_h, "ВЫХОД", "exit")
                        buttons = [play_btn, settings_btn, exit_btn]
                        fs_btn = Button(cx, cy - 30, btn_w, 60, "", "fullscreen")
                        back_btn = Button(cx, HEIGHT - 110, btn_w, 60, "НАЗАД", "back")
                    if back_btn.check_click(mouse_pos):
                        show_settings = False
                else:
                    for btn in buttons:
                        if btn.check_click(mouse_pos):
                            if btn.action == "play":
                                return "play"
                            elif btn.action == "settings":
                                show_settings = True
                            elif btn.action == "exit":
                                pygame.quit()
                                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if show_settings:
                    show_settings = False
                else:
                    pygame.quit()
                    sys.exit()

        game_surface.blit(get_background(), (0, 0))

        title = font_title.render("ЗМЕЙКА 2.0", True, SNAKE_HEAD)
        title_shadow = font_title.render("ЗМЕЙКА 2.0", True, (0, 100, 60))
        title_y = HEIGHT // 5
        game_surface.blit(title_shadow, (WIDTH // 2 - title.get_width() // 2 + 4, title_y + 4))
        game_surface.blit(title, (WIDTH // 2 - title.get_width() // 2, title_y))

        if not show_settings:
            for btn in buttons:
                btn.check_hover(mouse_pos)
                btn.draw(game_surface)
            hint = font_hint.render("WASD / стрелки — движение. ESC — выход", True, (120, 120, 120))
            game_surface.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 50))
        else:
            title2 = font_title.render("НАСТРОЙКИ", True, SNAKE_HEAD)
            game_surface.blit(title2, (WIDTH // 2 - title2.get_width() // 2, HEIGHT // 4))

            fs_text = "ПОЛНЫЙ ЭКРАН: ВКЛ" if fullscreen else "ПОЛНЫЙ ЭКРАН: ВЫКЛ"
            fs_btn.text = fs_text
            fs_btn.check_hover(mouse_pos)
            fs_btn.draw(game_surface)

            lines = [
                "WASD / стрелки — движение",
                "Зажми две кнопки — диагональ",
                "ЛКМ — выстрел пулей (летит в босса)",
                "ПКМ — рукопашный удар",
                "P — пауза   |   R — рестарт   |   ESC — меню",
            ]
            for i, line in enumerate(lines):
                color = TEXT_COLOR if i < 3 else (150, 200, 255)
                txt = font_hint.render(line, True, color)
                game_surface.blit(txt, (WIDTH // 2 - txt.get_width() // 2, HEIGHT // 2 + 60 + i * 30))

            back_btn.check_hover(mouse_pos)
            back_btn.draw(game_surface)

        present()
        clock.tick(FPS)


# ===== ЭКРАН СЛОЖНОСТИ =====
def difficulty_screen(clock):
    font_title = pygame.font.SysFont("Arial", 60, bold=True)
    font_sub = pygame.font.SysFont("Arial", 18)

    pygame.mouse.set_visible(True)

    cy = HEIGHT // 2
    btn_w, btn_h = 360, 70
    cx = WIDTH // 2 - btn_w // 2

    easy_btn = Button(cx, cy - 130, btn_w, btn_h, "ЛЁГКИЙ (босс 50 сек)", "easy")
    medium_btn = Button(cx, cy - 30, btn_w, btn_h, "СРЕДНИЙ (босс 30 сек)", "medium")
    hard_btn = Button(cx, cy + 70, btn_w, btn_h, "СЛОЖНЫЙ (босс 20 сек)", "hard")
    back_btn = Button(cx, HEIGHT - 110, btn_w, 60, "НАЗАД", "back")
    buttons = [easy_btn, medium_btn, hard_btn, back_btn]

    while True:
        raw_mouse = pygame.mouse.get_pos()
        mouse_pos = to_game_coords(raw_mouse)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for btn in buttons:
                    if btn.check_click(mouse_pos):
                        if btn.action == "back":
                            return None
                        return btn.action
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return None

        game_surface.blit(get_background(), (0, 0))

        title = font_title.render("ВЫБЕРИ СЛОЖНОСТЬ", True, SNAKE_HEAD)
        game_surface.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 6))

        sub = font_sub.render("Чем сложнее — тем чаще боссы и они сильнее", True, (150, 200, 255))
        game_surface.blit(sub, (WIDTH // 2 - sub.get_width() // 2, HEIGHT // 6 + 80))

        for btn in buttons:
            btn.check_hover(mouse_pos)
            btn.draw(game_surface)

        present()
        clock.tick(FPS)


# ===== ЭКРАН ПРОИГРЫША =====
def game_over_screen(score, clock):
    font_big = pygame.font.SysFont("Arial", 64, bold=True)
    font_mid = pygame.font.SysFont("Arial", 28)

    cy = HEIGHT // 2
    btn_w, btn_h = 260, 65
    cx = WIDTH // 2 - btn_w // 2
    restart_btn = Button(cx, cy + 60, btn_w, btn_h, "ЗАНОВО", "restart")
    menu_btn = Button(cx, cy + 150, btn_w, btn_h, "В МЕНЮ", "menu")
    buttons = [restart_btn, menu_btn]

    pygame.mouse.set_visible(True)

    while True:
        raw_mouse = pygame.mouse.get_pos()
        mouse_pos = to_game_coords(raw_mouse)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for btn in buttons:
                    if btn.check_click(mouse_pos):
                        return btn.action
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return "restart"
                if event.key == pygame.K_ESCAPE:
                    return "menu"

        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(190)
        overlay.fill((0, 0, 0))
        game_surface.blit(overlay, (0, 0))

        text1 = font_big.render("ИГРА ОКОНЧЕНА", True, (255, 80, 80))
        text2 = font_mid.render(f"Твой счёт: {score}", True, TEXT_COLOR)
        game_surface.blit(text1, (WIDTH // 2 - text1.get_width() // 2, cy - 120))
        game_surface.blit(text2, (WIDTH // 2 - text2.get_width() // 2, cy - 30))

        for btn in buttons:
            btn.check_hover(mouse_pos)
            btn.draw(game_surface)

        present()
        clock.tick(FPS)


# ===== ПАУЗА =====
def pause_screen(clock):
    font_big = pygame.font.SysFont("Arial", 72, bold=True)
    font_mid = pygame.font.SysFont("Arial", 24)

    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(180)
    overlay.fill((0, 0, 0))
    game_surface.blit(overlay, (0, 0))

    text = font_big.render("ПАУЗА", True, SNAKE_HEAD)
    game_surface.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - 80))

    hint = font_mid.render("Нажми P, чтобы продолжить", True, TEXT_COLOR)
    game_surface.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT // 2 + 30))
    hint2 = font_mid.render("ESC — выйти в меню", True, (150, 150, 150))
    game_surface.blit(hint2, (WIDTH // 2 - hint2.get_width() // 2, HEIGHT // 2 + 70))

    present()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    return "resume"
                if event.key == pygame.K_ESCAPE:
                    return "menu"
        clock.tick(FPS)


# ===== ИГРА =====
def play_game(clock, difficulty_key):
    diff = DIFFICULTIES[difficulty_key]

    font_score = pygame.font.SysFont("Arial", 26, bold=True)
    font_hint = pygame.font.SysFont("Arial", 16)
    font_big = pygame.font.SysFont("Arial", 40, bold=True)

    snake = Snake()
    food = Food(snake)
    score = 0
    bosses_defeated = 0
    boss = None
    boss_bullets = []
    player_bullets = []

    boss_timer = 0.0
    flash_message = ""
    flash_timer = 0

    pygame.mouse.set_visible(True)

    lmb_held = False
    rmb_held = False

    last_time = time.time()

    while True:
        now = time.time()
        dt = now - last_time
        last_time = now
        if dt > 0.1:
            dt = 0.1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "menu", score
                if event.key == pygame.K_p:
                    if pause_screen(clock) == "menu":
                        return "menu", score
                    last_time = time.time()
                if event.key == pygame.K_r:
                    return "restart", score
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    lmb_held = True
                elif event.button == 3:
                    rmb_held = True
            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    lmb_held = False
                elif event.button == 3:
                    rmb_held = False

        keys = pygame.key.get_pressed()
        target_angle = snake.handle_input(keys)

        if lmb_held and score > 0:
            if boss:
                bullet = snake.fire((boss.x, boss.y))
            else:
                bullet = snake.fire()
            if bullet:
                player_bullets.append(bullet)
                score -= 1

        if rmb_held:
            snake.melee_attack()

        if not snake.update(target_angle, dt):
            return "gameover", score

        if snake.hp <= 0:
            return "gameover", score

        if boss is None:
            boss_timer += dt
            if boss_timer >= diff["boss_interval"]:
                boss_timer = 0
                bosses_defeated += 1
                boss = Boss(bosses_defeated, diff)
                flash_message = f"БОСС {bosses_defeated} ПОЯВИЛСЯ!"
                flash_timer = 2.0

        if boss:
            boss.update(snake.get_head_pos(), boss_bullets, dt)
            head = snake.get_head_pos()
            if math.hypot(head[0] - boss.x, head[1] - boss.y) < boss.radius + SEGMENT_DIST:
                if snake.hurt_flash == 0:
                    snake.take_damage(20)
            if snake.check_melee_hit(boss.x, boss.y):
                boss.hp -= MELEE_DAMAGE
                boss.hit_flash = 10

        for b in player_bullets:
            b.update(dt)
            if boss and b.alive:
                if math.hypot(b.x - boss.x, b.y - boss.y) < boss.radius + b.radius:
                    boss.hp -= 1
                    boss.hit_flash = 10
                    b.alive = False
        player_bullets = [b for b in player_bullets if b.alive]

        if boss and boss.hp <= 0:
            boss = None
            score += 15
            snake.heal(25)
            boss_bullets.clear()
            flash_message = "БОСС ПОБЕЖДЁН! +15 очков, +25 HP"
            flash_timer = 2.0

        for b in boss_bullets:
            b.update(dt)

        for b in boss_bullets:
            if not b.alive:
                continue
            for seg in snake.body:
                if math.hypot(b.x - seg[0], b.y - seg[1]) < b.radius + SEGMENT_DIST * 0.8:
                    snake.take_damage(10)
                    b.alive = False
                    break
        boss_bullets = [b for b in boss_bullets if b.alive]

        head = snake.get_head_pos()
        if math.hypot(head[0] - food.position[0], head[1] - food.position[1]) < FOOD_RADIUS + SEGMENT_DIST:
            snake.grow()
            score += 1
            snake.heal(5)
            food.respawn(snake)

        game_surface.blit(get_background(), (0, 0))
        food.draw(game_surface)

        for b in boss_bullets:
            b.draw(game_surface)
        for b in player_bullets:
            b.draw(game_surface)

        if boss:
            boss.draw(game_surface)

        snake.draw(game_surface)
        snake.draw_melee(game_surface)

        if snake.hurt_flash > 0:
            flash_overlay = pygame.Surface((WIDTH, HEIGHT))
            flash_overlay.set_alpha(int(snake.hurt_flash * 6))
            flash_overlay.fill((255, 0, 0))
            game_surface.blit(flash_overlay, (0, 0), special_flags=pygame.BLEND_ADD)

        bar_w, bar_h = 200, 22
        bar_x, bar_y = 20, 50
        pygame.draw.rect(game_surface, HP_BG, (bar_x, bar_y, bar_w, bar_h), border_radius=6)
        hp_ratio = max(0, snake.hp / MAX_HP)
        pygame.draw.rect(game_surface, HP_SNAKE, (bar_x, bar_y, int(bar_w * hp_ratio), bar_h), border_radius=6)
        pygame.draw.rect(game_surface, (255, 255, 255), (bar_x, bar_y, bar_w, bar_h), 2, border_radius=6)
        hp_text = font_hint.render(f"HP: {int(snake.hp)}/{MAX_HP}", True, TEXT_COLOR)
        game_surface.blit(hp_text, (bar_x + bar_w + 10, bar_y + 2))

        score_text = font_score.render(f"Очки: {score}", True, TEXT_COLOR)
        game_surface.blit(score_text, (20, 15))

        diff_text = font_hint.render(f"Сложность: {diff['name']}", True, (180, 180, 180))
        game_surface.blit(diff_text, (20, 85))

        if boss is None:
            time_left = diff["boss_interval"] - boss_timer
            timer_text = font_hint.render(f"Босс через: {max(0, time_left):.0f} сек", True, (200, 200, 100))
            game_surface.blit(timer_text, (20, 105))
        else:
            timer_text = font_hint.render("БОСС АКТИВЕН!", True, (255, 100, 100))
            game_surface.blit(timer_text, (20, 105))

        hint = font_hint.render("WASD — движение   |   ЛКМ — авто-пуля   |   ПКМ — удар   |   ESC — меню",
                                True, (120, 120, 120))
        game_surface.blit(hint, (WIDTH - hint.get_width() - 15, 15))

        if flash_timer > 0:
            flash_timer -= dt
            alpha = min(255, int(flash_timer * 255))
            msg_surf = font_big.render(flash_message, True, (255, 255, 100))
            msg_surf.set_alpha(alpha)
            game_surface.blit(msg_surf, (WIDTH // 2 - msg_surf.get_width() // 2, 100))

        present()
        clock.tick(FPS)


# ===== ГЛАВНАЯ =====
def main():
    global screen, game_surface
    pygame.init()
    apply_display_mode()
    pygame.display.set_caption("Змейка 2.0")
    clock = pygame.time.Clock()

    while True:
        action = menu_screen(clock)

        if action == "play":
            difficulty_key = difficulty_screen(clock)
            if difficulty_key is None:
                continue

            while True:
                result, score = play_game(clock, difficulty_key)
                if result == "menu":
                    break
                elif result == "restart":
                    continue
                elif result == "gameover":
                    choice = game_over_screen(score, clock)
                    if choice == "restart":
                        continue
                    else:
                        break


if __name__ == "__main__":
    main()