"""Tests for intelligent organizer classification logic."""

import pytest
from sc2_replay_parser.organizer import classify_game, _race_to_abbreviation


class MockPlayer:
    def __init__(self, name, race):
        self.name = name
        self.play_race = race


class MockReplay:
    def __init__(self, players, real_type='1v1'):
        self.players = players
        self.real_type = real_type


def test_classify_1v1_with_specified_player():
    """Test 1v1 game with specified player goes to Ladder."""
    players = [MockPlayer("TestPlayer", "Terran"), MockPlayer("Opponent", "Zerg")]
    replay = MockReplay(players, real_type='1v1')
    
    category, subcategory = classify_game(replay, "TestPlayer")
    assert category == "Ladder"
    assert subcategory == "1v1"


def test_classify_1v1_without_specified_player():
    """Test 1v1 game without specified player goes to 1v1_Research."""
    players = [MockPlayer("Player1", "Terran"), MockPlayer("Player2", "Zerg")]
    replay = MockReplay(players, real_type='1v1')
    
    category, subcategory = classify_game(replay, "TestPlayer")
    assert category == "1v1_Research"
    assert subcategory == "1v1"


def test_classify_2v2_multiplayer():
    """Test 2v2 game classification."""
    players = [MockPlayer("P1", "Terran"), MockPlayer("P2", "Zerg"),
               MockPlayer("P3", "Protoss"), MockPlayer("P4", "Terran")]
    replay = MockReplay(players)
    
    category, subcategory = classify_game(replay)
    assert category == "Multiplayer_2v2"
    assert subcategory == "2v2"


def test_classify_2v2_with_specified_player():
    """Test 2v2 game with specified player goes to Multiplayer."""
    players = [MockPlayer("TestPlayer", "Terran"), MockPlayer("Ally", "Zerg"),
               MockPlayer("Enemy1", "Protoss"), MockPlayer("Enemy2", "Terran")]
    replay = MockReplay(players)
    
    category, subcategory = classify_game(replay, "TestPlayer")
    assert category == "Multiplayer_2v2"
    assert subcategory == "2v2"


def test_classify_3v3_multiplayer():
    """Test 3v3 game classification."""
    players = [MockPlayer(f"P{i}", "Terran") for i in range(6)]
    replay = MockReplay(players)
    
    category, subcategory = classify_game(replay)
    assert category == "Multiplayer_3v3"
    assert subcategory == "3v3"


def test_classify_4v4_multiplayer():
    """Test 4v4 game classification."""
    players = [MockPlayer(f"P{i}", "Terran") for i in range(8)]
    replay = MockReplay(players)
    
    category, subcategory = classify_game(replay)
    assert category == "Multiplayer_4v4"
    assert subcategory == "4v4"


def test_classify_coop():
    """Test coop game classification."""
    players = [MockPlayer("P1", "Terran"), MockPlayer("P2", "Zerg"),
               MockPlayer("AI1", "Terran"), MockPlayer("AI2", "Zerg")]
    replay = MockReplay(players)
    
    category, subcategory = classify_game(replay)
    assert category == "Other"
    assert subcategory == "unknown"


def test_classify_non_ladder():
    """Test non-ladder 1v1 game classification."""
    players = [MockPlayer("P1", "Terran"), MockPlayer("P2", "Zerg")]
    replay = MockReplay(players, real_type='Custom')
    
    category, subcategory = classify_game(replay, "P1")
    assert category == "1v1_Research"
    assert subcategory == "1v1"


def test_classify_case_insensitive_player_name():
    """Test case-insensitive player name matching."""
    players = [MockPlayer("TestPlayer", "Terran"), MockPlayer("Opponent", "Zerg")]
    replay = MockReplay(players, real_type='1v1')
    
    category, subcategory = classify_game(replay, "testplayer")
    assert category == "Ladder"
    assert subcategory == "1v1"


def test_classify_no_specified_player():
    """Test classification when no player is specified."""
    players = [MockPlayer("P1", "Terran"), MockPlayer("P2", "Zerg")]
    replay = MockReplay(players, real_type='1v1')
    
    category, subcategory = classify_game(replay, None)
    assert category == "1v1_Research"
    assert subcategory == "1v1"


def test_classify_player_name_whitespace():
    """Test player name matching with whitespace."""
    players = [MockPlayer("Test Player", "Terran"), MockPlayer("Opponent", "Zerg")]
    replay = MockReplay(players, real_type='1v1')
    
    category, subcategory = classify_game(replay, "TestPlayer")
    assert category == "Ladder"
    assert subcategory == "1v1"
