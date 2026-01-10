import os
import json
from api.io.Lightning.utils.ConfigFile import SAVES_PATH


class SaveManager:
    """Manager for game save/load functionality."""
    
    @staticmethod
    def save_game(username, maze_data, current_state, level, total_time):
        """Save game state to file.
        
        Args:
            username (str): Username
            maze_data (dict): Original maze configuration
            current_state (dict): Current game state
            level (int): Current level number
            total_time (int): Total time elapsed in milliseconds
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not username:
            return False
        
        save_path = os.path.join(SAVES_PATH, f"{username}.json")
        
        # Create saves directory if it doesn't exist
        os.makedirs(SAVES_PATH, exist_ok=True)
        
        save_data = {
            "original_maze": maze_data,
            "current_state": current_state,
            "level": level,
            "total_time": total_time
        }
        
        try:
            with open(save_path, 'w') as f:
                json.dump(save_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving game: {e}")
            return False
    
    @staticmethod
    def load_game(username):
        """Load game state from file.
        
        Args:
            username (str): Username
            
        Returns:
            dict or None: Save data or None if error/not found
        """
        save_path = os.path.join(SAVES_PATH, f"{username}.json")
        
        if not os.path.exists(save_path):
            return None
        
        try:
            with open(save_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading game: {e}")
            return None
    
    @staticmethod
    def has_save(username):
        """Check if a save file exists for user.
        
        Args:
            username (str): Username
            
        Returns:
            bool: True if save exists, False otherwise
        """
        save_path = os.path.join(SAVES_PATH, f"{username}.json")
        return os.path.exists(save_path)
    
    @staticmethod
    def delete_save(username):
        """Delete save file for user.
        
        Args:
            username (str): Username
            
        Returns:
            bool: True if successful, False otherwise
        """
        save_path = os.path.join(SAVES_PATH, f"{username}.json")
        
        if not os.path.exists(save_path):
            return False
        
        try:
            os.remove(save_path)
            return True
        except Exception as e:
            print(f"Error deleting save: {e}")
            return False
