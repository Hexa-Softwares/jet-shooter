"""Jet Shooter - Pygame version

Controls:
- Move: Arrow keys or A/D/W/S
- Fire: Space
- Switch element: 1 (Air), 2 (Water), 3 (Fire)
- Quit: ESC or window close

This script implements an endless shooter with three enemy tiers and elemental attacks.
"""
import math
import random
import sys
import os
import pygame

pygame.init()

# Asset dir
ASSET_DIR = os.path.join(os.path.dirname(__file__), 'assets')


def generate_assets():
    # Ensure assets folder exists (user will place custom assets here)
    os.makedirs(ASSET_DIR, exist_ok=True)


# NOTE: asset generation and mixer initialization run after colors are defined

# --- Config ---
WIDTH, HEIGHT = 900, 600
FPS = 60

# Colors (dark/techy)
BG = (12, 14, 20)
HUD_BG = (18, 20, 28)
NEON_CYAN = (24, 255, 255)
NEON_PINK = (255, 28, 179)
NEON_YELLOW = (255, 210, 20)
WHITE = (230, 230, 230)

# generate assets now that colors/constants exist
generate_assets()

# try to init mixer and load fire sound
try:
    pygame.mixer.init()
except Exception:
    pass
FIRE_SOUND = None
try:
    fire_file = os.path.join(ASSET_DIR, 'fire.wav')
    if os.path.exists(fire_file):
        FIRE_SOUND = pygame.mixer.Sound(fire_file)
except Exception:
    FIRE_SOUND = None
HIT_SOUND = None
BOMB_SOUND = None
try:
    hit_file = os.path.join(ASSET_DIR, 'hit.wav')
    if os.path.exists(hit_file):
        HIT_SOUND = pygame.mixer.Sound(hit_file)
except Exception:
    HIT_SOUND = None
try:
    bomb_file = os.path.join(ASSET_DIR, 'bomb.wav')
    if os.path.exists(bomb_file):
        BOMB_SOUND = pygame.mixer.Sound(bomb_file)
except Exception:
    BOMB_SOUND = None

screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
font_small = pygame.font.SysFont("Consolas", 18)
font_big = pygame.font.SysFont("Consolas", 32)


def draw_text(surf, text, pos, font, color=WHITE):
    surf.blit(font.render(text, True, color), pos)


class Player(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.speed = 4
        # Load player sprite from assets (user must provide player_ship.png)
        player_file = os.path.join(ASSET_DIR, 'player_ship.png')
        img = pygame.image.load(player_file).convert_alpha()
        img = pygame.transform.smoothscale(img, (160, 102))
        self.image = img
        self.rect = self.image.get_rect(center=pos)
        self.lives = 3
        self.score = 0
        self.element = 'Air'  # Air, Water, Fire
        self.fire_cooldown = 0

    def update(self, keys):
        dx = dy = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = self.speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy = -self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy = self.speed

        self.rect.x = max(10, min(WIDTH - 10 - self.rect.width, self.rect.x + dx))
        self.rect.y = max(60, min(HEIGHT - 10 - self.rect.height, self.rect.y + dy))

        if self.fire_cooldown > 0:
            self.fire_cooldown -= 1

    def fire(self):
        if self.fire_cooldown > 0:
            return []
        self.fire_cooldown = 14  # base rate
        shots = []
        cx, cy = self.rect.center
        if self.element == 'Air':
            shots.append(Projectile((cx, cy - 10), (0, -8), 'Air'))
        elif self.element == 'Water':
            # water: 3 spread small pulses
            for a in (-0.15, 0, 0.15):
                vx = math.sin(a) * 6
                vy = -6
                shots.append(Projectile((cx, cy - 10), (vx, vy), 'Water'))
        elif self.element == 'Fire':
            # fire: fast single projectile
            shots.append(Projectile((cx, cy - 10), (0, -12), 'Fire'))
        # play fire sound if available
        try:
            if FIRE_SOUND:
                FIRE_SOUND.play()
        except Exception:
            pass
        return shots


class Projectile(pygame.sprite.Sprite):
    def __init__(self, pos, vel, element):
        super().__init__()
        self.pos = pygame.math.Vector2(pos)
        self.vel = pygame.math.Vector2(vel)
        self.element = element
        
        # Try to load custom projectile sprite from assets
        fname = f"projectile_{element.lower()}.png"
        path = os.path.join(ASSET_DIR, fname)
        try:
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                # Scale based on element type (increased Water/Fire sizes)
                size = {'Air': 32, 'Water': 18, 'Fire': 28}[element]
                img = pygame.transform.smoothscale(img, (size, size))
                self.image = img
                # set attributes for explosion logic
                self.radius = size // 2
                self.color = {'Air': NEON_PINK, 'Water': (80, 160, 255), 'Fire': NEON_YELLOW}[element]
            else:
                # Fallback to procedural circle if sprite not found (larger water/fire)
                self.radius = {'Air': 16, 'Water': 9, 'Fire': 14}[element]
                self.color = {'Air': NEON_PINK, 'Water': (80, 160, 255), 'Fire': NEON_YELLOW}[element]
                self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(self.image, self.color, (self.radius, self.radius), self.radius)
        except Exception:
            # Fallback to procedural circle on any error
            self.radius = {'Air': 16, 'Water': 9, 'Fire': 14}[element]
            self.color = {'Air': NEON_PINK, 'Water': (80, 160, 255), 'Fire': NEON_YELLOW}[element]
            self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(self.image, self.color, (self.radius, self.radius), self.radius)
        
        self.rect = self.image.get_rect(center=pos)

    def update(self, *args):
        self.pos += self.vel
        self.rect.center = (int(self.pos.x), int(self.pos.y))
        # remove if off-screen
        if self.rect.bottom < 0 or self.rect.top > HEIGHT or self.rect.left > WIDTH or self.rect.right < 0:
            self.kill()


class Bomb(pygame.sprite.Sprite):
    def __init__(self, pos, target):
        super().__init__()
        self.pos = pygame.math.Vector2(pos)
        dir = (pygame.math.Vector2(target) - self.pos).normalize()
        self.vel = dir * 4.5
        self.image = pygame.Surface((10, 10), pygame.SRCALPHA)
        pygame.draw.circle(self.image, NEON_YELLOW, (5, 5), 5)
        self.rect = self.image.get_rect(center=pos)

    def update(self, *args):
        self.pos += self.vel
        self.rect.center = (int(self.pos.x), int(self.pos.y))
        if self.rect.top > HEIGHT or self.rect.left > WIDTH or self.rect.right < 0:
            self.kill()


class Explosion(pygame.sprite.Sprite):
    def __init__(self, pos, radius, color):
        super().__init__()
        self.pos = pos
        self.radius = radius
        self.color = color
        self.lifetime = 18
        self.image = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=pos)

    def update(self):
        t = self.lifetime
        self.image.fill((0, 0, 0, 0))
        alpha = int(255 * (t / 18.0))
        pygame.draw.circle(self.image, (*self.color, alpha), (self.radius, self.radius), int(self.radius * (1 - (18 - t) / 22)))
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.kill()


class Enemy(pygame.sprite.Sprite):
    def __init__(self, pos, kind='Beginner'):
        super().__init__()
        self.kind = kind
        self.pos = pygame.math.Vector2(pos)
        # Load enemy sprite from assets (user must provide enemy_{beginner,mid,hard}.png)
        fname = f"enemy_{kind.lower()}.png"
        path = os.path.join(ASSET_DIR, fname)
        img = pygame.image.load(path).convert_alpha()
        img = pygame.transform.smoothscale(img, (40, 28))
        self.image = img
        self.rect = self.image.get_rect(center=pos)
        # assign HP and color per kind; color used for explosions even when sprite is present
        if kind == 'Beginner':
            self.hp = 1
            self.speed = 1.0
            self.color = (90, 200, 255)
        elif kind == 'Mid':
            self.hp = 2
            self.speed = 1.2
            self.color = (255, 120, 90)
        else:  # Hard
            self.hp = 3
            self.speed = 0.9
            self.color = (255, 80, 200)
        self.direction = pygame.math.Vector2(random.uniform(-0.6, 0.6), 1).normalize()
        self.shoot_timer = random.randint(40, 120)

    def update(self, *args):
        # simple movement downward + slight horizontal sway
        self.pos += self.direction * self.speed
        self.rect.center = (int(self.pos.x), int(self.pos.y))

        if self.rect.top > HEIGHT + 20:
            self.kill()


def spawn_enemy():
    x = random.randint(40, WIDTH - 40)
    # Weighted spawn: Beginner more often, Mid moderate, Hard less frequent
    kinds = ['Beginner', 'Mid', 'Hard']
    weights = [0.6, 0.3, 0.1]
    choice = random.choices(kinds, weights=weights, k=1)[0]
    return Enemy((x, -20), choice)


def main():
    all_sprites = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    projectiles = pygame.sprite.Group()
    bombs = pygame.sprite.Group()
    explosions = pygame.sprite.Group()

    player = Player((WIDTH // 2, HEIGHT - 80))
    all_sprites.add(player)

    spawn_timer = 0
    running = True

    # techy overlay surfaces
    hud_surface = pygame.Surface((WIDTH, 56))

    while running:
        clock.tick(FPS)
        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    shots = player.fire()
                    for s in shots:
                        all_sprites.add(s)
                        projectiles.add(s)
                elif event.key == pygame.K_1:
                    player.element = 'Air'
                elif event.key == pygame.K_2:
                    player.element = 'Water'
                elif event.key == pygame.K_3:
                    player.element = 'Fire'
                elif event.key == pygame.K_q:
                    # cycle previous
                    order = ['Air', 'Water', 'Fire']
                    idx = order.index(player.element)
                    player.element = order[(idx - 1) % len(order)]
                elif event.key == pygame.K_e:
                    # cycle next
                    order = ['Air', 'Water', 'Fire']
                    idx = order.index(player.element)
                    player.element = order[(idx + 1) % len(order)]

        # spawn logic
        spawn_timer -= 1
        if spawn_timer <= 0:
            spawn_timer = random.randint(18, 42)
            e = spawn_enemy()
            all_sprites.add(e)
            enemies.add(e)

        # update
        all_sprites.update(keys)
        projectiles.update()
        bombs.update()
        explosions.update()

        # enemy shooting (Hard fires bombs)
        for e in list(enemies):
            if e.kind == 'Hard':
                e.shoot_timer -= 1
                if e.shoot_timer <= 0:
                    e.shoot_timer = random.randint(60, 140)
                    bomb = Bomb(e.rect.center, player.rect.center)
                    all_sprites.add(bomb)
                    bombs.add(bomb)

        # projectile hits enemy
        for proj in list(projectiles):
            hit = pygame.sprite.spritecollideany(proj, enemies)
            if hit:
                # Effectiveness: all bullets deal 1 damage (elements are just for visual/audio variety)
                effectiveness = 1

                hit.hp -= effectiveness
                explosions.add(Explosion(proj.rect.center, proj.radius * 2, proj.color))
                # play hit sound
                try:
                    if HIT_SOUND:
                        HIT_SOUND.play()
                except Exception:
                    pass
                proj.kill()
                if hit.hp <= 0:
                    hit.kill()
                    player.score += 5

        # bombs hit player
        if pygame.sprite.spritecollideany(player, bombs):
            # reduce life, explosion
            for b in bombs:
                if b.rect.colliderect(player.rect):
                    explosions.add(Explosion(b.rect.center, 36, NEON_YELLOW))
                    # play bomb sound
                    try:
                        if BOMB_SOUND:
                            BOMB_SOUND.play()
                    except Exception:
                        pass
                    b.kill()
                    player.lives -= 1
                    if player.lives <= 0:
                        running = False
                    break

        # enemies collide with player
        collided = pygame.sprite.spritecollideany(player, enemies)
        if collided:
            # damages player depending on kind
            player.lives -= 1
            explosions.add(Explosion(collided.rect.center, 28, collided.color))
            collided.kill()
            if player.lives <= 0:
                running = False

        # draw
        screen.fill(BG)

        # background grid for techy feel
        for gx in range(0, WIDTH, 40):
            pygame.draw.line(screen, (18, 20, 28), (gx, 56), (gx, HEIGHT), 1)
        for gy in range(56, HEIGHT, 40):
            pygame.draw.line(screen, (18, 20, 28), (0, gy), (WIDTH, gy), 1)

        all_sprites.draw(screen)
        projectiles.draw(screen)
        bombs.draw(screen)
        explosions.draw(screen)

        # HUD
        hud_surface.fill(HUD_BG)
        pygame.draw.rect(hud_surface, (30, 30, 40), (0, 0, WIDTH, 56))
        # score
        draw_text(hud_surface, f"Score: {player.score}", (14, 12), font_big, NEON_CYAN)
        # lives
        lives_x = WIDTH - 180
        draw_text(hud_surface, "Lives:", (lives_x, 8), font_small, WHITE)
        for i in range(player.lives):
            pygame.draw.polygon(hud_surface, NEON_PINK, [(lives_x + 58 + i * 30, 26), (lives_x + 68 + i * 30, 6), (lives_x + 78 + i * 30, 26)])

        # element indicator
        draw_text(hud_surface, f"Element: {player.element}", (WIDTH//2 - 80, 12), font_small, WHITE)
        el_col = {'Air': NEON_PINK, 'Water': (80, 160, 255), 'Fire': NEON_YELLOW}[player.element]
        pygame.draw.circle(hud_surface, el_col, (WIDTH//2 + 80, 26), 10)

        screen.blit(hud_surface, (0, 0))

        # tooltips
        draw_text(screen, "1-Air  2-Water  3-Fire  |  Q/E to cycle  |  Space=Fire  |  Move=Arrows/WASD", (12, HEIGHT-26), font_small, (160, 160, 160))

        pygame.display.flip()

    # end game screen
    screen.fill(BG)
    draw_text(screen, "GAME OVER", (WIDTH//2 - 90, HEIGHT//2 - 32), font_big, NEON_PINK)
    draw_text(screen, f"Final Score: {player.score}", (WIDTH//2 - 90, HEIGHT//2 + 8), font_small, NEON_CYAN)
    pygame.display.flip()
    pygame.time.wait(2000)
    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()
