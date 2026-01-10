import os
import json
import hashlib
from datetime import datetime
from api.io.Lightning.utils.ConfigFile import USERDATA_PATH, SAVES_PATH, LEADERBOARD_PATH


class StorageManager:
    """Unified manager for user profiles, saves, and leaderboard.
    
    This class provides a centralized interface for all storage operations
    including user authentication, profile management, game saves, and leaderboard.
    """
    
    def __init__(self):
        """Initialize the storage manager and ensure directories exist."""
        self.current_user = None
        self.current_profile = None
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create necessary directories if they don't exist."""
        os.makedirs(USERDATA_PATH, exist_ok=True)
        os.makedirs(SAVES_PATH, exist_ok=True)
        os.makedirs(LEADERBOARD_PATH, exist_ok=True)
    
    # ============= User Authentication =============
    
    @staticmethod
    def hash_password(password):
        """Hash password using SHA256.
        
        Args:
            password (str): Plain text password
            
        Returns:
            str: SHA256 hash of the password
        """
        return hashlib.sha256(password.encode()).hexdigest()
    
    def register_user(self, username, password):
        """Register a new user.
        
        Args:
            username (str): Username (must be >= 3 characters, alphanumeric)
            password (str): Password (must be >= 4 characters, alphanumeric)
            
        Returns:
            tuple: (success: bool, message: str)
        """
        # Validate username length
        if len(username) < 3:
            return False, "USERNAME TOO SHORT"
        
        # Validate password length
        if len(password) < 4:
            return False, "PASSWORD TOO SHORT"
        
        # Validate alphanumeric (allow underscore and hyphen for flexibility)
        if not username.replace('_', '').replace('-', '').isalnum():
            return False, "USERNAME INVALID"
        
        # Check if username already exists
        profile_path = os.path.join(USERDATA_PATH, f"{username}.json")
        if os.path.exists(profile_path):
            return False, "USERNAME EXISTS"
        
        # Create profile data
        profile_data = {
            "username": username,
            "password_hash": self.hash_password(password),
            "display_name": username,
            "pyramid": 1,
            "level": 1,
            "total_time": 0,
            "options": {
                "music_volume": 0.5,
                "sfx_volume": 0.5,
                "show_ankh": True
            },
            "created_at": datetime.now().isoformat(),
            "last_login": datetime.now().isoformat()
        }
        
        # Save profile
        try:
            # Atomic write using temp file
            temp_path = profile_path + ".tmp"
            with open(temp_path, 'w') as f:
                json.dump(profile_data, f, indent=2)
            os.replace(temp_path, profile_path)
            return True, "success"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def authenticate(self, username, password):
        """Authenticate user credentials.
        
        Args:
            username (str): Username
            password (str): Password
            
        Returns:
            tuple: (success: bool, message: str)
        """
        if not username or not password:
            return False, "MISSING INFO"
        
        profile_path = os.path.join(USERDATA_PATH, f"{username}.json")
        
        # Check if profile exists
        if not os.path.exists(profile_path):
            return False, "USER NOT FOUND"
        
        # Load profile and verify password
        try:
            with open(profile_path, 'r') as f:
                profile_data = json.load(f)
            
            password_hash = self.hash_password(password)
            if profile_data.get("password_hash") == password_hash:
                # Update last login
                profile_data["last_login"] = datetime.now().isoformat()
                self._save_profile_data(username, profile_data)
                
                # Set current user
                self.current_user = username
                self.current_profile = profile_data
                return True, "success"
            else:
                return False, "WRONG PASSWORD"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def logout(self):
        """Log out the current user."""
        self.current_user = None
        self.current_profile = None
    
    # ============= Profile Management =============
    
    def load_profile(self, username=None):
        """Load user profile data.
        
        Args:
            username (str, optional): Username to load. Uses current_user if None.
            
        Returns:
            dict or None: Profile data or None if error
        """
        if username is None:
            username = self.current_user
        
        if not username:
            return None
        
        profile_path = os.path.join(USERDATA_PATH, f"{username}.json")
        
        if not os.path.exists(profile_path):
            return None
        
        try:
            with open(profile_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading profile: {e}")
            return None
    
    def _save_profile_data(self, username, profile_data):
        """Internal method to save profile data atomically.
        
        Args:
            username (str): Username
            profile_data (dict): Profile data to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        profile_path = os.path.join(USERDATA_PATH, f"{username}.json")
        
        try:
            # Atomic write using temp file
            temp_path = profile_path + ".tmp"
            with open(temp_path, 'w') as f:
                json.dump(profile_data, f, indent=2)
            os.replace(temp_path, profile_path)
            return True
        except Exception as e:
            print(f"Error saving profile: {e}")
            return False
    
    def update_profile(self, updates):
        """Update current user's profile.
        
        Args:
            updates (dict): Dictionary of fields to update
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.current_user or not self.current_profile:
            return False
        
        # Update in-memory profile
        self.current_profile.update(updates)
        
        # Save to disk
        return self._save_profile_data(self.current_user, self.current_profile)
    
    def update_progression(self, pyramid, level):
        """Update user's pyramid and level progression.
        
        Args:
            pyramid (int): Pyramid number
            level (int): Level number
            
        Returns:
            bool: True if successful
        """
        return self.update_profile({"pyramid": pyramid, "level": level})
    
    def update_options(self, options):
        """Update user's game options.
        
        Args:
            options (dict): Options dictionary
            
        Returns:
            bool: True if successful
        """
        if not self.current_profile:
            return False
        
        if "options" not in self.current_profile:
            self.current_profile["options"] = {}
        
        self.current_profile["options"].update(options)
        return self._save_profile_data(self.current_user, self.current_profile)
    
    def update_option(self, key, value):
        """Update a single option and save to profile.
        
        Args:
            key: Option key (e.g., 'music_volume', 'sfx_volume', 'show_ankh')
            value: Option value
            
        Returns:
            bool: True if successful
        """
        if not self.current_user or not self.current_profile:
            return False
        
        if 'options' not in self.current_profile:
            self.current_profile['options'] = {}
        
        self.current_profile['options'][key] = value
        return self._save_profile_data(self.current_user, self.current_profile)
    
    # ============= Save/Load System =============
    
    def save_game(self, level_data, current_state, level_time, total_time, pyramid=None, level=None):
        """Save current game state.
        
        Args:
            level_data (dict): Original maze/level data
            current_state (dict): Current game state
            level_time (int): Time spent on current level (ms)
            total_time (int): Total time across all levels (ms)
            pyramid (int, optional): Current pyramid number (defaults to profile value)
            level (int, optional): Current level number (defaults to profile value)
            
        Returns:
            bool: True if successful
        """
        if not self.current_user or not self.current_profile:
            return False
        
        # Use provided pyramid/level or fall back to profile values
        if pyramid is None:
            pyramid = self.current_profile.get("pyramid", 1)
        if level is None:
            level = self.current_profile.get("level", 1)
        
        save_data = {
            "username": self.current_user,
            "pyramid": pyramid,
            "level": level,
            "level_time": level_time,
            "total_time": total_time,
            "original_maze": level_data,
            "current_state": current_state,
            "saved_at": datetime.now().isoformat()
        }
        
        save_path = os.path.join(SAVES_PATH, f"{self.current_user}.json")
        
        try:
            # Atomic write using temp file
            temp_path = save_path + ".tmp"
            with open(temp_path, 'w') as f:
                json.dump(save_data, f, indent=2)
            os.replace(temp_path, save_path)
            
            # Update profile with pyramid, level, and total time
            self.update_profile({"pyramid": pyramid, "level": level, "total_time": total_time})
            return True
        except Exception as e:
            print(f"Error saving game: {e}")
            return False
    
    def load_game(self):
        """Load saved game for current user.
        
        Returns:
            dict or None: Save data or None if not found
        """
        if not self.current_user:
            return None
        
        save_path = os.path.join(SAVES_PATH, f"{self.current_user}.json")
        
        if not os.path.exists(save_path):
            return None
        
        try:
            with open(save_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading game: {e}")
            return None
    
    def has_saved_game(self):
        """Check if current user has a saved game.
        
        Returns:
            bool: True if save exists
        """
        if not self.current_user:
            return False
        
        save_path = os.path.join(SAVES_PATH, f"{self.current_user}.json")
        return os.path.exists(save_path)
    
    def delete_save(self):
        """Delete save file for current user.
        
        Returns:
            bool: True if successful
        """
        if not self.current_user:
            return False
        
        save_path = os.path.join(SAVES_PATH, f"{self.current_user}.json")
        
        if not os.path.exists(save_path):
            return True  # Already deleted
        
        try:
            os.remove(save_path)
            return True
        except Exception as e:
            print(f"Error deleting save: {e}")
            return False
    
    # ============= Leaderboard System =============
    
    def submit_score(self, pyramid, total_time):
        """Submit score to pyramid leaderboard.
        
        Args:
            pyramid (int): Pyramid number
            total_time (int): Total time in milliseconds
            
        Returns:
            bool: True if successful
        """
        if not self.current_user or not self.current_profile:
            return False
        
        leaderboard_path = os.path.join(LEADERBOARD_PATH, f"{pyramid}.json")
        
        # Load existing leaderboard
        leaderboard = []
        if os.path.exists(leaderboard_path):
            try:
                with open(leaderboard_path, 'r') as f:
                    leaderboard = json.load(f)
            except Exception as e:
                print(f"Error loading leaderboard: {e}")
                leaderboard = []
        
        # Create entry
        entry = {
            "username": self.current_user,
            "display_name": self.current_profile.get("display_name", self.current_user),
            "total_time": total_time,
            "completed_at": datetime.now().isoformat()
        }
        
        # Check if user already has an entry
        user_entry_idx = None
        for i, e in enumerate(leaderboard):
            if e.get("username") == self.current_user:
                user_entry_idx = i
                break
        
        # Update or add entry (keep best time)
        if user_entry_idx is not None:
            if total_time < leaderboard[user_entry_idx]["total_time"]:
                leaderboard[user_entry_idx] = entry
        else:
            leaderboard.append(entry)
        
        # Sort by time (fastest first)
        leaderboard.sort(key=lambda x: x["total_time"])
        
        # Save leaderboard
        try:
            temp_path = leaderboard_path + ".tmp"
            with open(temp_path, 'w') as f:
                json.dump(leaderboard, f, indent=2)
            os.replace(temp_path, leaderboard_path)
            return True
        except Exception as e:
            print(f"Error saving leaderboard: {e}")
            return False
    
    def get_leaderboard(self, pyramid):
        """Get leaderboard for a pyramid.
        
        Args:
            pyramid (int): Pyramid number
            
        Returns:
            list: List of leaderboard entries sorted by time
        """
        leaderboard_path = os.path.join(LEADERBOARD_PATH, f"{pyramid}.json")
        
        if not os.path.exists(leaderboard_path):
            return []
        
        try:
            with open(leaderboard_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading leaderboard: {e}")
            return []
    
    def get_available_pyramids(self):
        """Get list of pyramids that have leaderboard data.
        
        Returns:
            list: List of pyramid numbers
        """
        pyramids = []
        try:
            for filename in os.listdir(LEADERBOARD_PATH):
                if filename.endswith('.json'):
                    try:
                        pyramid_num = int(filename[:-5])
                        pyramids.append(pyramid_num)
                    except ValueError:
                        pass
            pyramids.sort()
            return pyramids
        except Exception as e:
            print(f"Error getting pyramids: {e}")
            return []
    
    def get_all_leaderboard_data(self):
        """Get leaderboard data for ALL pyramids.
        
        Returns:
            list: List of all leaderboard entries from all pyramids
        """
        all_scores = []
        
        # Read all pyramid leaderboard files (1.json, 2.json, 3.json)
        for pyramid in range(1, 4):  # Pyramids 1, 2, 3
            leaderboard_path = os.path.join(LEADERBOARD_PATH, f"{pyramid}.json")
            if os.path.exists(leaderboard_path):
                try:
                    with open(leaderboard_path, 'r') as f:
                        pyramid_data = json.load(f)
                        for entry in pyramid_data:
                            all_scores.append({
                                'pyramid': pyramid,
                                'name': entry.get('display_name', entry.get('username', 'Unknown')),
                                'total_time': entry.get('total_time', 0)
                            })
                except Exception as e:
                    print(f"Error loading pyramid {pyramid} leaderboard: {e}")
        
        return all_scores
