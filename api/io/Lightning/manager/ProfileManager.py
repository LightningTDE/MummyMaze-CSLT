import os
import json
import hashlib
from datetime import datetime
from api.io.Lightning.utils.ConfigFile import USERDATA_PATH


class ProfileManager:
    """Manager for user profiles with authentication."""
    
    @staticmethod
    def hash_password(password):
        """Hash password using SHA256.
        
        Args:
            password (str): Plain text password
            
        Returns:
            str: SHA256 hash of the password
        """
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def create_profile(username, password):
        """Create a new user profile.
        
        Args:
            username (str): Username (must be >= 3 characters)
            password (str): Password (must be >= 4 characters)
            
        Returns:
            tuple: (success: bool, message: str)
        """
        # Validate username length
        if len(username) < 3:
            return False, "USERNAME TOO SHORT"
        
        # Validate password length
        if len(password) < 4:
            return False, "PASSWORD TOO SHORT"
        
        # Sanitize username for filesystem
        safe_username = "".join(c for c in username if c.isalnum() or c in ('_', '-'))
        if safe_username != username:
            return False, "USERNAME INVALID"
        
        # Check if username already exists
        profile_path = os.path.join(USERDATA_PATH, f"{username}.json")
        if os.path.exists(profile_path):
            return False, "USERNAME EXISTS"
        
        # Create userdata directory if it doesn't exist
        os.makedirs(USERDATA_PATH, exist_ok=True)
        
        # Create profile data
        profile_data = {
            "username": username,
            "password_hash": ProfileManager.hash_password(password),
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
            return False, f"Error creating profile: {str(e)}"
    
    @staticmethod
    def authenticate(username, password):
        """Verify user credentials.
        
        Args:
            username (str): Username
            password (str): Password
            
        Returns:
            tuple: (success: bool, message: str)
        """
        # Check for missing info
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
            
            password_hash = ProfileManager.hash_password(password)
            if profile_data.get("password_hash") == password_hash:
                return True, "success"
            else:
                return False, "WRONG PASSWORD"
        except Exception as e:
            return False, f"Error loading profile: {str(e)}"
    
    @staticmethod
    def load_profile(username):
        """Load user profile data.
        
        Args:
            username (str): Username
            
        Returns:
            dict or None: Profile data or None if error
        """
        profile_path = os.path.join(USERDATA_PATH, f"{username}.json")
        
        if not os.path.exists(profile_path):
            return None
        
        try:
            with open(profile_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading profile: {e}")
            return None
    
    @staticmethod
    def save_profile(profile_data):
        """Save user profile data.
        
        Args:
            profile_data (dict): Profile data with 'username' key
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not profile_data or 'username' not in profile_data:
            return False
        
        username = profile_data['username']
        profile_path = os.path.join(USERDATA_PATH, f"{username}.json")
        
        # Create userdata directory if it doesn't exist
        os.makedirs(USERDATA_PATH, exist_ok=True)
        
        try:
            with open(profile_path, 'w') as f:
                json.dump(profile_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving profile: {e}")
            return False
