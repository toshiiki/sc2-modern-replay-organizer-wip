"""PyQt6 GUI for SC2 Replay Organizer."""

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTreeWidget, QTreeWidgetItem, QLabel, QPushButton,
    QFileDialog, QCheckBox, QFormLayout, QLineEdit, QSpinBox,
    QMessageBox, QStatusBar, QMenuBar, QDialog, QDialogButtonBox
)
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from pathlib import Path
from typing import List, Optional

try:
    from .settings import SettingsManager
    from .themes import apply_theme
except ImportError:
    from sc2_replay_parser.settings import SettingsManager
    from sc2_replay_parser.themes import apply_theme


class OrganizerThread(QThread):
    """Background thread for organization to prevent UI freezing."""
    progress = pyqtSignal(str)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self, replay_paths, source_folder, specified_player, recursive=True):
        super().__init__()
        self.replay_paths = replay_paths
        self.source_folder = source_folder
        self.specified_player = specified_player
        self.recursive = recursive
    
    def run(self):
        try:
            self.progress.emit("Starting organization...")
            
            # Create organized folder structure
            dest_folder = Path(self.source_folder) / "organized"
            dest_folder.mkdir(exist_ok=True)
            
            # Organize with intelligent folders (recursive scanning)
            from sc2_replay_parser.organizer import organize_directory
            results = organize_directory(
                self.source_folder,
                str(dest_folder),
                recursive=self.recursive,
                specified_player=self.specified_player,
                use_intelligent_folders=True,
                dry_run=False
            )
            
            self.progress.emit(f"Organization complete: {len(results)} files organized")
            self.finished.emit(results)
            
        except Exception as e:
            self.error.emit(f"Organization failed: {str(e)}")


class SC2ReplayOrganizerGUI(QMainWindow):
    """Main GUI window for SC2 Replay Organizer."""
    
    def __init__(self):
        super().__init__()
        self.current_replay_info = None
        self.replay_files: List[str] = []
        self.settings_manager = SettingsManager()
        self.tray_icon = None
        self.init_ui()
        self.load_settings()
        self.apply_theme()
        self.setup_tray_icon()
    
    def set_app_icon(self):
        """Set the application icon for window and tray."""
        icon_path = Path(__file__).parent.parent / "sc2_frog_icon.png"
        if icon_path.exists():
            icon = QIcon(str(icon_path))
            self.setWindowIcon(icon)
            QApplication.instance().setWindowIcon(icon)
            return icon
        return QIcon()
    
    def setup_tray_icon(self):
        """Setup system tray icon with context menu."""
        try:
            from PyQt6.QtWidgets import QSystemTrayIcon
            if not QSystemTrayIcon.isSystemTrayAvailable():
                return
            
            icon = self.set_app_icon()
            self.tray_icon = QSystemTrayIcon(icon)
            
            # Create tray menu
            from PyQt6.QtWidgets import QMenu
            tray_menu = QMenu()
            
            # Show/Hide action
            show_action = QAction("Show/Hide", self)
            show_action.triggered.connect(self.toggle_window_visibility)
            tray_menu.addAction(show_action)
            
            # Separator
            tray_menu.addSeparator()
            
            # Quit action
            quit_action = QAction("Quit", self)
            quit_action.triggered.connect(self.force_quit)
            tray_menu.addAction(quit_action)
            
            self.tray_icon.setContextMenu(tray_menu)
            
            # Tray icon click to show/hide
            self.tray_icon.activated.connect(self.on_tray_icon_activated)
            
            # Always show tray icon by default
            self.tray_icon.show()
        except ImportError:
            pass
    
    def on_tray_icon_activated(self, reason):
        """Handle tray icon activation."""
        try:
            from PyQt6.QtWidgets import QSystemTrayIcon
            if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
                self.toggle_window_visibility()
            elif reason == QSystemTrayIcon.ActivationReason.Trigger:
                self.toggle_window_visibility()
        except:
            pass
    
    def toggle_window_visibility(self):
        """Toggle window visibility (show/hide)."""
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()
            self.activateWindow()
    
    def force_quit(self):
        """Force quit the application."""
        QApplication.instance().quit()
    
    def closeEvent(self, event):
        """Handle window close event - minimize to tray if enabled."""
        close_to_tray = self.settings_manager.get_setting('close_to_tray', True)
        
        if close_to_tray and self.tray_icon:
            try:
                from PyQt6.QtWidgets import QSystemTrayIcon
                event.ignore()
                self.hide()
                self.tray_icon.showMessage(
                    "SC2 Replay Organizer",
                    "Application minimized to tray. Double-click tray icon to restore.",
                    QSystemTrayIcon.MessageIcon.Information,
                    2000
                )
            except:
                event.accept()
        else:
            event.accept()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("SC2 Replay Organizer")
        self.setGeometry(100, 100, 900, 600)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create main widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # Main layout
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Instructions
        instructions = QLabel(
            "<b>Instructions:</b><br>"
            "1. Set your player name in Settings (for proper classification)<br>"
            "2. Click 'Add Folder' to select a replay folder<br>"
            "3. Confirm organization to rename and move files<br>"
            "4. Files will be organized into: Ladder, 1v1_Research, Multiplayer_*, Other"
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Add folder button
        add_folder_btn = QPushButton("Add Folder")
        add_folder_btn.clicked.connect(self.add_folder)
        layout.addWidget(add_folder_btn)
        
        # File tree
        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderLabels(["File", "Status"])
        self.file_tree.setColumnWidth(0, 600)
        self.file_tree.setColumnWidth(1, 100)
        layout.addWidget(self.file_tree)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - Add a folder to organize replays")
    
    def create_menu_bar(self):
        """Create the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        add_folder_action = QAction("Add Folder", self)
        add_folder_action.triggered.connect(self.add_folder)
        file_menu.addAction(add_folder_action)
        
        file_menu.addSeparator()
        
        clear_action = QAction("Clear Files", self)
        clear_action.triggered.connect(self.clear_files)
        file_menu.addAction(clear_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Settings menu
        settings_menu = menubar.addMenu("&Settings")
        preferences_action = QAction("Preferences", self)
        preferences_action.triggered.connect(self.show_preferences)
        settings_menu.addAction(preferences_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def add_folder(self):
        """Add a folder of replay files and organize them."""
        try:
            folder_path = QFileDialog.getExistingDirectory(self, "Select Replay Folder")
            
            if not folder_path:
                return
            
            folder = Path(folder_path)
            # Recursively scan for replay files
            replay_files = list(folder.rglob("*.SC2Replay")) + list(folder.rglob("*.sc2replay"))
            
            if not replay_files:
                QMessageBox.information(self, "No Replays", f"No replay files found in {folder_path}")
                return
            
            # Show files in the tree
            self.file_tree.clear()
            self.replay_files.clear()
            
            for replay_file in replay_files:
                item = QTreeWidgetItem()
                item.setText(0, str(replay_file.relative_to(folder)))
                item.setText(1, "Pending")
                item.setData(0, Qt.ItemDataRole.UserRole, str(replay_file))
                self.file_tree.addTopLevelItem(item)
                self.replay_files.append(str(replay_file))
            
            # Immediately offer to organize
            self.organize_folder(replay_files, folder_path)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error processing folder: {str(e)}")
            self.status_bar.showMessage("Error processing folder")
    
    def organize_folder(self, replay_files, source_folder):
        """Organize replay files: rename and move to intelligent folders."""
        # Get specified player from settings
        specified_player = self.settings_manager.get_setting('last_player', None)
        
        # Ask user to confirm organization
        reply = QMessageBox.question(
            self,
            "Organize Replays",
            f"Found {len(replay_files)} replay files (including subdirectories).\n\n"
            f"Player name: '{specified_player or 'Not specified'}'\n\n"
            f"This will:\n"
            f"1. Rename files using the naming convention\n"
            f"2. Move files to intelligent folders (Ladder, 1v1_Research, Multiplayer_*, Other)\n"
            f"3. Process all subdirectories recursively\n\n"
            f"Set your player name in Settings for proper classification.\n\n"
            f"Proceed with organization?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Run organization in background thread with recursive scanning
            self.status_bar.showMessage("Organizing replays...")
            self.organizer_thread = OrganizerThread(
                [str(f) for f in replay_files], 
                source_folder, 
                specified_player,
                recursive=True  # Enable recursive scanning
            )
            self.organizer_thread.progress.connect(self.status_bar.showMessage)
            self.organizer_thread.finished.connect(self.on_organization_complete)
            self.organizer_thread.error.connect(self.on_organization_error)
            self.organizer_thread.start()
        else:
            self.status_bar.showMessage("Organization cancelled")
    
    def on_organization_complete(self, results):
        """Handle successful organization completion."""
        self.status_bar.showMessage(f"Organization complete: {len(results)} files organized")
        
        # Display organization summary
        QMessageBox.information(
            self,
            "Organization Complete",
            f"Successfully organized {len(results)} replay files into organized/ folder\n\n"
            f"Intelligent folder structure:\n"
            f"- Ladder (your games)\n"
            f"- 1v1_Research (study games)\n"
            f"- Multiplayer_* (team games)\n"
            f"- Other (coop/custom games)\n\n"
            f"All subdirectories were processed recursively."
        )
        
        # Refresh file tree to show organized structure
        dest_folder = Path(results[0].parent).parent if results else None
        if dest_folder and dest_folder.exists():
            self.file_tree.clear()
            self.replay_files.clear()
            self.refresh_organized_folder(dest_folder)
    
    def on_organization_error(self, error_message):
        """Handle organization error."""
        self.status_bar.showMessage("Organization failed")
        QMessageBox.critical(self, "Organization Error", error_message)
    
    def refresh_organized_folder(self, dest_folder: Path):
        """Refresh file tree to show organized folder structure."""
        for subfolder in dest_folder.iterdir():
            if subfolder.is_dir():
                # Add folder as a parent item
                folder_item = QTreeWidgetItem(self.file_tree)
                folder_item.setText(0, subfolder.name)
                folder_item.setText(1, f"{len(list(subfolder.glob('*.SC2Replay')))} files")
                folder_item.setExpanded(True)
                
                # Add files under folder
                for replay_file in subfolder.glob("*.SC2Replay"):
                    item = QTreeWidgetItem(folder_item)
                    item.setText(0, replay_file.name)
                    item.setText(1, "Organized")
                    item.setData(0, Qt.ItemDataRole.UserRole, str(replay_file))
    
    def clear_files(self):
        """Clear all files from the file browser."""
        self.file_tree.clear()
        self.replay_files.clear()
        self.status_bar.showMessage("Files cleared")
    
    def load_settings(self):
        """Load application settings."""
        settings = self.settings_manager.load_settings()
        self.resize(settings.window_width, settings.window_height)
        self.move(settings.window_x, settings.window_y)
    
    def apply_theme(self):
        """Apply the selected theme."""
        if self.settings_manager.get_setting('dark_theme', True):
            apply_theme(self, dark=True)
        else:
            apply_theme(self, dark=False)
    
    def show_preferences(self):
        """Show preferences dialog."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Preferences")
        dialog.resize(400, 350)
        
        layout = QFormLayout(dialog)
        
        # Window settings
        width_spin = QSpinBox()
        width_spin.setRange(800, 1920)
        width_spin.setValue(self.settings_manager.get_setting('window_width', 900))
        layout.addRow("Window Width:", width_spin)
        
        height_spin = QSpinBox()
        height_spin.setRange(600, 1080)
        height_spin.setValue(self.settings_manager.get_setting('window_height', 600))
        layout.addRow("Window Height:", height_spin)
        
        # Naming template
        template_edit = QLineEdit()
        template_edit.setText(self.settings_manager.get_setting('default_template', '{date}_{player1}({race1_abbr})_v_{player2}({race2_abbr})_{map}'))
        layout.addRow("Naming Template:", template_edit)
        
        # Behavior settings
        recursive_check = QCheckBox()
        recursive_check.setChecked(self.settings_manager.get_setting('recursive_scan', True))
        layout.addRow("Recursive Scan:", recursive_check)
        
        dark_theme_check = QCheckBox()
        dark_theme_check.setChecked(self.settings_manager.get_setting('dark_theme', True))
        layout.addRow("Dark Theme:", dark_theme_check)
        
        # Player settings for organization
        player_edit = QLineEdit()
        player_edit.setText(self.settings_manager.get_setting('last_player', ''))
        player_edit.setPlaceholderText("Your player name for intelligent organization")
        layout.addRow("Your Player Name:", player_edit)
        
        # Behavior settings
        close_to_tray_check = QCheckBox()
        close_to_tray_check.setChecked(self.settings_manager.get_setting('close_to_tray', True))
        layout.addRow("Close to System Tray:", close_to_tray_check)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Save settings
            self.settings_manager.set_setting('window_width', width_spin.value())
            self.settings_manager.set_setting('window_height', height_spin.value())
            self.settings_manager.set_setting('default_template', template_edit.text())
            self.settings_manager.set_setting('recursive_scan', recursive_check.isChecked())
            self.settings_manager.set_setting('dark_theme', dark_theme_check.isChecked())
            self.settings_manager.set_setting('last_player', player_edit.text())
            self.settings_manager.set_setting('close_to_tray', close_to_tray_check.isChecked())
            
            # Apply window size
            self.resize(width_spin.value(), height_spin.value())
            
            # Apply theme
            self.apply_theme()
    
    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About SC2 Replay Organizer",
            "SC2 Replay Organizer v0.7.0\n\n"
            "A modern StarCraft II replay organizer with intelligent folder classification.\n\n"
            "Features:\n"
            "• Intelligent folder organization\n"
            "• Automatic file renaming\n"
            "• Recursive folder scanning\n"
            "• Modern PyQt6 GUI with dark theme\n"
            "• System tray support\n\n"
            "Generated with [Devin](https://devin.ai)"
        )


def main():
    """Main entry point for the GUI application."""
    app = QApplication([])
    app.setApplicationName("SC2 Replay Organizer")
    
    window = SC2ReplayOrganizerGUI()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    import sys
    sys.exit(main())
