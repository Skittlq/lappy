import pygame

class PhysicsEngine:
    def __init__(self, obj, mass=1.0, friction=0.1, gravity=(0, 0.5), restitution=0.8, **kwargs):
        """
        Wrap a Pygame object with physics properties.
        
        Parameters:
            obj (object): A Pygame object that must have a 'rect' attribute.
            mass (float): The mass of the object.
            friction (float): The friction coefficient (applied each frame).
            gravity (tuple): A tuple representing gravity vector.
            restitution (float): Bounciness factor (for collisions).
            kwargs: Additional custom parameters.
        """
        self.obj = obj
        self.mass = mass
        self.friction = friction
        self.gravity = pygame.math.Vector2(gravity)
        self.velocity = pygame.math.Vector2(0, 0)
        self.acceleration = pygame.math.Vector2(0, 0)
        self.restitution = restitution
        # Allow for additional customization through kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)

    def apply_force(self, force):
        """
        Apply an external force to the object.
        
        Args:
            force (tuple or pygame.math.Vector2): The force vector to apply.
        """
        # Newton's second law: F = m * a  ->  a = F / m
        self.acceleration += pygame.math.Vector2(force) / self.mass

    def update(self, dt, boundaries=None):
        """
        Update the physics state.
        
        Parameters:
            dt (float): Delta time (time step) since the last update.
            boundaries (pygame.Rect): Optional. The boundary within which the object must remain.
        """
        # Apply gravity force
        self.apply_force(self.gravity * self.mass)
        
        # Update velocity based on accumulated acceleration
        self.velocity += self.acceleration * dt
        
        # Apply friction as a damping factor
        self.velocity *= (1 - self.friction * dt)
        
        # Update the object's position based on velocity
        self.obj.rect.x += self.velocity.x * dt
        self.obj.rect.y += self.velocity.y * dt
        
        # Reset acceleration for the next frame
        self.acceleration = pygame.math.Vector2(0, 0)

        # Handle simple boundary collisions if a boundaries rect is provided
        if boundaries:
            if self.obj.rect.left < boundaries.left:
                self.obj.rect.left = boundaries.left
                self.velocity.x = -self.velocity.x * self.restitution
            if self.obj.rect.right > boundaries.right:
                self.obj.rect.right = boundaries.right
                self.velocity.x = -self.velocity.x * self.restitution
            if self.obj.rect.top < boundaries.top:
                self.obj.rect.top = boundaries.top
                self.velocity.y = -self.velocity.y * self.restitution
            if self.obj.rect.bottom > boundaries.bottom:
                self.obj.rect.bottom = boundaries.bottom
                self.velocity.y = -self.velocity.y * self.restitution
