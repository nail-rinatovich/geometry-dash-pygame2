import json
import os
from pathlib import Path

os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

import pygame
from level_loader import LevelLoader
from obstacles import Spike, Block
from states import GameState, LevelSelectState


class MemoryDB:
    def __init__(self):
        self.attempts = 0
        self.records = []

    def increment_attempt(self, level_id):
        self.attempts += 1

    def get_stats(self, level_id):
        return self.attempts, max(self.records, default=0)

    def save_record(self, level_id, progress):
        self.records.append(progress)


class Manager:
    current_level_id = 1

    def __init__(self):
        self.db = MemoryDB()
        self.current_state = GameState(self)

    def change_to(self, state_class):
        self.current_state = state_class(self)


pygame.init()
screen = pygame.display.set_mode((800, 600))
level = json.loads(Path('level_1.json').read_text(encoding='utf-8'))
assert level['duration_seconds'] == 30
assert level['speed'] * level['duration_seconds'] == 10800
assert max(item['x'] + 40 for item in level['objects']) < 10800

# Timing, persistence, and frozen completion state across frame rates.
for fps in (30, 60, 144):
    manager = Manager()
    state = manager.current_state
    state.obstacles.empty()
    for frame in range(30 * fps):
        if frame == 15 * fps:
            assert state.progress_percent == 50
        state.update(1 / fps)
        if frame < 30 * fps - 1:
            assert not state.level_complete
    assert state.level_complete
    assert state.elapsed_time == 30
    assert state.distance_traveled == 10800
    assert state.progress_percent == 100
    assert manager.db.records == [100]
    state.update(10)
    assert manager.db.records == [100]
    assert state.elapsed_time == 30
    state.draw(screen)
    if fps == 60:
        pygame.image.save(screen, 'level_complete.png')
    state.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)])
    assert isinstance(manager.current_state, GameState)
    assert manager.current_state.elapsed_time == 0
    assert manager.db.attempts == 2

# Variable frame times also stop at the exact configured duration.
manager = Manager()
state = manager.current_state
state.obstacles.empty()
frames = 0
while not state.level_complete:
    state.update((0.016, 0.017, 0.015, 0.022)[frames % 4])
    frames += 1
assert state.elapsed_time == 30
assert manager.db.records == [100]
state.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)])
assert isinstance(manager.current_state, LevelSelectState)

# Collisions still restart an attempt and save the achieved progress.
manager = Manager()
state = manager.current_state
state.obstacles.empty()
state.elapsed_time = 12
spike = Spike(100, 500)
state.player.rect.bottom = 500
state.player.is_on_ground = True
state.obstacles.add(spike)
state.update(0)
assert manager.current_state is not state
assert manager.db.records == [40]
assert manager.db.attempts == 2

# Fractional movement must agree with the level's elapsed time.
for obstacle_type in (Spike, Block):
    obstacle = obstacle_type(12000, 500)
    for frame in range(30 * 144):
        obstacle.update(1 / 144, 360)
    assert obstacle.rect.x == 1200

# Play the entire real layout using mask collisions and timed jumps.
for fps in (30, 60, 144):
    manager = Manager()
    state = manager.current_state
    for frame in range(30 * fps):
        upcoming = [item for item in state.obstacles if item.rect.right >= state.player.rect.left]
        if upcoming and state.player.is_on_ground:
            nearest = min(upcoming, key=lambda item: item.rect.left)
            if nearest.rect.left - state.player.rect.right <= 70:
                state.player.jump()
        state.update(1 / fps)
        assert manager.current_state is state, 'Collision at {} FPS, {:.3f}s'.format(fps, state.elapsed_time)
        if fps == 60 and frame == 720:
            state.draw(screen)
            pygame.image.save(screen, 'level_playing.png')
    assert state.level_complete
    assert manager.db.records == [100]

# Levels without explicit duration retain their existing 2400-pixel length.
original_dir = Path(os.path.abspath(__file__)).parents[2]
for level_id in (2, 3):
    _, speed, _, duration = LevelLoader.load_level(str(original_dir / ('level_{}.json'.format(level_id))), 500)
    assert abs(speed * duration - 2400) < 1e-9

pygame.quit()
print('PASS: 30-second finish at 30/60/144 FPS, full playable layout, variable dt, restart/menu, record saving, and other level lengths.')
