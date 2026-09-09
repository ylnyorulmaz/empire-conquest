# Empire Conquest

OGame-inspired browser-based text strategy game set in medieval times.

## Game Concept

A medieval strategy game where players build their empire, train armies, and conquer territories. Inspired by OGame's resource management and fleet mechanics, adapted to medieval warfare.

## Units

| Unit | Loot Capacity | Attack | Defense | Cost (Food) |
|------|---------------|--------|---------|-------------|
| Peasant | 10 | 2 | 4 | 50 |
| Warrior | 6 | 4 | 6 | 100 |
| Archer | 4 | 8 | 3 | 120 |
| Pikeman | 5 | 6 | 8 | 110 |
| Knight | 8 | 12 | 12 | 250 |

## Buildings

### Resource Buildings
- **Farm** - Produces food and increases population capacity

### Military Buildings
- **Barracks** - Trains peasants and warriors
- **Archery Range** - Trains archers
- **Stable** - Trains knights

### Upgrade Buildings
- **Blacksmith** - Upgrades unit attack/defense

### Defensive Buildings
- **Tower** - Ranged defense
- **Moat** - Reduces enemy attack effectiveness

## Tech Stack

- Backend: Python (FastAPI)
- Frontend: Vanilla HTML/CSS/JS (text-based, no frameworks)
- Data: JSON for game state persistence

## Project Structure

```
empire-conquest/
├── backend/
│   ├── main.py           # FastAPI app
│   ├── models/
│   │   ├── units.py      # Unit definitions
│   │   ├── buildings.py  # Building definitions
│   │   └── game_state.py # Game state management
│   └── api/
│       └── routes.py     # API endpoints
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── app.js
└── data/
    └── game_state.json
```

## Quick Start

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

Then open `frontend/index.html` in browser.

## Game Loop

1. Build farms for food production
2. Build barracks/archery range/stable for unit training
3. Research upgrades at blacksmith
4. Build defenses (towers, moats)
5. Attack other players for loot
6. Manage population and food consumption
```

## API Endpoints

- `GET /state` - Get current game state
- `POST /build` - Construct a building
- `POST /train` - Train units
- `POST /research` - Upgrade units
- `POST /attack` - Attack another player
- `GET /map` - Get world map