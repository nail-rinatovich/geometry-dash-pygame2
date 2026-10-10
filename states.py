import pygame
from player import Player
from level_loader import LevelLoader
from obstacles import Spike, Block

class BaseState:
    def __init__(self, manager):
        self.manager = manager
        
    def handle_events(self, events): 
        print("[DEBUG] BaseState: handle_events вызван (пустая реализация)")
        pass
        
    def update(self, dt): 
        pass
        
    def draw(self, screen): 
        pass


class MainMenuState(BaseState):
    """Стартовый экран."""
    def __init__(self, manager):
        print("[DEBUG] MainMenuState: Инициализация")
        super().__init__(manager)
        self.font = pygame.font.SysFont(None, 40)
        self.title = self.font.render("GEOMETRY DASH PYGAME", True, (0, 255, 100))
        self.subtitle = self.font.render("Нажмите ПРОБЕЛ для входа в меню уровней", True, (255, 255, 255))
        self.progress_percent = 0

    # ИСПРАВЛЕНО: Метод вынесен на правильный уровень отступа (вне __init__)
    def handle_events(self, events):
        print(f"[DEBUG] MainMenuState: Получено событий: {len(events)}")
        for event in events:
            if event.type == pygame.KEYDOWN:
                print(f"[DEBUG] MainMenuState: Нажата клавиша. key={event.key}, scancode={getattr(event, 'scancode', 'N/A')}")
                
                # pygame.K_SPACE — это самый надежный способ отследить пробел в Pygame
                if event.key == pygame.K_SPACE:
                    print("[DEBUG] MainMenuState: Пробел успешно распознан! Переход в LevelSelectState")
                    self.manager.change_to(LevelSelectState)
                    return # Прерываем цикл, так как событие обработано

    def update(self, dt):
        pass

    def draw(self, screen):
        screen.fill((15, 15, 30))
        screen.blit(self.title, self.title.get_rect(center=(screen.get_width()//2, screen.get_height()//2 - 40)))
        screen.blit(self.subtitle, self.subtitle.get_rect(center=(screen.get_width()//2, screen.get_height()//2 + 20)))


class LevelSelectState(BaseState):
    """Экран выбора из 3 уровней."""
    def __init__(self, manager):
        print("[DEBUG] LevelSelectState: Инициализация")
        super().__init__(manager)
        self.font = pygame.font.SysFont(None, 36)
        
        self.levels = []
        for i in range(1, 4):
            attempts, best = self.manager.db.get_stats(i)
            self.levels.append({"id": i, "filename": f"level_{i}.json", "attempts": attempts, "best": best})

    # ИСПРАВЛЕНО: Метод вынесен на правильный уровень отступа
    def handle_events(self, events):
        print(f"[DEBUG] LevelSelectState: Получено событий: {len(events)}")
        for event in events:
            if event.type == pygame.KEYDOWN:
                print(f"[DEBUG] LevelSelectState: Нажата клавиша. key={event.key}, scancode={getattr(event, 'scancode', 'N/A')}")
                
                if event.key == pygame.K_1: 
                    print("[DEBUG] LevelSelectState: Выбран уровень 1")
                    self.start_level(1)
                elif event.key == pygame.K_2: 
                    print("[DEBUG] LevelSelectState: Выбран уровень 2")
                    self.start_level(2)
                elif event.key == pygame.K_3: 
                    print("[DEBUG] LevelSelectState: Выбран уровень 3")
                    self.start_level(3)
                elif event.key == pygame.K_ESCAPE: 
                    print("[DEBUG] LevelSelectState: Нажат ESC, возврат в главное меню")
                    self.manager.change_to(MainMenuState)

    def start_level(self, level_id):
        print(f"[DEBUG] LevelSelectState: Запуск уровня {level_id}")
        self.manager.current_level_id = level_id
        self.manager.change_to(GameState)

    def update(self, dt):
        pass

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
    """Игровой процесс с коллизией платформ."""
    def __init__(self, manager):
        print("[DEBUG] GameState: Инициализация")
        super().__init__(manager)
        
        self.progress_percent = 0
        self.level_id = getattr(manager, 'current_level_id', 1)
        self.floor_y = 500
        
        print(f"[DEBUG] GameState: Увеличение счетчика попыток для уровня {self.level_id}")
        self.manager.db.increment_attempt(self.level_id)
        self.attempts, _ = self.manager.db.get_stats(self.level_id)

        print(f"[DEBUG] GameState: Загрузка объектов уровня из level_{self.level_id}.json")
        self.level_name, self.level_speed, objects = LevelLoader.load_level(f"level_{self.level_id}.json", self.floor_y)
        
        self.obstacles = pygame.sprite.Group()
        self.obstacles.add(objects)
        
        self.player = Player(100, 300)
        self.distance_traveled = 0
        self.max_level_width = 2400 
        self.font = pygame.font.SysFont(None, 36)
        print("[DEBUG] GameState: Инициализация успешно завершена")

    def handle_events(self, events):
        print(f"[DEBUG] GameState: Получено событий: {len(events)}")
        for event in events:
            if event.type == pygame.KEYDOWN:
                print(f"[DEBUG] GameState: Нажата клавиша. key={event.key}")
                
                if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                    print("[DEBUG] GameState: Попытка прыжка")
                    self.player.jump()
                elif event.key == pygame.K_ESCAPE:
                    print("[DEBUG] GameState: Прерывание уровня, возврат в меню выбора")
                    self.manager.change_to(LevelSelectState)
                    
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                    print("[DEBUG] GameState: Клавиша прыжка отпущена")

    def update(self, dt):
        # Обновляем игрока (если в player.py метод update принимает dt, иначе оставьте просто self.player.update())
        try:
            self.player.update(dt)
        except TypeError:
            self.player.update()
            
        self.distance_traveled += self.level_speed
        if self.max_level_width > 0:
            self.progress_percent = min(100, int((self.distance_traveled / self.max_level_width) * 100))
            
        # Обновляем препятствия
        try:
            self.obstacles.update(dt, self.level_speed)
        except TypeError:
            self.obstacles.update()

    def draw(self, screen):
        screen.fill((15, 15, 30))
        
        # 1. Отрисовка препятствий (группа спрайтов имеет встроенный метод draw)
        self.obstacles.draw(screen)
        
        # 2. Универсальная отрисовка игрока
        if hasattr(self.player, 'image') and hasattr(self.player, 'rect'):
            # Стандартный способ для pygame.sprite.Sprite
            screen.blit(self.player.image, self.player.rect)
        elif hasattr(self.player, 'draw'):
            # Если вы все же добавили метод draw внутрь класса Player
            self.player.draw(screen)
        elif hasattr(self.player, 'rect'):
            # Заглушка: если есть только rect, рисуем зеленый квадрат, чтобы игра не падала
            pygame.draw.rect(screen, (0, 255, 100), self.player.rect)
        else:
            print("[ОШИБКА ОТРИСОВКИ] Не удалось найти способ отрисовать игрока. Проверьте player.py")

        # 3. Отрисовка интерфейса (UI)
        ui_text = self.font.render(f"Уровень: {self.level_name} | Попытка: {self.attempts} | Прогресс: {self.progress_percent}%", True, (255, 255, 255))
        screen.blit(ui_text, (20, 20))
        
        hint = self.font.render("ESC — Выход в меню", True, (150, 150, 150))
        screen.blit(hint, (20, screen.get_height() - 50))