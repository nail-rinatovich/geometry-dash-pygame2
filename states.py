import pygame
from player import Player
from level_loader import LevelLoader
from obstacles import Spike, Block

class BaseState:
    def __init__(self, manager):
        self.manager = manager
    def handle_events(self, events): pass
    def update(self, dt): pass
    def draw(self, screen): pass

class MainMenuState(BaseState):
    def __init__(self, manager):
        super().__init__(manager)
        self.font = pygame.font.SysFont(None, 40)
        self.title = self.font.render("GEOMETRY DASH PYGAME", True, (0, 255, 100))
        self.subtitle = self.font.render("Нажмите ПРОБЕЛ для входа в меню уровней", True, (255, 255, 255))
        self.progress_percent = 0

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.manager.change_to(LevelSelectState)
                    return

    def draw(self, screen):
        screen.fill((15, 15, 30))
        screen.blit(self.title, self.title.get_rect(center=(screen.get_width()//2, screen.get_height()//2 - 40)))
        screen.blit(self.subtitle, self.subtitle.get_rect(center=(screen.get_width()//2, screen.get_height()//2 + 20)))

class LevelSelectState(BaseState):
    def __init__(self, manager):
        super().__init__(manager)
        self.font = pygame.font.SysFont(None, 36)
        self.levels = []
        for i in range(1, 4):
            attempts, best = self.manager.db.get_stats(i)
            self.levels.append({"id": i, "filename": f"level_{i}.json", "attempts": attempts, "best": best})

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1: self.start_level(1)
                elif event.key == pygame.K_2: self.start_level(2)
                elif event.key == pygame.K_3: self.start_level(3)
                elif event.key == pygame.K_ESCAPE: self.manager.change_to(MainMenuState)

    def start_level(self, level_id):
        self.manager.current_level_id = level_id
        self.manager.change_to(GameState)

    def draw(self, screen):
        screen.fill((25, 20, 40))
        title = self.font.render("ВЫБОР УРОВНЯ (Нажмите цифру 1, 2 или 3):", True, (255, 255, 255))
        screen.blit(title, (50, 50))
        y_offset = 150
        names = ["1. Stereo Madness (30 сек)", "2. Back On Track", "3. Polargeist"]
        for lvl in self.levels:
            txt = self.font.render(f"{names[lvl['id']-1]} | Рекорд: {lvl['best']}% | Попыток: {lvl['attempts']}", True, (230, 230, 230))
            screen.blit(txt, (50, y_offset))
            y_offset += 80
        hint = self.font.render("ESC — Вернуться назад", True, (150, 150, 150))
        screen.blit(hint, (50, 500))

class GameState(BaseState):
    def __init__(self, manager):
        super().__init__(manager)
        self.progress_percent = 0
        self.level_id = getattr(manager, 'current_level_id', 1)
        self.floor_y = 500
        
        self.manager.db.increment_attempt(self.level_id)
        self.attempts, _ = self.manager.db.get_stats(self.level_id)
        
        self.level_name, self.level_speed, objects, self.level_duration = LevelLoader.load_level(f"level_{self.level_id}.json", self.floor_y)
        self.obstacles = pygame.sprite.Group()
        self.obstacles.add(objects)
        
        self.player = Player(100, 300)
        self.elapsed_time = 0
        self.level_complete = False
        self.distance_traveled = 0
        self.max_level_width = self.level_speed * self.level_duration
        self.font = pygame.font.SysFont(None, 36)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                    if self.level_complete:
                        self.manager.change_to(GameState)
                        return
                    self.player.jump()
                elif event.key == pygame.K_ESCAPE:
                    self.manager.change_to(LevelSelectState)
                    return

    def update(self, dt):
        if self.level_complete:
            return

        dt = min(dt, self.level_duration - self.elapsed_time)
        self.player.update(dt)
        
        # Двигаем уровень и считаем прогресс
        self.elapsed_time += dt
        if self.elapsed_time >= self.level_duration - 1e-9:
            self.elapsed_time = self.level_duration
        self.distance_traveled = self.level_speed * self.elapsed_time
        if self.max_level_width > 0:
            self.progress_percent = min(99, int((self.distance_traveled / self.max_level_width) * 100 + 1e-9))
            
        self.obstacles.update(dt, self.level_speed)
        
        # === ПРОВЕРКА СТОЛКНОВЕНИЙ (СМЕРТЬ) ===
        for obstacle in self.obstacles:
            # collide_mask проверяет точное пересечение пикселей (учитывает треугольную форму шипов)
            if pygame.sprite.collide_mask(self.player, obstacle):
                print(f"[DEBUG] СТОЛКНОВЕНИЕ! Игрок врезался в {type(obstacle).__name__}")
                self.manager.db.save_record(self.level_id, self.progress_percent)
                # Перезапуск уровня
                self.manager.change_to(GameState)
                return

        if self.elapsed_time >= self.level_duration:
            self.level_complete = True
            self.progress_percent = 100
            self.manager.db.save_record(self.level_id, 100)

    def draw(self, screen):
        screen.fill((15, 15, 30))
        
        # === ОТРИСОВКА ПОЛА ===
        # Темный фон под полом
        pygame.draw.rect(screen, (10, 10, 25), (0, self.floor_y, 800, 600 - self.floor_y))
        # Яркая линия пола
        pygame.draw.line(screen, (0, 255, 100), (0, self.floor_y), (800, self.floor_y), 4)
        
        # Отрисовка препятствий
        self.obstacles.draw(screen)
        
        # Отрисовка игрока
        if hasattr(self.player, 'image') and hasattr(self.player, 'rect'):
            screen.blit(self.player.image, self.player.rect)
            
        # Отрисовка UI
        ui_text = self.font.render(f"Уровень: {self.level_name} | Попытка: {self.attempts} | Прогресс: {self.progress_percent}%", True, (255, 255, 255))
        screen.blit(ui_text, (20, 20))

        time_text = self.font.render(f"Время: {self.elapsed_time:.1f} / {self.level_duration:g} сек", True, (200, 200, 200))
        screen.blit(time_text, (20, 55))
        
        hint = self.font.render("ESC — Выход в меню", True, (150, 150, 150))
        screen.blit(hint, (20, screen.get_height() - 50))

        if self.level_complete:
            overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 190))
            screen.blit(overlay, (0, 0))
            messages = [
                ("УРОВЕНЬ ПРОЙДЕН!", (0, 255, 100)),
                (f"100% — {self.level_duration:g} секунд", (255, 255, 255)),
                ("ПРОБЕЛ — повторить | ESC — меню", (200, 200, 200)),
            ]
            for index, (message, color) in enumerate(messages):
                text = self.font.render(message, True, color)
                screen.blit(text, text.get_rect(center=(screen.get_width() // 2, 240 + index * 50)))
