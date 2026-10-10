import pygame

class Spike(pygame.sprite.Sprite):
    """Класс препятствия-шипа."""
    def __init__(self, x, floor_y):
        super().__init__()
        self.size = 40
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        points = [(0, self.size), (self.size // 2, 0), (self.size, self.size)]
        pygame.draw.polygon(self.image, (255, 50, 50), points)
        self.rect = self.image.get_rect(bottomleft=(x, floor_y))
        self.mask = pygame.mask.from_surface(self.image)

    def update(self, dt, speed):
        self.rect.x -= speed * dt
        if self.rect.right < 0:
            self.kill()


class Block(pygame.sprite.Sprite):
    """Класс твердого блока-платформы."""
    def __init__(self, x, y):
        super().__init__()
        self.size = 40
        self.image = pygame.Surface((self.size, self.size))
        self.image.fill((200, 200, 200)) # Серый цвет для блоков
        # Рисуем внутреннюю рамку
        pygame.draw.rect(self.image, (100, 100, 100), (0, 0, self.size, self.size), 2)
        
        # В JSON y указывает на верхнюю грань блока, если он стоит на полу,
        # либо на его точную высоту в воздухе.
        self.rect = self.image.get_rect(topleft=(x, y - self.size))
        
        # Маска для коллизий
        self.mask = pygame.mask.from_surface(self.image)

    def update(self, dt, speed):
        """Движение блока влево."""
        self.rect.x -= speed * dt
        if self.rect.right < 0:
            self.kill()
