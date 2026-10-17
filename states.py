import pygame
from player import Player
from level_loader import LevelLoader
from obstacles import Block, Spike

class MainMenuState:
    """Главное меню игры."""
    def __init__(self, manager):
        self.manager = manager
        self.font = pygame.font.SysFont("Arial", 40)
        self.title_font = pygame.font.SysFont("Arial", 60)
        
        # Кнопки: (текст, rect, действие)
        self.buttons = [
            ("Уровень 1", pygame.Rect(300, 200, 200, 50), 1),
            ("Уровень 2", pygame.Rect(300, 270, 200, 50), 2),
            ("Уровень 3", pygame.Rect(300, 340, 200, 50), 3),
            ("Уровень 4", pygame.Rect(300, 410, 200, 50), 4),
            ("Выход", pygame.Rect(300, 480, 200, 50), 0)
        ]

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                for text, rect, action in self.buttons:
                    if rect.collidepoint(mouse_pos):
                        if action == 0:
                            pygame.quit()
                            exit()
                        else:
                            # Запускаем игру с выбранным уровнем
                            self.manager.change_to(GameState)
                            self.manager.current_state.load_level(action)

    def update(self, dt):
        pass

    def draw(self, screen):
        screen.fill((30, 30, 50))
        
        # Заголовок
        title = self.title_font.render("Geometry Dash Clone", True, (255, 255, 255))
        screen.blit(title, (150, 50))
        
        # Кнопки
        for text, rect, _ in self.buttons:
            pygame.draw.rect(screen, (0, 150, 255), rect)
            pygame.draw.rect(screen, (255, 255, 255), rect, 2)
            label = self.font.render(text, True, (255, 255, 255))
            label_rect = label.get_rect(center=rect.center)
            screen.blit(label, label_rect)


class GameState:
    """Состояние самой игры."""
    def __init__(self, manager):
        self.manager = manager
        self.floor_y = 500
        self.player = Player(100, self.floor_y - 40)
        self.jump_held = False
        
        # Инициализируем переменные, чтобы избежать ошибки AttributeError
        self.obstacles = pygame.sprite.Group()
        self.speed = 0 
        self.level_name = ""
        self.max_distance = 0
        self.distance_traveled = 0
        self.is_playing = True
        
        # Фон
        self.bg_color = (20, 20, 40)

    def load_level(self, level_id):
        """Загружает уровень из JSON файла."""
        filename = f"level_{level_id}.json"
        name, speed, obstacles_list, duration_sec = LevelLoader.load_level(filename, self.floor_y)
        
        self.level_name = name
        self.speed = speed  # <--- ВОТ ЗДЕСЬ МЫ ПРИСВАИВАЕМ SPEED, ЧТОБЫ ОШИБКА ИСЧЕЗЛА
        self.max_distance = speed * duration_sec
        
        # Очищаем старые препятствия и добавляем новые
        self.obstacles.empty()
        for obj in obstacles_list:
            self.obstacles.add(obj)
            
        # Сброс игрока
        self.player = Player(100, self.floor_y - 40)
        self.jump_held = False
        self.distance_traveled = 0
        self.is_playing = True
        
        # Увеличиваем счетчик попыток в БД
        self.manager.db.increment_attempt(level_id)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                    if self.is_playing:
                        self.jump_held = True
                        self.player.jump()
            elif event.type == pygame.KEYUP:
                if event.key in (pygame.K_SPACE, pygame.K_UP):
                    self.jump_held = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if not self.is_playing:
                    # Возврат в меню при клике после смерти/победы
                    self.manager.change_to(MainMenuState)

    def update(self, dt):
        if not self.is_playing:
            return

        # Обновляем игрока
        self.player.update(dt)
        
        # Обновляем препятствия
        self.obstacles.update(dt, self.speed)
        
        # Двигаем камеру (увеличиваем пройденное расстояние)
        self.distance_traveled += self.speed * dt
        
        # === НОВАЯ ЛОГИКА: Коллизии с блоками ===
        blocks = [obj for obj in self.obstacles if isinstance(obj, Block)]
        if self.player.check_block_collisions(blocks):
            self.game_over()
            return

        # Удерживаемая кнопка автоматически запускает следующий прыжок
        # сразу после приземления на пол или на блок.
        if self.jump_held and self.player.is_on_ground:
            self.player.jump()

        # === Старая логика: Коллизии с шипами ===
        spikes = [obj for obj in self.obstacles if isinstance(obj, Spike)]
        for spike in spikes:
            if self.player.rect.colliderect(spike.rect):
                # Точная проверка по маске
                offset_x = int(spike.rect.x - self.player.rect.x)
                offset_y = int(spike.rect.y - self.player.rect.y)
                if self.player.mask.overlap(spike.mask, (offset_x, offset_y)):
                    self.game_over()
                    return

        # Проверка победы
        if self.distance_traveled >= self.max_distance:
            self.game_win()

    def game_over(self):
        self.is_playing = False
        progress = min(100, int((self.distance_traveled / self.max_distance) * 100))
        # Здесь можно определить ID уровня по имени, но для простоты пока просто выводим
        print(f"Game Over! Progress: {progress}%")
        # Сохраняем рекорд (нужно передать ID уровня, но пока упростим)
        # self.manager.db.save_record(...) 

    def game_win(self):
        self.is_playing = False
        print("Level Complete!")
        self.manager.db.save_record(1, 100) # Пример сохранения

    def draw(self, screen):
        screen.fill(self.bg_color)
        
        # Рисуем пол
        pygame.draw.line(screen, (255, 255, 255), (0, self.floor_y), (800, self.floor_y), 2)
        
        # Рисуем препятствия
        self.obstacles.draw(screen)
        
        # Рисуем игрока
        screen.blit(self.player.image, self.player.draw_rect)
        
        # UI: Прогресс
        font = pygame.font.SysFont("Arial", 20)
        progress = min(100, int((self.distance_traveled / self.max_distance) * 100))
        text = font.render(f"{self.level_name} | {progress}%", True, (255, 255, 255))
        screen.blit(text, (10, 10))
        
        if not self.is_playing:
            overlay = pygame.Surface((800, 600))
            overlay.set_alpha(128)
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))
            
            msg_font = pygame.font.SysFont("Arial", 50)
            msg = msg_font.render("Нажмите кнопку мыши для выхода в меню", True, (255, 255, 255))
            screen.blit(msg, (100, 250))
