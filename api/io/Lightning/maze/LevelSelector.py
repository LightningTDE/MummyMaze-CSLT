import random

class LevelSystem:
    def __init__(self):
        self.max_levels = 15  # Levels per pyramid
        self.current_level_num = 1  # Level within current pyramid (1-15)
        self.current_pyramid = 1  # Current pyramid number
        self.level_difficulties = {}

        # Generate the difficulty map immediately
        self.generate_pyramid_structure()
    
    def get_pyramid_from_absolute_level(self, absolute_level):
        """Calculate pyramid number from absolute level.
        
        Args:
            absolute_level (int): Absolute level number (1, 2, 3, ..., 16, 17, ...)
            
        Returns:
            int: Pyramid number
        """
        return ((absolute_level - 1) // 15) + 1
    
    def get_level_in_pyramid(self, absolute_level):
        """Calculate level within pyramid from absolute level.
        
        Args:
            absolute_level (int): Absolute level number
            
        Returns:
            int: Level within pyramid (1-15)
        """
        return ((absolute_level - 1) % 15) + 1
    
    def get_absolute_level(self):
        """Get absolute level number from pyramid and level.
        
        Returns:
            int: Absolute level number
        """
        return (self.current_pyramid - 1) * 15 + self.current_level_num

    def generate_pyramid_structure(self):
        """
        Pre-calculates difficulty for all 15 levels based on the rules.
        """
        self.level_difficulties.clear()

        # Weighted probabilities for levels 4-14
        options = ['easy', 'medium', 'hard']
        weights = [0.3, 0.5, 0.2]

        for level in range(1, self.max_levels + 1):
            if level <= 3:
                self.level_difficulties[level] = 'easy'
            elif level == 15:
                self.level_difficulties[level] = 'hard'
            else:
                # Random choice based on weights
                # k=1 returns a list, so we take [0]
                diff = random.choices(options, weights=weights, k=1)[0]
                self.level_difficulties[level] = diff

    def get_current_difficulty(self):
        """Returns the difficulty string for the current active level."""
        return self.level_difficulties.get(self.current_level_num, 'medium')

    def next_level(self):
        """Advances to the next level. Returns True if successful, False if pyramid complete."""
        if self.current_level_num < self.max_levels:
            self.current_level_num += 1
            return True
        else:
            # Pyramid complete, move to next pyramid
            self.current_pyramid += 1
            self.current_level_num = 1
            self.generate_pyramid_structure()
            return False  # Indicates pyramid completion

    def set_level(self, level_num):
        """Manually jumps to a level within current pyramid (useful for Map Screen)."""
        if 1 <= level_num <= self.max_levels:
            self.current_level_num = level_num
            return True
        return False
    
    def set_pyramid(self, pyramid):
        """Set the current pyramid.
        
        Args:
            pyramid (int): Pyramid number
        """
        self.current_pyramid = pyramid
        self.generate_pyramid_structure()
    
    def set_pyramid_and_level(self, pyramid, level):
        """Set both pyramid and level.
        
        Args:
            pyramid (int): Pyramid number
            level (int): Level number (1-15)
        """
        self.current_pyramid = pyramid
        self.current_level_num = level
        self.generate_pyramid_structure()

    def get_current_level(self):
        """Get current level within pyramid."""
        return self.current_level_num
    
    def get_current_pyramid(self):
        """Get current pyramid number."""
        return self.current_pyramid

    def reset_progress(self):
        """Reset to pyramid 1, level 1."""
        self.current_pyramid = 1
        self.current_level_num = 1
        self.generate_pyramid_structure()