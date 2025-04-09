import pgzrun
import time
from random import randint as r
import base64

# === Sound Loading ===
jump_sound = sounds.jump
gem_collect_sound = sounds.gem_collect
death_sound = sounds.death

# === Config Class ===
class Config:
    last_loaded = 0
    cache = {}

    @staticmethod
    def load():
        current_time = time.time()
        if current_time - Config.last_loaded > 1:
            try:
                with open('config.txt', 'r') as file:
                    new_config = {}
                    for line in file:
                        key, value = line.strip().split(':')
                        new_config[key.strip()] = float(value.strip())
                    Config.cache = new_config
                    Config.last_loaded = current_time
            except Exception as e:
                print(f"Config Reload Error: {e}")
        return Config.cache

config = Config.load()

# === Settings ===
WIDTH = int(config.get('Screen WIDTH', 750))
HEIGHT = int(config.get('Screen HEIGHT', 680))
GLOBAL_GRAVITY = config.get('GLOBAL_GRAVITY', 2.5)
JUMP_POWER = config.get('JUMP_POWER', 35)
MAX_FALL_SPEED = config.get('MAX_FALL_SPEED', 15)
MOVE_SPEED = config.get('MOVE_SPEED', 0.5)
H_GLIDE = config.get('H_GLIDE', 0.2)
PLATFORM_SPEED = config.get('PLATFORM_SPEED', 0.5)
MIN_PLATFORM_ON_SCREEN = int(config.get('MIN_PLATFORM_ON_SCREEN', 3))
MAX_GEM_AMOUNT = int(config.get('MAX_GEM_AMOUNT', 5))
HIGH_SCORE_FILE = "level.txt"
SOUND_VOLUME = config.get('SOUND_VOLUME', 0.5)  # Load volume setting from config

# === Set Sound Volume ===
def set_sound_volumes():
    jump_sound.set_volume(SOUND_VOLUME)
    gem_collect_sound.set_volume(SOUND_VOLUME)
    death_sound.set_volume(SOUND_VOLUME)

# === Game State ===
SCORE = 0
START = False

player = Actor('player_blue_stand.png')
player.pos = WIDTH / 2, HEIGHT / 2
player.X_velocity = 0
player.Y_velocity = 0

gems = []
spikes = []
platforms = []

# === Background Parallax State ===
bg_far_offset = 0
bg_near_offset = 0

# === High Score ===
def encrypt_score(score):
    return base64.b64encode(str(score).encode()).decode()

def decrypt_score(encrypted_score):
    try:
        return int(base64.b64decode(encrypted_score.encode()).decode())
    except Exception:
        return 0

def load_high_score():
    try:
        with open(HIGH_SCORE_FILE, "r") as file:
            return decrypt_score(file.read().strip())
    except:
        return 0

def save_high_score(score):
    with open(HIGH_SCORE_FILE, "w") as file:
        file.write(encrypt_score(score))

def update_high_score(score):
    if score > load_high_score():
        save_high_score(score)

# === Helpers ===
def collide(actor, victim):
    return actor.colliderect(victim)

def drawPlatforms():
    for platform in platforms:
        platform.draw()

def drawGems():
    for gem in gems:
        gem.draw()

def drawSpikes():
    for spike in spikes:
        spike.draw()

def drawBackground():
    global bg_far_offset, bg_near_offset
    tile_width, tile_height = 64, 64

    # Parallax speeds
    bg_far_offset -= PLATFORM_SPEED * 0.2
    bg_near_offset -= PLATFORM_SPEED * 0.5

    bg_far_offset %= tile_width
    bg_near_offset %= tile_width

    # Far background layer
    for row in range(0, HEIGHT // tile_height + 2):
        for col in range(-1, WIDTH // tile_width + 2):
            color = (200, 230, 255)
            x = col * tile_width + bg_far_offset
            y = row * tile_height
            screen.draw.filled_rect(Rect((x, y), (tile_width, tile_height)), color)

    # Near background layer
    for row in range(0, HEIGHT // tile_height + 2):
        for col in range(-1, WIDTH // tile_width + 2):
            color = (170, 210, 240)
            x = col * tile_width + bg_near_offset
            y = row * tile_height
            screen.draw.filled_rect(Rect((x, y), (tile_width, tile_height)), color)

def spawnGemOn(platform):
    gem = Actor('yellow_gem.png')
    gem.pos = platform.x, platform.y - platform.height
    gems.append(gem)

def spawnSpikeOn(platform):
    spike = Actor('spikes.png')
    spike.pos = platform.x, platform.y - spike.height + 5
    spikes.append(spike)

def generatePlatforms(count, start_x):
    new_platforms = []
    for i in range(count):
        platform_length = r(3, 6)
        y = r(int(HEIGHT / 2 + 20), int(HEIGHT - 100))

        if i == 0:
            y = HEIGHT / 2 + 100

        if not platforms or all(abs(y - p.y) > 64 for p in platforms):
            row = []
            for j in range(platform_length):
                tile = Actor('tile_green_05.png')
                tile.pos = start_x + (j * 64), y
                row.append(tile)
                new_platforms.append(tile)

            if row:
                gem_tile = r(0, len(row) - 1)
                spawnGemOn(row[gem_tile])
                if r(0, 2) == 0:
                    spike_tile = r(0, len(row) - 1)
                    if spike_tile != gem_tile:
                        spawnSpikeOn(row[spike_tile])

            start_x += (platform_length + r(1, 3)) * 64

    platforms.extend(new_platforms)

def movePlatforms():
    for platform in platforms[:]:
        platform.x -= PLATFORM_SPEED
        if platform.x < -64:
            platforms.remove(platform)

    for gem in gems[:]:
        gem.x -= PLATFORM_SPEED
        if gem.x < -64:
            gems.remove(gem)

    for spike in spikes[:]:
        spike.x -= PLATFORM_SPEED
        if spike.x < -64:
            spikes.remove(spike)

def updatePlayerYPos():
    player.Y_velocity = min(player.Y_velocity + GLOBAL_GRAVITY, MAX_FALL_SPEED)
    player.y += player.Y_velocity

    on_ground = False
    for platform in platforms:
        if collide(player, platform) and player.Y_velocity > 0:
            player.y = platform.top - player.height / 2
            player.Y_velocity = 0
            on_ground = True
            break

    if keyboard.space and on_ground:
        player.Y_velocity = -JUMP_POWER
        jump_sound.play()  # Play jump sound

def updatePlayerHPos():
    player.x += player.X_velocity
    if player.x < 0:
        player.x, player.X_velocity = 0, 0
    elif player.x > WIDTH:
        player.x, player.X_velocity = WIDTH, 0

def input():
    if keyboard.d:
        player.X_velocity += MOVE_SPEED
    elif keyboard.a:
        player.X_velocity -= MOVE_SPEED
    else:
        player.X_velocity *= H_GLIDE

    if abs(player.X_velocity) < 0.3:
        player.X_velocity = 0

    updatePlayerHPos()

def scoreUpdate():
    global SCORE
    for gem in gems[:]:
        if collide(gem, player):
            SCORE += 1
            gems.remove(gem)
            gem_collect_sound.play()  # Play gem collect sound

def checkDeath():
    global SCORE
    for spike in spikes:
        if collide(spike, player):
            death_sound.play()  # Play death sound
            update_high_score(SCORE)
            SCORE = 0
            resetPlayer()
            break

    if player.y > HEIGHT + player.height:
        death_sound.play()  # Play death sound when player falls off the screen
        update_high_score(SCORE)
        SCORE = 0
        resetPlayer()

def resetPlayer():
    global gems, spikes, platforms
    gems.clear()
    spikes.clear()
    platforms.clear()
    player.pos = WIDTH / 2, HEIGHT / 2
    player.X_velocity = 0
    player.Y_velocity = 0
    generatePlatforms(10, WIDTH / 4)

# === Game Loop ===
def draw():
    screen.clear()
    drawBackground()

    if not START:
        screen.draw.text("Press SPACE to Start", center=(WIDTH // 2, HEIGHT // 2), fontsize=40, color="black")
    else:
        player.draw()
        drawPlatforms()
        drawGems()
        drawSpikes()
        screen.draw.text(f"Score: {SCORE}", topleft=(10, 10), fontsize=30, color="black")
        screen.draw.text(f"High Score: {load_high_score()}", topleft=(10, 40), fontsize=24, color="black")

def update():
    global START, config
    config = Config.load()
    set_sound_volumes()  # Update the sound volume when config is loaded

    if not START:
        if keyboard.space:
            START = True
        return

    updatePlayerYPos()
    input()
    movePlatforms()
    scoreUpdate()
    checkDeath()

    if len(platforms) < MIN_PLATFORM_ON_SCREEN * 5:
        generatePlatforms(10, WIDTH)

generatePlatforms(10, WIDTH / 4)
player.y = platforms[0].y - player.height / 2
pgzrun.go()
