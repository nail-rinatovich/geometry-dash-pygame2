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
        names = ["1. Stereo Madness", "2. Back On Track", "3. Polargeist"]
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
        
        self.level_name, self.level_speed, objects = LevelLoader.load_level(f"level_{self.level_id}.json", self.floor_y)
        self.obstacles = pygame.sprite.Group()
        self.obstacles.add(objects)
        
        self.player = Player(100, 300)
        self.distance_traveled = 0
        self.max_level_width = 2400 
        self.font = pygame.font.SysFont(None, 36)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                    self.player.jump()
                elif event.key == pygame.K_ESCAPE:
                    self.manager.change_to(LevelSelectState)

    def update(self, dt):
        self.player.update(dt)
        
        # Двигаем уровень и считаем прогресс
        self.distance_traveled += self.level_speed * dt
        if self.max_level_width > 0:
            self.progress_percent = min(100, int((self.distance_traveled / self.max_level_width) * 100))
            
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
        
        hint = self.font.render("ESC — Выход в меню", True, (150, 150, 150))
        screen.blit(hint, (20, screen.get_height() - 50))
