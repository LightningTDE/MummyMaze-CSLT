import pygame

class UIFont:
    """
    UI Font system using pygame.font.SysFont for Login Screen and Leaderboard.
    Provides clean, readable text with outline support.
    """
    
    def __init__(self, font_name="arial", size=28, color=(255, 255, 255), hover_color=(255, 255, 0)):
        """
        Initialize UI font renderer.
        
        Args:
            font_name: Font family name
            size: Font size in pixels
            color: Default RGB color
            hover_color: RGB color for hovered elements
        """
        self.base_font = pygame.font.SysFont(font_name, size, bold=True)
        self.header_font = pygame.font.SysFont(font_name, int(size * 1.5), bold=True)
        self.color = color
        self.hover_color = hover_color

    def _create_text_surface(self, text, font, color, outline=True):
        """
        Create text surface with optional black outline.
        
        Args:
            text: String to render
            font: pygame.font.Font object
            color: RGB color tuple
            outline: Whether to add black outline
            
        Returns:
            pygame.Surface with rendered text
        """
        txt_surf = font.render(str(text), True, color)
        if not outline:
            return txt_surf
        
        # Create black outline by rendering text in 8 directions
        outline_surf = font.render(str(text), True, (0, 0, 0))
        w = txt_surf.get_width() + 4
        h = txt_surf.get_height() + 4
        final_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        
        # Draw outline
        for dx in range(3):
            for dy in range(3):
                if dx == 1 and dy == 1: 
                    continue
                final_surf.blit(outline_surf, (dx, dy))
        
        # Draw main text on top
        final_surf.blit(txt_surf, (1, 1))
        return final_surf

    def render_header(self, text, surface, x, y, color=None):
        """
        Render large header text centered at (x, y).
        
        Args:
            text: String to display
            surface: pygame.Surface to draw on
            x: X coordinate (center)
            y: Y coordinate (center)
            color: Optional color override (defaults to gold)
        """
        gold = color if color else (255, 215, 0)
        surf = self._create_text_surface(text, self.header_font, gold)
        rect = surf.get_rect(center=(x, y))
        surface.blit(surf, rect)

    def render_label(self, text, surface, x, y, color=None):
        """
        Render regular text centered at (x, y).
        
        Args:
            text: String to display
            surface: pygame.Surface to draw on
            x: X coordinate (center)
            y: Y coordinate (center)
            color: Optional color override
        """
        c = color if color else self.color
        surf = self._create_text_surface(text, self.base_font, c)
        rect = surf.get_rect(center=(x, y))
        surface.blit(surf, rect)

    def draw_button(self, surface, text, x, y, mouse_pos, clicked=False):
        """
        Draw interactive button with hover effect.
        
        Args:
            surface: pygame.Surface to draw on
            text: Button text
            x: X coordinate (center)
            y: Y coordinate (center)
            mouse_pos: Current mouse position tuple
            clicked: Whether mouse button is pressed
            
        Returns:
            True if button was clicked, False otherwise
        """
        # Calculate button rect
        temp_surf = self.base_font.render(str(text), True, self.color)
        rect = temp_surf.get_rect(center=(x, y))
        
        # Check hover state
        is_hovered = rect.collidepoint(mouse_pos)
        color = self.hover_color if is_hovered else self.color
        
        # Render final button
        final_surf = self._create_text_surface(text, self.base_font, color)
        draw_rect = final_surf.get_rect(center=(x, y))
        surface.blit(final_surf, draw_rect)
        
        # Update cursor and return click state
        if is_hovered:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
            return clicked
        return False
