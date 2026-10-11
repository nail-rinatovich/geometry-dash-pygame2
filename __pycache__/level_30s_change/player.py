import pygame

class Player(pygame.sprite.Sprite):
    """Класс игрока-кубика с анимацией вращения."""
    def __init__(self, x, y):
        super().__init__()
        self.size = 40
        # Базовая поверхность кубика
        self.base_image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self.base_image.fill((0, 255, 100))
        # Внутренняя рамка
        pygame.draw.rect(self.base_image, (0, 150, 50), (5, 5, 30, 30), 3)
        
        # ВАЖНО: Создаем маску для точных коллизий
        self.mask = pygame.mask.from_surface(self.base_image)
        
        self.image = self.base_image.copy()
        self.rect = self.image.get_rect(topleft=(x, y))
        
        self.velocity_y = 0
        self.gravity = 1600
        self.jump_force = -580
        self.is_on_ground = False
        self.floor_y = 500
        
        # Параметры вращения
        self.angle = 0
        self.rotation_speed = 360 

    def jump(self):
        if self.is_on_ground:
            self.velocity_y = self.jump_force
            self.is_on_ground = False

    def update(self, dt):
        if not self.is_on_ground:
            self.velocity_y += self.gravity * dt
            self.angle = (self.angle - self.rotation_speed * dt) % 360
        else:
            self.angle = round(self.angle / 90) * 90 % 360
            
        self.rect.y += self.velocity_y * dt
        
        # Проверка пола
        if self.rect.bottom >= self.floor_y:
            self.rect.bottom = self.floor_y
            self.velocity_y = 0
            self.is_on_ground = True
            
        self.rotate_sprite()

    def rotate_sprite(self):
        """Поворачивает изображение и обновляет маску коллизий."""
        old_center = self.rect.center
        self.image = pygame.transform.rotate(self.base_image, self.angle)
        self.rect = self.image.get_rect(center=old_center)
        # ВАЖНО: Обновляем маску после поворота, иначе коллизии будут работать криво
        self.mask = pygame.mask.from_surface(self.image)
