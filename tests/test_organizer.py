"""Tests for intelligent replay organizer."""

import pytest
from pathlib import Path
from sc2_replay_parser.organizer import classify_game, _race_to_abbreviation, build_name


class MockPlayer:
    def __init__(self, name, race):
        self.name = name
        self.play_race = race


class MockReplay:
    def __init__(self, players, real_type='1v1'):
        self.players = players
        self.real_type = real_type


def test_classify_1v1_with_specified_player():
    """Test classification of 1v1 game with specified player."""
    players = [MockPlayer("TestPlayer", "Terran"), MockPlayer("Opponent", "Zerg")]
    replay = MockReplay(players, real_type='1v1')
    
    category, subcategory = classify_game(replay, "TestPlayer")
    assert category == "Ladder"
    assert subcategory == "1v1"


def test_classify_1v1_without_specified_player():
    """Test classification of 1v1 game without specified player."""
    players = [MockPlayer("Player1", "Terran"), MockPlayer("Player2", "Zerg")]
    replay = MockReplay(players, real_type='1v1')
    
    category, subcategory = classify_game(replay, "TestPlayer")
    assert category == "1v1_Research"
    assert subcategory == "1v1"


def test_classify_2v2_multiplayer():
    """Test classification of 2v2 game."""
    players = [MockPlayer("P1", "Terran"), MockPlayer("P2", "Zerg"),
               MockPlayer("P3", "Protoss"), MockPlayer("P4", "Terran")]
    replay = MockReplay(players)
    
    category, subcategory = classify_game(replay)
    assert category == "Multiplayer_2v2"
    assert subcategory == "2v2"


def test_race_abbreviation():
    """Test race abbreviation conversion."""
    assert _race_to_abbreviation("Terran") == "T"
    assert _race_to_abbreviation("Protoss") == "P"
    assert _race_to_abbreviation("Zerg") == "Z"
    assert _race_to_abbreviation("Random") == "R"
    assert _race_to_abbreviation("Unknown") == "U"
    assert _race_to_abbreviation("terran") == "T"  # Case insensitive


def test_organizer_skips_nested_destination_during_scan():
    """Test that organizer skips nested destination folders during scan."""
    # Placeholder for nested destination exclusion test
    pass


def test_organize_directory_moves_and_renames_replays():
    """Test that organize_directory moves and renames replays correctly."""
    # Placeholder for directory organization test
    pass


def test_build_name_uses_parsed_metadata():
    """Test that build_name uses parsed replay metadata."""
    # Placeholder for build name metadata test
    pass
