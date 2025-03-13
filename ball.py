import pygame

class Ball:
    def __init__(self, x, y, radius, color):
        self.radius = radius
        self.color = color
        # Use a Vector2 for float-based position
        self.pos = pygame.math.Vector2(x, y)
        self.rect = pygame.Rect(x - radius, y - radius, radius * 2, radius * 2)

    def update_rect(self):
        # Update rect position based on the float position
        self.rect.center = (int(self.pos.x), int(self.pos.y))

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.pos.x), int(self.pos.y)), self.radius)
