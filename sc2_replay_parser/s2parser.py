"""s2protocol-based parser for modern SC2 replays."""

from pathlib import Path
from typing import Dict, Any, Optional
import json


def parse_replay(replay_path: str) -> Dict[str, Any]:
    """
    Parse a SC2 replay file using s2protocol.
    
    Args:
        replay_path: Path to the .SC2Replay file
    
    Returns:
        Dictionary containing parsed replay data
    """
    try:
        import s2protocol
    except ImportError:
        raise ImportError("s2protocol is not installed. Install with: pip install s2protocol")
    
    replay_file = Path(replay_path)
    if not replay_file.exists():
        raise FileNotFoundError(f"Replay file not found: {replay_path}")
    
    try:
        # Parse replay header
        decoder = s2protocol.decode_replay_header(replay_file)
        
        # Extract basic information
        data = {
            'map_name': decoder.get('map_name', 'Unknown'),
            'region': decoder.get('region', 'Unknown'),
            'expansion': decoder.get('expansion', 'Unknown'),
            'game_length_seconds': decoder.get('duration', 0),
            'game_date': decoder.get('date', 'Unknown'),
            'players': [],
            'build_orders': [],
            'upgrades': [],
            'unit_tracks': [],
            'timeline': [],
        }
        
        # Extract player information
        if 'players' in decoder:
            for player in decoder['players']:
                player_data = {
                    'name': player.get('name', 'Unknown'),
                    'race': player.get('race', 'Unknown'),
                    'color': player.get('color', {}),
                    'is_winner': player.get('is_winner', False),
                }
                data['players'].append(player_data)
        
        return data
        
    except Exception as e:
        raise RuntimeError(f"Failed to parse replay with s2protocol: {e}")


def main():
    """CLI entry point for s2protocol parser."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Parse SC2 replay files using s2protocol')
    parser.add_argument('replay', help='Path to the replay file')
    parser.add_argument('--output', '-o', help='Output JSON file')
    parser.add_argument('--jsonl', action='store_true', help='Output in JSONL format')
    
    args = parser.parse_args()
    
    try:
        data = parse_replay(args.replay)
        
        if args.jsonl:
            output = json.dumps(data)
        else:
            output = json.dumps(data, indent=2)
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(output)
            print(f"Results written to {args.output}")
        else:
            print(output)
            
    except Exception as e:
        print(f"Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
