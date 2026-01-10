import os
import pygame

from api.io.Lightning.manager.Spritesheet import Spritesheet
from api.io.Lightning.utils.ConfigFile import OBJECTS_PATH, maze_coord_x, maze_coord_y


class Trap:
    def __init__(self, x, y, cell_size, maze_size):
        self.grid_x = x
        self.grid_y = y
        self.cell_size = cell_size
        self.maze_size = maze_size

        # Calculate base grid position (top-left of the cell)
        self.base_x = maze_coord_x + self.grid_x * self.cell_size
        self.base_y = maze_coord_y + self.grid_y * self.cell_size

        # Initialize defaults
        self.pixel_x = self.base_x
        self.target_y = self.base_y

        # Initialize State
        self.reset()

        # Load sprites and calculate centering
        self._load_sprites()

    def reset(self):
        """Resets the trap to its initial state."""
        self.is_triggered = False
        self.state = 'IDLE'
        self.block_y = -self.cell_size * 3  # Reset position well above screen
        self.eye_frame_index = 0
        self.eye_speed = 0.15

        # --- ANIMATION SPEEDS (INCREASED) ---
        self.fall_speed = 24   # Very fast fall to match sound impact
        self.break_frame_index = 0
        self.break_speed = 0.5 # Fast crumble animation

    def _load_sprites(self):
        """Load trap base, sparkle animation, and falling block"""
        # 1. Base Trap
        self.trap_base = pygame.image.load(
            os.path.join(OBJECTS_PATH, f'trap{self.maze_size}.png')
        )

        # 2. Sparkle Animation
        sparkle_sheet = Spritesheet(
            os.path.join(OBJECTS_PATH, f'trapsparkle{self.maze_size}.png')
        )
        sheet_width = sparkle_sheet.sheet.get_width() // 14
        sheet_height = sparkle_sheet.sheet.get_height()
        self.eye_frames = []
        for i in range(14):
            frame = sparkle_sheet.get_image(
                i * sheet_width, 0, sheet_width, sheet_height
            )
            self.eye_frames.append(frame)

        # 3. Block Animation
        self.block_frames = []
        try:
            block_sheet = Spritesheet(
                os.path.join(OBJECTS_PATH, f'block{self.maze_size}.gif')
            )

            total_w = block_sheet.sheet.get_width()
            total_h = block_sheet.sheet.get_height()

            cols = 16
            b_w = total_w // cols
            b_h = total_h

            for i in range(cols):
                self.block_frames.append(block_sheet.get_image(i * b_w, 0, b_w, b_h))

            # --- POSITION FIX: CENTER & BOTTOM ALIGN ---
            # 1. Center Horizontally: (Cell Width - Block Width) / 2
            # 2. Align Bottoms: Cell Height - Block Height
            # This ensures the 'feet' of the block sit on the floor of the tile.
            center_offset_x = (self.cell_size - b_w) // 2
            bottom_align_y = self.cell_size - b_h

            self.pixel_x = self.base_x + center_offset_x
            self.target_y = self.base_y + bottom_align_y

        except Exception as e:
            print(f"Error loading block sprites: {e}")
            self.pixel_x = self.base_x
            self.target_y = self.base_y

    def update(self):
        # 1. Idle Animation (Sparkle)
        if not self.is_triggered:
            self.eye_frame_index += self.eye_speed
            if self.eye_frame_index >= len(self.eye_frames):
                self.eye_frame_index = 0

        # 2. Falling Logic
        elif self.state == 'FALLING':
            if self.block_y < self.target_y:
                self.block_y += self.fall_speed
                if self.block_y >= self.target_y:
                    self.block_y = self.target_y
                    self.state = 'BREAKING'

        # 3. Breaking Logic
        elif self.state == 'BREAKING':
            self.break_frame_index += self.break_speed
            if self.break_frame_index >= len(self.block_frames):
                self.break_frame_index = len(self.block_frames) - 1
                self.state = 'FINISHED'

    def trigger(self):
        """Trigger the trap (called by GameUI)"""
        if not self.is_triggered:
            self.is_triggered = True
            self.state = 'FALLING'
            self.block_y = -self.cell_size * 3

    def is_finished(self):
        return self.state == 'FINISHED'

    def check_collision(self, entity_x, entity_y):
        """Check if entity is on trap position"""
        return entity_x == self.grid_x and entity_y == self.grid_y

    def draw(self, surface):
        """Draws the base trap and eyes (under player)"""
        # Draw base trap centered
        trap_x = self.base_x + (self.cell_size - self.trap_base.get_width()) // 2
        trap_y = self.base_y + (self.cell_size - self.trap_base.get_height()) // 2
        surface.blit(self.trap_base, (trap_x, trap_y))

        # Draw glowing eyes if not triggered
        if not self.is_triggered and len(self.eye_frames) > 0:
            frame = self.eye_frames[int(self.eye_frame_index) % len(self.eye_frames)]
            s_w = frame.get_width()
            s_h = frame.get_height()
            center_x = self.base_x + self.cell_size // 2
            center_y = self.base_y + self.cell_size // 2

            eye_offset_x = int(self.cell_size * 0.13)
            eye_offset_y = int(self.cell_size * 0.04)

            surface.blit(frame, (center_x - eye_offset_x - (s_w // 2), center_y - eye_offset_y - (s_h // 2)))
            surface.blit(frame, (center_x + eye_offset_x - (s_w // 2), center_y - eye_offset_y - (s_h // 2)))

    def draw_active_block(self, surface):
        """Draws the falling/breaking block (Called AFTER player is drawn)"""
        if not self.is_triggered or not self.block_frames:
            return

        img = None
        if self.state == 'FALLING':
            img = self.block_frames[0]
        elif self.state == 'BREAKING' or self.state == 'FINISHED':
            idx = int(self.break_frame_index)
            if idx < len(self.block_frames):
                img = self.block_frames[idx]

        if img:
            surface.blit(img, (self.pixel_x, self.block_y))