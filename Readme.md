# Text Adventure Game Framework

Started out as a simple adventure game command parser in Python and then grew. 

New item types, vocabulary and behaviors can easily be added without modifying the existing modules. 

The front end llm_game will use Claude to understand your input, send it to the game engine, and narrate the result. You will need a Claude API key in the approprate environment variable. 

I plan to have the llm operate NPCs but haven't gotten to it. The LLM will never manage the game state, that needs to be stable and fairly rigid. 

## Quick Start Guide

quick_start.md

## Installation

```bash
# Clone repository
git clone <repository-url>
cd text-game

# Create virtual environment (optional but recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# wxPython required to save and load game state (intial state loads without this)
# Optional: Install coverage for testing
pip install coverage
```

## Testing

```bash
# Run all tests
python -m unittest discover tests

# Or use the test runner script
python run_tests.py              # Run all tests
python run_tests.py parser -v    # Run parser tests with verbose output
python run_tests.py performance  # Run performance tests
...

# Run with coverage
pip install coverage
coverage run -m unittest discover tests
coverage report
coverage html
open htmlcov/index.html
```

## Documentation

Right now the best available account is in docs/behavior_refactoring.md but it is is a design document and is out of date. Still conceptually useful. 

## License

MIT

## Credits

Framework for a simple llm friendly text adventure game UI, in Python. To my surprise, searching for this did not find any existing libraries that fit the bill, so I built one! Claude did nearly all the tedious parts. 
