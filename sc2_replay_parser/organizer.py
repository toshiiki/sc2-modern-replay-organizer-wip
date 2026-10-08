"""Intelligent replay organizer with folder classification."""

from pathlib import Path
from typing import List, Optional, Tuple
import shutil
from datetime import datetime

from sc2reader import resources


def classify_game(replay, specified_player: Optional[str] = None) -> Tuple[str, str]:
    """
    Classify a replay game into a category and subcategory.
    
    Returns tuple of (category, subcategory):
    - Ladder: 1v1 ladder games with specified player
    - 1v1_Research: 1v1 games without specified player
    - Multiplayer_2v2, Multiplayer_3v3, Multiplayer_4v4: Team games
    - Other: Coop, custom games, or nonstandard
    """
    try:
        # Determine game type
        player_count = len(replay.players)
        
        # Check if ladder game
        is_ladder = hasattr(replay, 'real_type') and replay.real_type == '1v1'
        
        # Normalize specified player name
        specified_player = specified_player.strip().lower() if specified_player else None
        
        # Check if specified player is in the game
        player_in_game = False
        if specified_player:
            for player in replay.players:
                player_name = getattr(player, 'name', '').strip().lower()
                if specified_player in player_name or player_name in specified_player:
                    player_in_game = True
                    break
        
        # Classification logic
        if player_count == 2:
            if player_in_game and is_ladder:
                return 'Ladder', '1v1'
            else:
                return '1v1_Research', '1v1'
        elif player_count == 4:
            return 'Multiplayer_2v2', '2v2'
        elif player_count == 6:
            return 'Multiplayer_3v3', '3v3'
        elif player_count == 8:
            return 'Multiplayer_4v4', '4v4'
        else:
            return 'Other', 'unknown'
    except Exception:
        return 'Other', 'unknown'


def _race_to_abbreviation(race: str) -> str:
    """Convert race name to abbreviation."""
    race_map = {
        'Terran': 'T',
        'Protoss': 'P',
        'Zerg': 'Z',
        'Random': 'R',
    }
    race_upper = str(race).upper()
    for full_name, abbr in race_map.items():
        if full_name.upper() == race_upper:
            return abbr
    return 'U'  # Unknown


def _safe_player_name(player, fallback: str) -> str:
    """Extract player name safely with fallbacks."""
    for attr in ["name", "player_name", "display_name"]:
        name = getattr(player, attr, None)
        if name and name not in (None, "", "Unknown"):
            return str(name)
    return fallback


def _safe_game_date(replay) -> str:
    """Extract game date from replay metadata."""
    try:
        if hasattr(replay, 'date') and replay.date:
            return replay.date.strftime('%Y-%m-%d')
        elif hasattr(replay, 'end_time') and replay.end_time:
            return replay.end_time.strftime('%Y-%m-%d')
    except Exception:
        pass
    # Fallback to file modification time
    return datetime.fromtimestamp(replay.filename.stat().st_mtime).strftime('%Y-%m-%d')


def build_name(replay, template: str = "{date}_{player1}({race1_abbr})_v_{player2}({race2_abbr})_{map}") -> str:
    """
    Build a filename from replay metadata using a template.
    
    Available template variables:
    - {date}: Game date
    - {player1}, {player2}: Player names
    - {race1}, {race2}: Full race names
    - {race1_abbr}, {race2_abbr}: Race abbreviations
    - {map}: Map name
    - {time}: Time (HHMMSS)
    - {length}: Game length in seconds
    - {file}: Original filename
    """
    try:
        players = list(replay.players)
        if len(players) < 2:
            return replay.filename.name
        
        player1 = _safe_player_name(players[0], "Player1")
        player2 = _safe_player_name(players[1], "Player2")
        
        race1 = getattr(players[0], 'play_race', 'Unknown')
        race2 = getattr(players[1], 'play_race', 'Unknown')
        
        race1_abbr = _race_to_abbreviation(race1)
        race2_abbr = _race_to_abbreviation(race2)
        
        game_date = _safe_game_date(replay)
        
        map_name = getattr(replay, 'map_name', 'Unknown')
        map_clean = map_name.replace(' ', '_').replace('/', '_')
        
        game_length = getattr(replay, 'game_length', 0)
        
        time_str = datetime.now().strftime('%H%M%S')
        
        # Build filename from template
        filename = template.format(
            date=game_date,
            player1=player1,
            player2=player2,
            race1=race1,
            race2=race2,
            race1_abbr=race1_abbr,
            race2_abbr=race2_abbr,
            map=map_clean,
            map_clean=map_clean,
            time=time_str,
            length=game_length,
            file=replay.filename.stem
        )
        
        return filename + '.SC2Replay'
    except Exception:
        return replay.filename.name


def organize_directory(
    source_dir: str,
    dest_dir: str,
    recursive: bool = True,
    specified_player: Optional[str] = None,
    use_intelligent_folders: bool = True,
    dry_run: bool = False,
    template: str = "{date}_{player1}({race1_abbr})_v_{player2}({race2_abbr})_{map}"
) -> List[Path]:
    """
    Organize replay files from source directory to destination.
    
    Args:
        source_dir: Source directory containing replay files
        dest_dir: Destination directory for organized files
        recursive: Scan subdirectories recursively
        specified_player: Player name for intelligent classification
        use_intelligent_folders: Use intelligent folder separation
        dry_run: Preview changes without moving files
        template: Naming template for files
    
    Returns:
        List of destination file paths
    """
    import sc2reader
    
    source_path = Path(source_dir)
    dest_path = Path(dest_dir)
    
    results = []
    
    # Find replay files
    if recursive:
        replay_files = list(source_path.rglob("*.SC2Replay")) + list(source_path.rglob("*.sc2replay"))
    else:
        replay_files = list(source_path.glob("*.SC2Replay")) + list(source_path.glob("*.sc2replay"))
    
    for replay_file in replay_files:
        try:
            # Parse replay
            replay = sc2reader.read_replay(str(replay_file))
            
            # Build new filename
            new_name = build_name(replay, template)
            
            # Determine destination folder
            if use_intelligent_folders:
                category, _ = classify_game(replay, specified_player)
                dest_folder = dest_path / category
            else:
                dest_folder = dest_path
            
            dest_folder.mkdir(parents=True, exist_ok=True)
            dest_file = dest_folder / new_name
            
            # Handle duplicates
            if dest_file.exists():
                counter = 1
                while dest_file.exists():
                    stem = new_name.rsplit('.', 1)[0]
                    dest_file = dest_folder / f"{stem}_{counter}.SC2Replay"
                    counter += 1
            
            if not dry_run:
                shutil.move(str(replay_file), str(dest_file))
            
            results.append(dest_file)
        except Exception as e:
            print(f"Error processing {replay_file}: {e}")
            continue
    
    return results


def main():
    """CLI entry point for replay organizer."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Organize SC2 replay files into intelligent folders')
    parser.add_argument('source', help='Source directory containing replay files')
    parser.add_argument('dest', help='Destination directory for organized files')
    parser.add_argument('--player', help='Your player name for intelligent classification')
    parser.add_argument('--no-recursive', action='store_true', help='Do not scan subdirectories')
    parser.add_argument('--no-intelligent-folders', action='store_true', help='Disable intelligent folder separation')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without moving files')
    parser.add_argument('--template', default='{date}_{player1}({race1_abbr})_v_{player2}({race2_abbr})_{map}',
                       help='Naming template for files')
    
    args = parser.parse_args()
    
    results = organize_directory(
        args.source,
        args.dest,
        recursive=not args.no_recursive,
        specified_player=args.player,
        use_intelligent_folders=not args.no_intelligent_folders,
        dry_run=args.dry_run,
        template=args.template
    )
    
    print(f"Organized {len(results)} replay files")
    for result in results:
        print(f"  {result}")


if __name__ == "__main__":
    main()
