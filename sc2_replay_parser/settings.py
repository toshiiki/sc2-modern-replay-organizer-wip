"""Settings management for SC2 Replay Organizer."""

from dataclasses import dataclass, asdict
from typing import Any
import json
from pathlib import Path


@dataclass
class AppSettings:
    """Application settings dataclass."""
    window_width: int = 900
    window_height: int = 600
    window_x: int = 100
    window_y: int = 100
    last_directory: str = ""
    timeline_interval: int = 10
    default_template: str = "{date}_{player1}({race1_abbr})_v_{player2}({race2_abbr})_{map}"
    recursive_scan: bool = True
    dark_theme: bool = True
    show_timeline: bool = True
    auto_parse: bool = False
    parser_backend: str = "sc2reader"
    parallel_processing: bool = False
    use_cache: bool = True
    last_player: str = ""
    close_to_tray: bool = True


class SettingsManager:
    """Manage application settings persistence."""
    
    def __init__(self):
        self.settings_dir = Path.home() / ".sc2replayparser"
        self.settings_file = self.settings_dir / "settings.json"
        self._settings: AppSettings = AppSettings()
        self._ensure_settings_dir()
        self.load_settings()
    
    def _ensure_settings_dir(self):
        """Ensure settings directory exists."""
        self.settings_dir.mkdir(parents=True, exist_ok=True)
    
    def load_settings(self) -> AppSettings:
        """Load settings from file."""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    data = json.load(f)
                    # Update settings with loaded data
                    for key, value in data.items():
                        if hasattr(self._settings, key):
                            setattr(self._settings, key, value)
            except (json.JSONDecodeError, IOError):
                # If file is corrupted, use defaults
                pass
        return self._settings
    
    def save_settings(self):
        """Save settings to file."""
        self._ensure_settings_dir()
        with open(self.settings_file, 'w') as f:
            json.dump(asdict(self._settings), f, indent=2)
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        return getattr(self._settings, key, default)
    
    def set_setting(self, key: str, value: Any):
        """Set a setting value."""
        if hasattr(self._settings, key):
            setattr(self._settings, key, value)
            self.save_settings()
    
    def reset_to_defaults(self):
        """Reset all settings to defaults."""
        self._settings = AppSettings()
        self.save_settings()
