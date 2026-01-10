# ----------------------------------- Package ----------------------------------- #
import pygame
import os

from api.io.Lightning.utils.ConfigFile import UI_PATH
# ----------------------------------- Package ----------------------------------- #

class BaseFontRenderer:
    """
    Base class for all font renderers.  Handles common operations like:
    - Loading font sprite sheets
    - Creating glyph rectangles from character widths
    - Applying color transformations
    - Rendering text with configurable spacing
    """

    def __init__(self, image_filename, chars_order, widths, source_padding=0):
        """
        Initialize the font renderer.

        Args:
            image_filename:  Name of the sprite sheet file in UI_PATH
            chars_order:  String containing all characters in sprite sheet order
            widths: Dictionary mapping characters to their pixel widths
            source_padding:  Spacing between glyphs in the source image
        """
        # Load the original white sprite sheet
        self.original_image = pygame.image.load(os.path.join(UI_PATH, image_filename)).convert_alpha()
        self.original_image.set_colorkey((0, 0, 0))

        self.chars_order = chars_order
        self.widths = widths
        self.height = self.original_image.get_height()

        # Build glyph rectangles from the sprite sheet
        self.glyph_rects = self._build_glyph_rects(source_padding)

    def _build_glyph_rects(self, source_padding):
        """
        Parse the sprite sheet and create rectangles for each character glyph.

        Returns:
            Dictionary mapping characters to their pygame.Rect on the sprite sheet
        """
        glyph_rects = {}
        x = 0

        for ch in self.chars_order:
            w = self.widths.get(ch, 6)
            if x + w <= self.original_image.get_width():
                glyph_rects[ch] = pygame.Rect(x, 0, w, self.height)
            x += w + source_padding

        return glyph_rects

    def _apply_color(self, color):
        """
        Create a colored version of the font sprite sheet.

        Args:
            color: RGB tuple (r, g, b)

        Returns:
            Colored pygame.Surface
        """
        if color == (255, 255, 255):
            return self.original_image

        colored = self.original_image.copy()
        colored.fill(color[0:3], special_flags=pygame.BLEND_MULT)
        return colored

    def render(self, text, color=(255, 255, 255), letter_spacing=1, word_spacing=6):
        """
        Render text using this font.

        Args:
            text: String to render
            color: RGB tuple for text color
            letter_spacing: Pixels between characters
            word_spacing:  Pixels for space characters

        Returns:
            pygame.Surface containing the rendered text
        """
        # Calculate total width and collect valid characters
        total_width = 0
        valid_chars = []

        for ch in str(text):
            if ch == ' ':
                total_width += word_spacing
                valid_chars.append((' ', word_spacing))
            elif ch in self.glyph_rects:
                w = self.glyph_rects[ch].width
                total_width += w + letter_spacing
                valid_chars.append((ch, w))

        # Adjust for trailing letter spacing
        if total_width > 0:
            total_width -= letter_spacing

        # Handle empty or invalid text
        if total_width <= 0:
            return pygame.Surface((1, self.height), pygame.SRCALPHA)

        # Create output surface
        surf = pygame.Surface((total_width, self.height), pygame.SRCALPHA)
        source = self._apply_color(color)

        # Blit each character glyph
        x = 0
        for ch, w in valid_chars:
            if ch == ' ':
                x += w
            else:
                rect = self.glyph_rects[ch]
                surf.blit(source, (x, 0), area=rect)
                x += w + letter_spacing

        return surf


class HeaderText(BaseFontRenderer):
    """
    Large decorative font from headerfont.png.
    Supports uppercase, lowercase, numbers, and common symbols.
    """

    def __init__(self):
        chars_order = (
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "abcdefghijklmnopqrstuvwxyz"
            "0123456789"
            "!?.,@#$&*:-+'"
        )

        widths = {
            # Uppercase letters
            'A': 15, 'B': 15, 'C': 12, 'D': 15, 'E': 12, 'F': 13, 'G': 14, 'H': 14, 'I': 8, 'J': 9,
            'K': 14, 'L': 12, 'M': 18, 'N': 15, 'O': 16, 'P': 14, 'Q': 16, 'R': 16, 'S': 14, 'T': 13,
            'U': 16, 'V': 15, 'W': 21, 'X': 15, 'Y': 15, 'Z': 13,
            # Lowercase letters
            'a': 13, 'b': 13, 'c': 10, 'd': 14, 'e': 13, 'f': 10, 'g': 13, 'h': 13, 'i': 9, 'j': 8,
            'k': 14, 'l': 8, 'm': 20, 'n': 13, 'o': 12, 'p': 14, 'q': 13, 'r': 10, 's': 11, 't': 10,
            'u': 14, 'v': 14, 'w': 18, 'x': 13, 'y': 13, 'z': 12,
            # Numbers
            '0': 13, '1': 12, '2': 12, '3': 14, '4': 15, '5': 14, '6': 13, '7': 14, '8': 14, '9': 13,
            # Symbols
            '!': 9, '?': 10, ',': 7, '.': 6, '@': 20, '#': 18, '$': 12, '&': 17, '*': 8, ':': 8,
            '-': 8, '+': 21, "'": 10
        }

        super().__init__('headerfont.png', chars_order, widths, source_padding=0)

    def render(self, text, color=(255, 255, 255), letter_spacing=1):
        """Render text with header font (no word_spacing parameter)."""
        return super().render(text, color, letter_spacing, word_spacing=8)


class DefaultFont(BaseFontRenderer):
    """
    Small general-purpose font from font1.png.
    Supports uppercase, lowercase, numbers, and extended symbols.
    """

    def __init__(self):
        chars_order = (
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "abcdefghijklmnopqrstuvwxyz"
            "0123456789"
            "`!@#$%&*()+=\\/'\":?-.,"
        )

        widths = {
            # Uppercase letters
            'A': 12, 'B': 10, 'C': 13, 'D': 12, 'E': 10, 'F': 11, 'G': 12, 'H': 13, 'I': 6, 'J': 6,
            'K': 12, 'L': 10, 'M': 16, 'N': 13, 'O': 14, 'P': 10, 'Q': 14, 'R': 10, 'S': 10, 'T': 11,
            'U': 13, 'V': 14, 'W': 16, 'X': 12, 'Y': 12, 'Z': 11,
            # Lowercase letters
            'a': 6, 'b': 8, 'c': 7, 'd': 8, 'e': 7, 'f': 7, 'g': 7, 'h': 9, 'i': 5, 'j': 5,
            'k': 8, 'l': 6, 'm': 12, 'n': 9, 'o': 8, 'p': 8, 'q': 7, 'r': 6, 's': 7, 't': 5,
            'u': 8, 'v': 8, 'w': 11, 'x': 8, 'y': 8, 'z': 7,
            # Numbers
            '0': 9, '1': 5, '2': 7, '3': 8, '4': 8, '5': 8, '6': 9, '7': 7, '8': 9, '9': 7,
            # Symbols
            '`': 5, '!': 4, '@': 14, '#': 8, '$': 7, '%': 12, '&': 11, '*': 7, '(': 6, ')': 6,
            '+': 11, '=': 9, '\\': 10, '/': 10, "'": 4, '"': 5, ':': 4, '?': 6, '-': 5, '.': 7, ',': 5
        }

        super().__init__('font1.png', chars_order, widths, source_padding=0)


class PyramidFont(BaseFontRenderer):
    """
    Numeric-only font from pyramidfont.png.
    Supports digits 0-9 only.
    """

    def __init__(self):
        chars_order = "0123456789"
        widths = {"0": 6, "1": 5, "2": 6, "3": 6, "4": 6, "5": 6, "6": 6, "7": 6, "8": 6, "9": 6}
        super().__init__('pyramidfont.png', chars_order, widths, source_padding=1)

    def render(self, text, letter_spacing=1):
        """Render numeric text (uses white color only)."""
        return super().render(str(text), color=(255, 255, 255), letter_spacing=letter_spacing)


class CustomFont:
    """
    Main text rendering system combining multiple bitmap fonts.
    Used for in-game elements (WinState, MapTracker, etc.) that use biggestfont.gif.
    Provides color customization and hover effects.
    """

    def __init__(self, color=(255, 255, 255), hover_color=(255, 255, 0)):
        """
        Initialize the custom font with default colors.

        Args:
            color: Default RGB color for text
            hover_color: RGB color for hovered text
        """
        self.color = color
        self.hover_color = hover_color

        # Load the big display font (biggestfont.gif)
        self._load_biggest_font()

        # Initialize helper fonts
        self.pyramid_font = PyramidFont()
        self.default_font = DefaultFont()
        self.header_font = HeaderText()

    def _load_biggest_font(self):
        """
        Load and prepare the large display font (biggestfont.gif).
        Creates both normal and hover-colored versions with individual glyphs.
        """
        # Load original white bitmap
        self.original_image = pygame.image.load(os.path.join(UI_PATH, 'biggestfont.gif')).convert_alpha()
        self.original_image.set_colorkey((0, 0, 0))

        # Create colored versions
        self.image = self._create_colored_version(self.color)
        self.hover_image = self._create_colored_version(self.hover_color)

        # Define character layout
        self.letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        widths = {
            "A": 16, "B": 14, "C": 11, "D": 15, "E": 12, "F": 11, "G": 15, "H": 15,
            "I": 6, "J": 7, "K": 14, "L": 10, "M": 19, "N": 16, "O": 16, "P": 15,
            "Q": 17, "R": 15, "S": 13, "T": 12, "U": 16, "V": 15, "W": 23, "X": 15,
            "Y": 16, "Z": 12
        }
        spacings = [4, 4, 3, 4, 4, 3, 3, 3, 3, 4, 4, 4, 3, 3, 4, 3, 4, 4, 4, 4, 4, 4, 4, 3, 4]

        # Extract individual glyphs for both normal and hover states
        self.glyphs = self._extract_glyphs(self.image, widths, spacings)
        self.hover_glyphs = self._extract_glyphs(self.hover_image, widths, spacings)

    def _create_colored_version(self, color):
        """
        Create a colored copy of the original font image.

        Args:
            color: RGB tuple for the desired color

        Returns:
            Colored pygame.Surface
        """
        colored = self.original_image.copy()
        if color != (255, 255, 255):
            colored.fill(color[0:3], special_flags=pygame.BLEND_MULT)
        return colored

    def _extract_glyphs(self, source_image, widths, spacings):
        """
        Extract individual character glyphs from a sprite sheet.

        Args:
            source_image: Source sprite sheet
            widths: Dictionary of character widths
            spacings:  List of spacing values between characters

        Returns:
            Dictionary mapping characters to their glyph surfaces
        """
        glyphs = {}
        x = 0
        height = source_image.get_height()

        for i, ch in enumerate(self.letters):
            w = widths[ch]
            rect = pygame.Rect(x, 0, w, height)
            glyphs[ch] = source_image.subsurface(rect).copy()

            # Add spacing for next character
            if i < len(spacings):
                x += w + spacings[i]
            else:
                x += w

        return glyphs

    def render(self, text, letter_spacing=2, word_spacing=12, outline=True, outline_thickness=2, hovered=False):
        """
        Render large display text with optional outline.

        Args:
            text: String to render (converted to uppercase)
            letter_spacing:  Pixels between characters
            word_spacing: Pixels for space characters
            outline: Whether to add black outline
            outline_thickness:  Thickness of outline in pixels
            hovered: Use hover color if True

        Returns:
            pygame.Surface containing the rendered text
        """
        text = text.upper()
        height = self.original_image.get_height()

        # Choose glyphs based on hover state
        glyphs = self.hover_glyphs if hovered else self.glyphs

        # Calculate required surface width
        width = self._calculate_text_width(text, glyphs, letter_spacing, word_spacing)

        # Create base text surface
        base_surf = self._render_base_text(text, glyphs, width, height, letter_spacing, word_spacing)

        # Add outline if requested
        if outline:
            return self._add_outline(base_surf, outline_thickness)

        return base_surf

    def _calculate_text_width(self, text, glyphs, letter_spacing, word_spacing):
        """Calculate the total width needed for the text."""
        width = 0
        for ch in text:
            if ch == " ":
                width += word_spacing
            elif ch in glyphs:
                width += glyphs[ch].get_width() + letter_spacing

        # Remove trailing letter spacing
        return max(0, width - letter_spacing)

    def _render_base_text(self, text, glyphs, width, height, letter_spacing, word_spacing):
        """Render the base text without outline."""
        surf = pygame.Surface((width, height), pygame.SRCALPHA)
        x = 0

        for ch in text:
            if ch == " ":
                x += word_spacing
            elif ch in glyphs:
                glyph = glyphs[ch]
                surf.blit(glyph, (x, 0))
                x += glyph.get_width() + letter_spacing

        return surf

    def _add_outline(self, base_surf, thickness):
        """
        Add a black outline around the text.

        Args:
            base_surf: Base text surface
            thickness: Outline thickness in pixels

        Returns:
            New surface with outlined text
        """
        width, height = base_surf.get_size()
        padded_width = width + thickness * 2
        padded_height = height + thickness * 2
        final_surf = pygame.Surface((padded_width, padded_height), pygame.SRCALPHA)

        # Create black silhouette of the text
        black_surf = self._create_black_silhouette(base_surf, width, height)

        # Draw outline by blitting black version with offsets
        offsets = [
            (-1, -1), (0, -1), (1, -1),
            (-1, 0), (1, 0),
            (-1, 1), (0, 1), (1, 1)
        ]

        for dx, dy in offsets:
            for layer in range(thickness):
                final_surf.blit(black_surf,
                                (thickness + dx * (layer + 1), thickness + dy * (layer + 1)))

        # Draw colored text on top
        final_surf.blit(base_surf, (thickness, thickness))

        return final_surf

    def _create_black_silhouette(self, source_surf, width, height):
        """Create a black version of the text (preserving alpha)."""
        black_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        for x in range(width):
            for y in range(height):
                pixel = source_surf.get_at((x, y))
                if pixel.a > 0:
                    black_surf.set_at((x, y), (0, 0, 0, pixel.a))
        return black_surf

    # Convenience methods for rendering with different fonts

    def render_header(self, text, color=None, letter_spacing=1):
        """
        Render text using HeaderText font.

        Args:
            text: String to render
            color: RGB color (uses instance color if None)
            letter_spacing: Pixels between characters
        """
        use_color = color if color is not None else self.color
        return self.header_font.render(text, use_color, letter_spacing)

    def render_pyramid(self, text, letter_spacing=1):
        """
        Render numeric text using PyramidFont.

        Args:
            text:  Numeric string to render
            letter_spacing: Pixels between characters
        """
        return self.pyramid_font.render(text, letter_spacing)

    def render_default(self, text, color=None, letter_spacing=1, word_spacing=6):
        """
        Render text using DefaultFont (small general-purpose font).

        Args:
            text: String to render
            color: RGB color (uses instance color if None)
            letter_spacing: Pixels between characters
            word_spacing: Pixels for space characters
        """
        use_color = color if color is not None else self.color
        return self.default_font.render(text, use_color, letter_spacing, word_spacing)