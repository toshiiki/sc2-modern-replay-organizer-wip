"""Replay handler for batch processing."""

from pathlib import Path
from typing import List, Dict, Any
import json
from .parser import parse_replay


def scan_replay_dir(directory: str, output_file: str = None) -> List[Dict[str, Any]]:
    """
    Scan a directory for replay files and parse them.
    
    Args:
        directory: Directory to scan for replay files
        output_file: Optional JSONL file to write results to
    
    Returns:
        List of parsed replay data
    """
    dir_path = Path(directory)
    results = []
    
    replay_files = list(dir_path.glob("*.SC2Replay")) + list(dir_path.glob("*.sc2replay"))
    
    for replay_file in replay_files:
        try:
            data = parse_replay(str(replay_file))
            results.append(data)
        except Exception as e:
            print(f"Error parsing {replay_file}: {e}")
    
    if output_file:
        with open(output_file, 'w') as f:
            for result in results:
                f.write(json.dumps(result) + '\n')
    
    return results


def main():
    """CLI entry point for replay handler."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Scan and parse replay files from a directory')
    parser.add_argument('directory', help='Directory to scan for replay files')
    parser.add_argument('--output', '-o', help='Output JSONL file')
    
    args = parser.parse_args()
    
    results = scan_replay_dir(args.directory, args.output)
    
    print(f"Parsed {len(results)} replay files from {args.directory}")
    if args.output:
        print(f"Results written to {args.output}")


if __name__ == "__main__":
    main()
