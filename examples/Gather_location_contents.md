gather_location_contents() is now a general-purpose utility that returns raw data. Game developers could use it for:
Custom descriptions - e.g., a behavior that describes a room differently based on what's there
AI/NPC decisions - an NPC could check what items are visible before deciding what to do
Puzzles - check if certain items are present in a location
Ambient text - "The room feels cluttered" if many items, "The room is nearly empty" if few
Lighting checks - iterate through items to see if any provide light
The pattern is: gather_location_contents() gives you the data, you decide how to use it. The existing describe_location() and _query_location() are just two built-in formatters for that data.