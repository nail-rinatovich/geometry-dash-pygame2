"""Headless verification of the project's real sprite physics; no database."""
import os
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
sys.dont_write_bytecode = True
sys.path.insert(0, os.environ.get("CHECK_SOURCE_DIR", os.path.dirname(os.path.dirname(__file__))))

import pygame
from player import Player
from obstacles import Spike

pygame.init()


def trial(count, lead, dt):
    player = Player(100, 300)
    for _ in range(180):
        player.update(dt)
    spikes = [Spike(500 + 40 * i, 500) for i in range(count)]
    jumped = False
    air_frames = 0
    for frame in range(600):
        if not jumped and spikes[0].rect.left - player.rect.right <= lead:
            player.jump()
            jumped = True
        player.update(dt)
        if jumped and not player.is_on_ground:
            air_frames += 1
        for spike in spikes:
            spike.update(dt, 360)
            if pygame.sprite.collide_mask(player, spike):
                return False, air_frames * dt
        if spikes[-1].rect.right < player.rect.left - 20:
            return True, air_frames * dt
    return False, air_frames * dt


def simulate(raw_objects, dts, duration):
    player = Player(100, 300)
    groups = []
    for obj in sorted(raw_objects, key=lambda obj: obj["x"]):
        if obj["type"] != "spike":
            raise ValueError("This verifier handles spike-only levels")
        spike = Spike(obj["x"], 500)
        if groups and obj["x"] - groups[-1][-1].rect.x <= 40:
            groups[-1].append(spike)
        else:
            groups.append([spike])
    spikes = [spike for group in groups for spike in group]
    jumped = set()
    frames = 0
    t = 0
    while t < duration:
        dt = min(dts[frames % len(dts)], duration - t)
        for i, group in enumerate(groups):
            if i in jumped:
                continue
            lead = {1: 90, 2: 70, 3: 50}.get(len(group), 30)
            if group[0].rect.left - player.rect.right <= lead and player.is_on_ground:
                player.jump()
                jumped.add(i)
                break
        player.update(dt)
        for spike in spikes:
            spike.update(dt, 360)
            if pygame.sprite.collide_mask(player, spike):
                return False, round(t + dt, 4), len(jumped)
        t += dt
        frames += 1
    remaining = sum(1 for spike in spikes if spike.rect.right >= player.rect.left)
    return True, round(t, 4), len(jumped), remaining


if len(sys.argv) > 1:
    import json
    with open(sys.argv[1], encoding="utf-8") as stream:
        data = json.load(stream)
    for dts in ([1 / 60], [0.016], [0.017], [1 / 30], [1 / 120], [0.016, 0.017], [0.015, 0.02, 0.018]):
        print("level", dts, simulate(data["objects"], dts, data.get("duration_seconds", 30)))
else:
    for dt in (1 / 60, 0.016, 0.017, 1 / 30, 1 / 120):
        for count in (1, 2, 3, 4):
            passing = [lead for lead in range(0, 221, 2) if trial(count, lead, dt)[0]]
            if passing:
                midpoint = passing[len(passing) // 2]
                print(f"dt={dt:.6f} count={count} lead={min(passing)}..{max(passing)} midpoint={midpoint} air_seconds={trial(count, midpoint, dt)[1]:.3f}")
            else:
                print(f"dt={dt:.6f} count={count} NONE")
    for count in (1, 2, 3):
        for spacing in (280, 320, 360, 400, 440):
            objects = [{"type": "spike", "x": 600 + spacing * i + 40 * j, "y": 500} for i in range(20) for j in range(count)]
            print("spacing", count, spacing, simulate(objects, [1 / 60], 30))

pygame.quit()
