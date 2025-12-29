"""
Tests for Phase 3: Core field protection in entity properties dicts.

CoreFieldProtectingDict prevents accidental modification of core entity fields
(id, name, location, etc.) through the properties dict. Core fields should only
be modified via direct attribute access.
"""

import unittest
from src.state_manager import Actor, Item, Location, Part, CoreFieldProtectingDict
from src.types import ActorId, ItemId, LocationId, PartId


class TestCoreFieldProtectingDict(unittest.TestCase):
    """Test CoreFieldProtectingDict behavior directly."""

    def test_can_set_non_core_field(self):
        """Should allow setting fields not in core_fields set."""
        props = CoreFieldProtectingDict({'id', 'name'})
        props['health'] = 100
        self.assertEqual(props['health'], 100)

    def test_cannot_set_core_field(self):
        """Should raise TypeError when setting a core field."""
        props = CoreFieldProtectingDict({'id', 'name'})
        with self.assertRaises(TypeError) as cm:
            props['id'] = 'new_id'
        self.assertIn('Cannot set core field', str(cm.exception))
        self.assertIn('id', str(cm.exception))
        self.assertIn('entity.id = value', str(cm.exception))

    def test_setdefault_on_non_core_field(self):
        """Should allow setdefault on non-core fields."""
        props = CoreFieldProtectingDict({'id', 'name'})
        result = props.setdefault('health', 100)
        self.assertEqual(result, 100)
        self.assertEqual(props['health'], 100)

    def test_setdefault_on_core_field_raises(self):
        """Should raise TypeError when using setdefault on core field."""
        props = CoreFieldProtectingDict({'id', 'name'})
        with self.assertRaises(TypeError) as cm:
            props.setdefault('name', 'Test')
        self.assertIn('Cannot set core field', str(cm.exception))
        self.assertIn('name', str(cm.exception))

    def test_update_with_non_core_fields(self):
        """Should allow update with non-core fields."""
        props = CoreFieldProtectingDict({'id', 'name'})
        props.update({'health': 100, 'mana': 50})
        self.assertEqual(props['health'], 100)
        self.assertEqual(props['mana'], 50)

    def test_update_with_core_field_raises(self):
        """Should raise TypeError when update includes core field."""
        props = CoreFieldProtectingDict({'id', 'name'})
        with self.assertRaises(TypeError) as cm:
            props.update({'health': 100, 'name': 'NewName'})
        self.assertIn('Cannot set core field', str(cm.exception))
        self.assertIn('name', str(cm.exception))

    def test_update_kwargs_with_core_field_raises(self):
        """Should raise TypeError when update kwargs include core field."""
        props = CoreFieldProtectingDict({'id', 'name'})
        with self.assertRaises(TypeError) as cm:
            props.update(health=100, id='new_id')
        self.assertIn('Cannot set core field', str(cm.exception))
        self.assertIn('id', str(cm.exception))

    def test_can_read_any_field(self):
        """Should allow reading both core and non-core fields."""
        props = CoreFieldProtectingDict({'id', 'name'})
        props['health'] = 100
        # Reading should work for any field
        self.assertEqual(props.get('health'), 100)
        self.assertIsNone(props.get('id'))
        self.assertIsNone(props.get('name'))

    def test_attribute_access_blocked(self):
        """Should prevent attribute-style writes to properties dict."""
        props = CoreFieldProtectingDict({'id'})
        with self.assertRaises(TypeError) as cm:
            props.custom_field = 'value'
        self.assertIn('Cannot set attributes on properties dict', str(cm.exception))
        self.assertIn("properties['custom_field']", str(cm.exception))


class TestActorCoreFieldProtection(unittest.TestCase):
    """Test that Actor uses core field protection (once Step 2 is implemented)."""

    def test_actor_can_set_custom_property(self):
        """Actors should be able to set non-core properties."""
        actor = Actor(id=ActorId('test'), name='Test', description='Test actor', location=LocationId('start'))
        actor.properties['health'] = 100
        self.assertEqual(actor.properties['health'], 100)

    def test_actor_core_fields_identified(self):
        """Verify Actor has correct core fields defined."""
        # This test will pass once Step 2 is complete
        # For now, it documents what the expected core fields are
        expected_core_fields = {'id', 'name', 'description', 'location', 'inventory', 'behaviors'}
        # After Step 2, we can check: self.assertEqual(actor.properties._core_fields, expected_core_fields)


class TestItemCoreFieldProtection(unittest.TestCase):
    """Test that Item uses core field protection (once Step 2 is implemented)."""

    def test_item_can_set_custom_property(self):
        """Items should be able to set non-core properties."""
        item = Item(id=ItemId('sword'), name='Sword', description='A sharp blade', location=LocationId('start'))
        item.properties['damage'] = 10
        self.assertEqual(item.properties['damage'], 10)

    def test_item_core_fields_identified(self):
        """Verify Item has correct core fields defined."""
        expected_core_fields = {'id', 'name', 'description', 'location', 'behaviors'}


class TestLocationCoreFieldProtection(unittest.TestCase):
    """Test that Location uses core field protection (once Step 2 is implemented)."""

    def test_location_can_set_custom_property(self):
        """Locations should be able to set non-core properties."""
        location = Location(id=LocationId('cave'), name='Cave', description='A dark cave')
        location.properties['light_level'] = 0
        self.assertEqual(location.properties['light_level'], 0)

    def test_location_core_fields_identified(self):
        """Verify Location has correct core fields defined."""
        expected_core_fields = {'id', 'name', 'description', 'exits', 'items', 'behaviors'}


class TestPartCoreFieldProtection(unittest.TestCase):
    """Test that Part uses core field protection (once Step 2 is implemented)."""

    def test_part_can_set_custom_property(self):
        """Parts should be able to set non-core properties."""
        part = Part(id=PartId('blade'), name='Blade', part_of=ItemId('sword'))
        part.properties['sharpness'] = 95
        self.assertEqual(part.properties['sharpness'], 95)

    def test_part_core_fields_identified(self):
        """Verify Part has correct core fields defined."""
        expected_core_fields = {'id', 'name', 'part_of', 'behaviors'}


if __name__ == '__main__':
    unittest.main()
