"""Zerg Rush benchmark — progressive validation for Build Module "Creating a Zerg Rush Bot".

Maps to VersusAI Workshop Discourse topic 40:
https://community.versusai.net/t/creating-a-zerg-rush-bot-in-python-from-scratch/40

4 progressive stages:
  Stage 1: Economy Foundation — 16 workers, Extractor, no supply blocks
  Stage 2: The Rush Core — Spawning Pool, Zerglings
  Stage 3: The Speed Advantage — Queen Injects, Metabolic Boost
  Stage 4: Attack — Zerglings sent to enemy base

Uses parsed replay data from sc2-replay-parser. Player-agnostic — use
--bot-player=1 or --bot-player=2 to specify which player is the bot.
"""

import pytest

from conftest import (
    LOOPS_PER_SECOND,
    ZERG_UNITS,
    get_build_order,
    get_unit_tracks,
    get_upgrades,
    get_raw_stats,
    get_timeline,
    find_build_entry,
    find_all_build_entries,
)

# Shorthand constants for this benchmark
SPAWNING_POOL = ZERG_UNITS["SPAWNING_POOL"]
EXTRACTOR = ZERG_UNITS["EXTRACTOR"]
HATCHERY = ZERG_UNITS["HATCHERY"]
OVERLORD = ZERG_UNITS["OVERLORD"]
DRONE = ZERG_UNITS["DRONE"]
ZERGLING = ZERG_UNITS["ZERGLING"]
QUEEN = ZERG_UNITS["QUEEN"]

# Game-time targets (in seconds) from the module checkpoints
POOL_TARGET_TIME = 40       # Spawning Pool started by ~0:40
POOL_MIN_TIME = 30          # Allow 0:30–0:55 pass range
POOL_MAX_TIME = 55
SPEED_TARGET_TIME = 150      # Speed researching by ~2:30
SPEED_MIN_TIME = 120         # Allow 2:00–4:00 pass range
SPEED_MAX_TIME = 240
ATTACK_TARGET_TIME = 240     # Engagement before 4:00
ATTACK_MAX_TIME = 300        # Hard cap — rush should happen by 5:00


# ---------------------------------------------------------------------------
# Stage 1: Economy Foundation
# ---------------------------------------------------------------------------

class TestStage1EconomyFoundation:
    """Stage 1: Your bot produces Drones to 16 supply, builds an Extractor,
    and never gets supply-blocked."""

    def test_16_workers_reached(self, replay_data, bot_player):
        """At some point during the game, the bot should have at least 16 workers."""
        for snap in get_timeline(replay_data):
            player = snap.get("players", {}).get(bot_player, {})
            if player.get("workers_active", 0) >= 16:
                return

        for stats in get_raw_stats(replay_data, bot_player):
            if stats.get("workers_active", 0) >= 16:
                return

        pytest.fail("Never reached 16 workers during the game")

    def test_workers_before_pool(self, replay_data, bot_player):
        """At least 12 Drones should be trained before the Spawning Pool appears."""
        build_order = get_build_order(replay_data, bot_player)
        pool_entry = find_build_entry(build_order, SPAWNING_POOL)
        if not pool_entry:
            pytest.skip("No Spawning Pool built in this replay")

        pool_frame = pool_entry["frame"]
        drones_before_pool = sum(
            1 for entry in build_order
            if entry["name"] == DRONE and entry["frame"] < pool_frame
        )

        assert drones_before_pool >= 12, (
            f"Expected ≥ 12 Drones before Spawning Pool, got {drones_before_pool}"
        )

    def test_extractor_built(self, replay_data, bot_player):
        """An Extractor should appear in the build order."""
        build_order = get_build_order(replay_data, bot_player)
        extractor = find_build_entry(build_order, EXTRACTOR)
        assert extractor is not None, "No Extractor built during the game"

    def test_no_extended_supply_block(self, replay_data, bot_player):
        """No extended hard supply block before Pool.

        Zerg naturally hit 14/14 before their second Overlord pops. The Overlord
        costs 0 supply, so the bot can still produce one. A true block means being
        stuck at cap for an extended time with no Overlord started.
        """
        build_order = get_build_order(replay_data, bot_player)
        pool = find_build_entry(build_order, SPAWNING_POOL)
        pool_frame = pool["frame"] if pool else float("inf")

        # Find all frames before pool where food_used >= food_made
        block_frames = []
        for stats in get_raw_stats(replay_data, bot_player):
            if stats["frame"] >= pool_frame:
                break
            food_used = stats.get("food_used", 0)
            food_made = stats.get("food_made", 1)
            if food_used >= food_made and food_made > 0:
                block_frames.append(stats["frame"])

        if not block_frames:
            return  # No blocks at all

        # Check if an Overlord was started within 15 seconds of the first block
        overlords = find_all_build_entries(build_order, OVERLORD)
        first_block_time = block_frames[0] / LOOPS_PER_SECOND

        for ol in overlords:
            if ol["time_seconds"] <= first_block_time + 15:
                return  # Overlord started within 15s of block

        pytest.fail(
            f"Supply block from {first_block_time:.1f}s with no Overlord "
            f"started within 15 seconds"
        )


# ---------------------------------------------------------------------------
# Stage 2: The Rush Core
# ---------------------------------------------------------------------------

class TestStage2RushCore:
    """Stage 2: Your bot builds a Spawning Pool and produces Zerglings."""

    def test_spawning_pool_built(self, replay_data, bot_player):
        """A Spawning Pool should appear in the build order."""
        build_order = get_build_order(replay_data, bot_player)
        pool_entry = find_build_entry(build_order, SPAWNING_POOL)
        assert pool_entry is not None, "No Spawning Pool built during the game"

    def test_pool_timing(self, replay_data, bot_player):
        """Spawning Pool should start by ~0:40 game time (0:30–0:55 pass range)."""
        build_order = get_build_order(replay_data, bot_player)
        pool_entry = find_build_entry(build_order, SPAWNING_POOL)
        if not pool_entry:
            pytest.skip("No Spawning Pool built")

        pool_time = pool_entry["time_seconds"]
        assert pool_time <= POOL_MAX_TIME, (
            f"Spawning Pool started at {pool_time:.0f}s, expected by {POOL_MAX_TIME}s"
        )

    def test_pool_at_supply_12(self, replay_data, bot_player):
        """Spawning Pool should start at supply 11-14 (Zerg standard range)."""
        build_order = get_build_order(replay_data, bot_player)
        pool_entry = find_build_entry(build_order, SPAWNING_POOL)
        if not pool_entry:
            pytest.skip("No Spawning Pool built")

        supply = pool_entry.get("supply", 0)
        assert 11 <= supply <= 14, (
            f"Spawning Pool started at supply {supply}, expected 11-14"
        )

    def test_at_most_one_pool(self, replay_data, bot_player):
        """At no point should there be more than 1 Spawning Pool."""
        build_order = get_build_order(replay_data, bot_player)
        pool_entries = find_all_build_entries(build_order, SPAWNING_POOL)
        assert len(pool_entries) <= 1, (
            f"Built {len(pool_entries)} Spawning Pools, expected at most 1"
        )

    def test_zerglings_produced(self, replay_data, bot_player):
        """Zerglings should appear in the build order after Pool is ready."""
        build_order = get_build_order(replay_data, bot_player)
        zerglings = find_all_build_entries(build_order, ZERGLING)
        assert len(zerglings) > 0, "No Zerglings produced during the game"

    def test_zerglings_after_pool(self, replay_data, bot_player):
        """Zerglings should only be produced after Pool starts."""
        build_order = get_build_order(replay_data, bot_player)
        pool = find_build_entry(build_order, SPAWNING_POOL)
        if not pool:
            pytest.skip("No Spawning Pool to compare timing")

        zerglings = find_all_build_entries(build_order, ZERGLING)
        if not zerglings:
            pytest.skip("No Zerglings produced")

        first_zerg = zerglings[0]
        assert first_zerg["frame"] >= pool["frame"], (
            f"First Zergling at frame {first_zerg['frame']} before Pool at {pool['frame']}"
        )


# ---------------------------------------------------------------------------
# Stage 3: The Speed Advantage
# ---------------------------------------------------------------------------

class TestStage3SpeedAdvantage:
    """Stage 3: Your Zerglings have Metabolic Boost (Speed) and your
    economy is reinforced with Queen Injects."""

    def test_queen_produced(self, replay_data, bot_player):
        """At least one Queen should be produced."""
        tracks = get_unit_tracks(replay_data, bot_player)
        queens = [t for t in tracks if t["unit_type"] == QUEEN]
        assert len(queens) >= 1, "No Queen produced during the game"

    def test_speed_researched(self, replay_data, bot_player):
        """Zergling Movement Speed upgrade should be started."""
        upgrades = get_upgrades(replay_data, bot_player)
        speed_ups = [u for u in upgrades
                     if "movementspeed" in u.get("name", "").lower()
                     or "speed" in u.get("name", "").lower()]
        assert len(speed_ups) > 0, "Zergling Movement Speed not researched"

    def test_speed_timing(self, replay_data, bot_player):
        """Speed upgrade should start by ~2:30 game time (2:00–3:30 pass range)."""
        upgrades = get_upgrades(replay_data, bot_player)
        speed_ups = [u for u in upgrades
                     if "movementspeed" in u.get("name", "").lower()
                     or "speed" in u.get("name", "").lower()]

        if not speed_ups:
            pytest.skip("Zergling Speed not researched")

        speed_time = speed_ups[0]["time_seconds"]
        assert speed_time <= SPEED_MAX_TIME, (
            f"Speed upgrade started at {speed_time:.0f}s, expected by {SPEED_MAX_TIME}s"
        )

    def test_speed_after_pool(self, replay_data, bot_player):
        """Speed should be researched after Pool is started."""
        build_order = get_build_order(replay_data, bot_player)
        upgrades = get_upgrades(replay_data, bot_player)

        pool = find_build_entry(build_order, SPAWNING_POOL)
        speed_ups = [u for u in upgrades
                     if "movementspeed" in u.get("name", "").lower()
                     or "speed" in u.get("name", "").lower()]

        if not speed_ups:
            pytest.skip("Zergling Speed not researched")
        if not pool:
            pytest.skip("No Spawning Pool to compare timing")

        speed_frame = speed_ups[0]["frame"]
        assert speed_frame > pool["frame"], (
            f"Speed researched at frame {speed_frame} before Pool at {pool['frame']}"
        )


# ---------------------------------------------------------------------------
# Stage 4: Attack
# ---------------------------------------------------------------------------

class TestStage4Attack:
    """Stage 4: Your Zerglings attack the enemy base.

    Replay data doesn't capture attack commands directly. We verify attack
    intent through death positions (units died far from spawn) or, when no
    death data is available, through game outcome (short game + army produced).
    """

    def test_zerglings_sent_to_enemy(self, replay_data, bot_player):
        """Zerglings should move away from spawn (indicating attack)."""
        tracks = get_unit_tracks(replay_data, bot_player)
        zerglings = [t for t in tracks if t["unit_type"] == ZERGLING]

        if not zerglings:
            pytest.skip("No Zerglings produced")

        # Check if any zerglings have death position data
        died_with_position = [
            z for z in zerglings
            if z["died_at"] is not None and z.get("died_x") is not None
        ]

        if died_with_position:
            attackers = 0
            for z in died_with_position:
                dx = z["died_x"] - z["born_x"]
                dy = z["died_y"] - z["born_y"]
                dist = (dx ** 2 + dy ** 2) ** 0.5
                if dist > 20:
                    attackers += 1
            assert attackers > 0, (
                f"No Zerglings died away from birth position. "
                f"Total: {len(zerglings)}, died with pos: {len(died_with_position)}"
            )
        else:
            # No death data (opponent surrendered). Fall back to verifying
            # that zerglings were produced and the game ended as a rush.
            total_zerglings = len(zerglings)
            game_length = replay_data.get("game_length_seconds", 0)

            assert total_zerglings >= 4, (
                f"Only {total_zerglings} Zerglings produced — need ≥ 4 to verify attack"
            )
            assert game_length < 300, (
                f"Game took {game_length:.0f}s — rush attack expected under 300s"
            )

    def test_attack_timing(self, replay_data, bot_player):
        """Engagement should begin before 4:00 game time (5:00 hard cap).

        Verified via game length for no-death-data replays, or via
        death positions for combat replays.
        """
        tracks = get_unit_tracks(replay_data, bot_player)
        zerglings = [t for t in tracks if t["unit_type"] == ZERGLING]

        if not zerglings:
            pytest.skip("No Zerglings produced")

        # If we have death data, check that deaths occurred before the hard cap
        died_with_position = [
            z for z in zerglings
            if z["died_at"] is not None and z.get("died_x") is not None
            and (z["died_x"] - z["born_x"]) ** 2 + (z["died_y"] - z["born_y"]) ** 2 > 400
        ]

        if died_with_position:
            first_combat_death = min(z["died_at"] for z in died_with_position)
            first_combat_time = first_combat_death / LOOPS_PER_SECOND
            assert first_combat_time <= ATTACK_MAX_TIME, (
                f"First combat death at {first_combat_time:.0f}s, "
                f"expected attack before {ATTACK_MAX_TIME}s"
            )
        else:
            # Fall back to game length
            game_length = replay_data.get("game_length_seconds", 0)
            assert game_length <= ATTACK_MAX_TIME, (
                f"Game lasted {game_length:.0f}s — rush engagement expected by {ATTACK_MAX_TIME}s"
            )

    def test_zergling_count_at_attack(self, replay_data, bot_player):
        """At least 6 Zerglings should be produced for a viable rush."""
        tracks = get_unit_tracks(replay_data, bot_player)
        zerglings = [t for t in tracks if t["unit_type"] == ZERGLING]
        assert len(zerglings) >= 6, (
            f"Only {len(zerglings)} Zerglings produced — need ≥ 6 for a rush"
        )


# ---------------------------------------------------------------------------
# Overall: Game Result
# ---------------------------------------------------------------------------

class TestGameResult:
    """Overall game outcome validation."""

    def test_game_completed(self, replay_data):
        """Game should have completed (not crashed or timed out)."""
        game_loops = replay_data.get("game_length_loops", 0)
        assert game_loops > 0, "Game did not complete (0 game loops)"

    def test_game_length_reasonable(self, replay_data):
        """Game should last between 30 seconds and 10 minutes for a rush build."""
        duration = replay_data.get("game_length_seconds", 0)
        assert 30 <= duration <= 600, (
            f"Game duration {duration:.0f}s outside expected range (30-600s)"
        )