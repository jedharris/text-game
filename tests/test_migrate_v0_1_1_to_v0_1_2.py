"""Tests for v0.1.1 → v0.1.2 migration (virtual entity standardization)."""

import unittest
import json
import tempfile
from pathlib import Path
from tools.migrations.migrate_v0_1_1_to_v0_1_2 import (
    migrate_commitments,
    migrate_scheduled_events,
    migrate_gossip,
    migrate_spreads,
    migrate_file,
)


class TestCommitmentMigration(unittest.TestCase):
    """Test commitment migration from extra to first-class entities."""

    def test_empty_commitments(self):
        """No commitments should result in no migration."""
        data = {"extra": {"active_commitments": []}}
        count = migrate_commitments(data)
        self.assertEqual(count, 0)
        self.assertNotIn("commitments", data)

    def test_single_commitment(self):
        """Migrate single commitment to first-class entity."""
        data = {
            "extra": {
                "active_commitments": [
                    {
                        "id": "commit_sira_rescue",
                        "config_id": "commit_sira_rescue",
                        "state": "ACTIVE",
                        "made_at_turn": 5,
                        "deadline_turn": 15,
                        "hope_applied": False
                    }
                ]
            }
        }

        count = migrate_commitments(data)
        self.assertEqual(count, 1)
        self.assertIn("commitments", data)
        self.assertEqual(len(data["commitments"]), 1)

        commitment = data["commitments"][0]
        self.assertEqual(commitment["id"], "commit_sira_rescue")
        self.assertIn("promise", commitment["name"].lower())
        self.assertIn("ACTIVE", commitment["description"])
        self.assertEqual(commitment["properties"]["state"], "ACTIVE")
        self.assertEqual(commitment["properties"]["deadline_turn"], 15)
        self.assertEqual(commitment["behaviors"], ["behaviors.shared.infrastructure.commitments"])

    def test_multiple_commitments(self):
        """Migrate multiple commitments."""
        data = {
            "extra": {
                "active_commitments": [
                    {"id": "commit_1", "config_id": "commit_test1", "state": "ACTIVE"},
                    {"id": "commit_2", "config_id": "commit_test2", "state": "FULFILLED"},
                ]
            }
        }

        count = migrate_commitments(data)
        self.assertEqual(count, 2)
        self.assertEqual(len(data["commitments"]), 2)


class TestScheduledEventMigration(unittest.TestCase):
    """Test scheduled event migration."""

    def test_empty_events(self):
        """No events should result in no migration."""
        data = {"extra": {"scheduled_events": []}}
        count = migrate_scheduled_events(data)
        self.assertEqual(count, 0)
        self.assertNotIn("scheduled_events", data)

    def test_single_event(self):
        """Migrate single scheduled event."""
        data = {
            "extra": {
                "scheduled_events": [
                    {
                        "id": "evt_cold_spread_75",
                        "trigger_turn": 75,
                        "event_type": "cold_spread_milestone",
                        "data": {"region": "meridian_nexus"},
                        "repeating": False
                    }
                ]
            }
        }

        count = migrate_scheduled_events(data)
        self.assertEqual(count, 1)
        self.assertEqual(len(data["scheduled_events"]), 1)

        event = data["scheduled_events"][0]
        self.assertEqual(event["id"], "evt_cold_spread_75")
        self.assertIn("75", event["name"])
        self.assertEqual(event["properties"]["trigger_turn"], 75)
        self.assertEqual(event["properties"]["event_type"], "cold_spread_milestone")
        self.assertFalse(event["properties"]["repeating"])
        self.assertEqual(event["behaviors"], ["behaviors.shared.infrastructure.scheduled_events"])

    def test_repeating_event(self):
        """Migrate repeating event with interval."""
        data = {
            "extra": {
                "scheduled_events": [
                    {
                        "id": "evt_tick",
                        "trigger_turn": 10,
                        "event_type": "periodic_tick",
                        "repeating": True,
                        "interval": 5
                    }
                ]
            }
        }

        count = migrate_scheduled_events(data)
        self.assertEqual(count, 1)

        event = data["scheduled_events"][0]
        self.assertTrue(event["properties"]["repeating"])
        self.assertEqual(event["properties"]["interval"], 5)
        self.assertIn("repeating", event["description"].lower())


class TestGossipMigration(unittest.TestCase):
    """Test gossip migration."""

    def test_empty_gossip(self):
        """No gossip should result in no migration."""
        data = {"extra": {"gossip_queue": []}}
        count = migrate_gossip(data)
        self.assertEqual(count, 0)
        self.assertNotIn("gossip", data)

    def test_point_to_point_gossip(self):
        """Migrate point-to-point gossip."""
        data = {
            "extra": {
                "gossip_queue": [
                    {
                        "id": "gossip_sira_rescue",
                        "content": "Player rescued Sira from wolves",
                        "source_npc": "npc_traveler",
                        "target_npcs": ["npc_healer_elara"],
                        "created_turn": 5,
                        "arrives_turn": 17,
                        "confession_window_until": 29
                    }
                ]
            }
        }

        count = migrate_gossip(data)
        self.assertEqual(count, 1)

        gossip = data["gossip"][0]
        self.assertEqual(gossip["id"], "gossip_sira_rescue")
        self.assertIn("Player rescued Sira", gossip["name"])
        self.assertEqual(gossip["properties"]["gossip_type"], "POINT_TO_POINT")
        self.assertEqual(gossip["properties"]["source_npc"], "npc_traveler")
        self.assertEqual(gossip["properties"]["target_npcs"], ["npc_healer_elara"])
        self.assertEqual(gossip["properties"]["confession_window_until"], 29)
        self.assertEqual(gossip["behaviors"], ["behaviors.shared.infrastructure.gossip"])

    def test_broadcast_gossip(self):
        """Migrate broadcast gossip."""
        data = {
            "extra": {
                "gossip_queue": [
                    {
                        "id": "gossip_broadcast",
                        "content": "Strange noises in caves",
                        "source_npc": "npc_guard",
                        "target_regions": ["loc_town", "loc_market"],
                        "created_turn": 10,
                        "arrives_turn": 12
                    }
                ]
            }
        }

        count = migrate_gossip(data)
        self.assertEqual(count, 1)

        gossip = data["gossip"][0]
        self.assertEqual(gossip["properties"]["gossip_type"], "BROADCAST")
        self.assertEqual(gossip["properties"]["target_regions"], ["loc_town", "loc_market"])
        self.assertIn("broadcast", gossip["description"].lower())

    def test_network_gossip(self):
        """Migrate network gossip."""
        data = {
            "extra": {
                "gossip_queue": [
                    {
                        "id": "gossip_network",
                        "content": "Network message",
                        "source_npc": "npc_spy",
                        "network_id": "spy_network",
                        "created_turn": 1,
                        "arrives_turn": 3
                    }
                ]
            }
        }

        count = migrate_gossip(data)
        self.assertEqual(count, 1)

        gossip = data["gossip"][0]
        self.assertEqual(gossip["properties"]["gossip_type"], "NETWORK")
        self.assertEqual(gossip["properties"]["network_id"], "spy_network")
        self.assertIn("network", gossip["description"].lower())


class TestSpreadMigration(unittest.TestCase):
    """Test environmental spread migration."""

    def test_empty_spreads(self):
        """No spreads should result in no migration."""
        data = {"extra": {"environmental_spreads": {}}}
        count = migrate_spreads(data)
        self.assertEqual(count, 0)
        self.assertNotIn("spreads", data)

    def test_single_spread(self):
        """Migrate single environmental spread."""
        data = {
            "extra": {
                "environmental_spreads": {
                    "frozen_reaches_cold": {
                        "active": True,
                        "halt_flag": "cold_stopped",
                        "milestones": [
                            {"turn": 25, "effects": [{"property": "temperature", "value": "FREEZING"}]},
                            {"turn": 50, "effects": [{"property": "temperature", "value": "DEADLY_COLD"}]}
                        ],
                        "reached_milestones": [25]
                    }
                }
            }
        }

        count = migrate_spreads(data)
        self.assertEqual(count, 1)

        spread = data["spreads"][0]
        self.assertEqual(spread["id"], "frozen_reaches_cold")
        self.assertIn("Frozen Reaches Cold", spread["name"])
        self.assertTrue(spread["properties"]["active"])
        self.assertEqual(spread["properties"]["halt_flag"], "cold_stopped")
        self.assertEqual(len(spread["properties"]["milestones"]), 2)
        self.assertEqual(spread["properties"]["reached_milestones"], [25])
        self.assertEqual(spread["behaviors"], ["behaviors.shared.infrastructure.spreads"])

    def test_multiple_spreads(self):
        """Migrate multiple spreads."""
        data = {
            "extra": {
                "environmental_spreads": {
                    "spread_1": {"active": True, "milestones": []},
                    "spread_2": {"active": False, "milestones": []}
                }
            }
        }

        count = migrate_spreads(data)
        self.assertEqual(count, 2)
        self.assertEqual(len(data["spreads"]), 2)


class TestFileMigration(unittest.TestCase):
    """Test full file migration."""

    def test_migrate_complete_file(self):
        """Migrate a complete game_state.json with all virtual entity types."""
        game_data = {
            "metadata": {"title": "Test", "version": "0.1.1"},
            "locations": [{"id": "loc_start", "name": "Start", "description": "Start location"}],
            "items": [],
            "locks": [],
            "actors": {
                "player": {
                    "id": "player",
                    "name": "Player",
                    "description": "The player",
                    "location": "loc_start",
                    "inventory": []
                }
            },
            "extra": {
                "active_commitments": [
                    {"id": "commit_1", "config_id": "commit_test", "state": "ACTIVE"}
                ],
                "scheduled_events": [
                    {"id": "evt_1", "trigger_turn": 10, "event_type": "test"}
                ],
                "gossip_queue": [
                    {
                        "id": "gossip_1",
                        "content": "Test news",
                        "source_npc": "npc_1",
                        "target_npcs": ["npc_2"],
                        "created_turn": 1,
                        "arrives_turn": 2
                    }
                ],
                "environmental_spreads": {
                    "test_spread": {"active": True, "milestones": []}
                }
            }
        }

        # Write to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(game_data, f, indent=2)
            temp_path = Path(f.name)

        try:
            # Migrate
            changed = migrate_file(temp_path)
            self.assertTrue(changed)

            # Load and verify
            migrated_data = json.loads(temp_path.read_text())

            # Check version
            self.assertEqual(migrated_data["metadata"]["version"], "0.1.2")

            # Check all collections exist and have correct counts
            self.assertEqual(len(migrated_data["commitments"]), 1)
            self.assertEqual(len(migrated_data["scheduled_events"]), 1)
            self.assertEqual(len(migrated_data["gossip"]), 1)
            self.assertEqual(len(migrated_data["spreads"]), 1)

            # Verify structure of first commitment
            commitment = migrated_data["commitments"][0]
            self.assertIn("id", commitment)
            self.assertIn("name", commitment)
            self.assertIn("description", commitment)
            self.assertIn("properties", commitment)
            self.assertIn("behaviors", commitment)

        finally:
            temp_path.unlink()

    def test_no_changes_if_already_migrated(self):
        """File already at v0.1.2 with no extra virtual entities should not change."""
        game_data = {
            "metadata": {"title": "Test", "version": "0.1.2"},
            "locations": [],
            "items": [],
            "locks": [],
            "actors": {
                "player": {
                    "id": "player",
                    "name": "Player",
                    "description": "Player",
                    "location": "loc_start",
                    "inventory": []
                }
            },
            "extra": {}
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(game_data, f, indent=2)
            temp_path = Path(f.name)

        try:
            changed = migrate_file(temp_path)
            self.assertFalse(changed)
        finally:
            temp_path.unlink()


if __name__ == '__main__':
    unittest.main()
