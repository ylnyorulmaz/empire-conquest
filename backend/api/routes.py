"""
API routes for Empire Conquest.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
import time
import sys
from pathlib import Path

# Add backend root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.game_state import GameState, Village, Resources
from models.units import UnitType, UNIT_DEFINITIONS
from models.buildings import BuildingType, BUILDING_DEFINITIONS

# Initialize game state (absolute path so Render/cwd changes do not break saves)
_data_dir = Path(__file__).resolve().parent.parent.parent / "data"
game_state = GameState(data_dir=str(_data_dir))

app = FastAPI(title="Empire Conquest API")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class BuildRequest(BaseModel):
    building_type: str


class TrainRequest(BaseModel):
    unit_type: str
    count: int = 1


class AttackRequest(BaseModel):
    target_village: str  # target village name or coordinates


class NewGameRequest(BaseModel):
    village_name: str = "My Village"


class VillageResponse(BaseModel):
    name: str
    coordinates: tuple
    resources: dict
    population: int
    max_population: int
    buildings: dict
    army: dict
    attack_level: int
    defense_level: int


# API Routes
@app.get("/")
async def root():
    return {"game": "Empire Conquest", "version": "0.1.0", "status": "running"}


@app.get("/state")
async def get_state():
    """Get current village state"""
    if not game_state.village:
        raise HTTPException(status_code=404, detail="No active game. Create one with POST /new-game")
    
    game_state.village.update_resources()
    game_state.village.process_all_buildings()
    game_state.village.apply_blacksmith_bonuses()
    
    return game_state.village.to_dict()


@app.post("/new-game")
async def new_game(request: NewGameRequest = NewGameRequest()):
    """Create a new game"""
    village = game_state.new_game(request.village_name)
    return village.to_dict()


@app.post("/build")
async def build(request: BuildRequest):
    """Start building/upgrading a building"""
    if not game_state.village:
        raise HTTPException(status_code=404, detail="No active game")
    
    try:
        building_type = BuildingType(request.building_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid building type: {request.building_type}")
    
    success, msg = game_state.village.start_building(building_type)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    
    game_state.save()
    return {"success": True, "message": msg, "state": game_state.village.to_dict()}


@app.get("/buildings")
async def list_buildings():
    """List all building definitions"""
    return {
        btype.value: {
            "name": defn.name,
            "description": defn.description,
            "base_cost": {
                "food": defn.base_cost.food,
                "wood": defn.base_cost.wood,
                "stone": defn.base_cost.stone,
                "gold": defn.base_cost.gold,
            },
            "cost_multiplier": defn.cost_multiplier,
            "base_build_time": defn.base_build_time,
            "max_level": defn.max_level,
            "prerequisites": defn.prerequisite_buildings,
        }
        for btype, defn in BUILDING_DEFINITIONS.items()
    }


@app.get("/building/{building_type}")
async def get_building_info(building_type: str):
    """Get detailed info about a specific building"""
    try:
        btype = BuildingType(building_type)
    except ValueError:
        raise HTTPException(status_code=404, detail="Building not found")
    
    defn = BUILDING_DEFINITIONS[btype]
    return {
        "name": defn.name,
        "description": defn.description,
        "levels": {
            level: {
                "cost": {
                    "food": defn.get_cost_at_level(level).food,
                    "wood": defn.get_cost_at_level(level).wood,
                    "stone": defn.get_cost_at_level(level).stone,
                    "gold": defn.get_cost_at_level(level).gold,
                },
                "build_time": defn.get_build_time(level),
                "effects": defn.get_effects_at_level(level).__dict__,
            }
            for level in range(1, defn.max_level + 1)
        },
        "prerequisites": defn.prerequisite_buildings,
    }


@app.post("/train")
async def train(request: TrainRequest):
    """Train units"""
    if not game_state.village:
        raise HTTPException(status_code=404, detail="No active game")
    
    try:
        unit_type = UnitType(request.unit_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid unit type: {request.unit_type}")
    
    if request.count <= 0:
        raise HTTPException(status_code=400, detail="Count must be positive")
    
    success, msg = game_state.village.train_unit(unit_type, request.count)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    
    game_state.save()
    return {"success": True, "message": msg, "state": game_state.village.to_dict()}


@app.get("/units")
async def list_units():
    """List all unit definitions"""
    return {
        utype.value: {
            "loot_capacity": defn.loot_capacity,
            "attack": defn.attack,
            "defense": defn.defense,
            "food_cost": defn.food_cost,
            "training_time": defn.training_time,
            "required_building": defn.required_building,
        }
        for utype, defn in UNIT_DEFINITIONS.items()
    }


@app.get("/army")
async def get_army():
    """Get current army composition"""
    if not game_state.village:
        raise HTTPException(status_code=404, detail="No active game")
    
    game_state.village.update_resources()
    game_state.village.apply_blacksmith_bonuses()
    
    army_data = {}
    total_attack = 0
    total_defense = 0
    total_loot = 0
    total_population = 0
    
    for utype, unit in game_state.village.army.items():
        if unit.count > 0:
            army_data[utype.value] = unit.to_dict()
            total_attack += unit.total_attack * unit.count
            total_defense += unit.total_defense * unit.count
            total_loot += unit.total_loot_capacity
            total_population += unit.count
    
    return {
        "units": army_data,
        "summary": {
            "total_attack": total_attack,
            "total_defense": total_defense,
            "total_loot_capacity": total_loot,
            "total_population": total_population,
        }
    }


@app.post("/attack")
async def attack(request: AttackRequest):
    """Attack another village (simplified simulation)"""
    if not game_state.village:
        raise HTTPException(status_code=404, detail="No active game")
    
    # Simplified attack simulation
    attacker_power = game_state.village.get_total_attack_power()
    attacker_loot_capacity = game_state.village.get_total_loot_capacity()
    
    # Simulate defender (random power for now)
    import random
    defender_power = random.randint(50, 500)
    defender_resources = {
        "food": random.randint(100, 2000),
        "wood": random.randint(50, 1000),
        "stone": random.randint(20, 500),
        "gold": random.randint(10, 200),
    }
    
    # Calculate outcome
    if attacker_power > defender_power:
        # Victory
        loot_taken = min(attacker_loot_capacity, sum(defender_resources.values()))
        # Distribute loot proportionally
        total_defender_res = sum(defender_resources.values())
        if total_defender_res > 0:
            loot = {}
            for res_type, amount in defender_resources.items():
                loot[res_type] = int(amount * (loot_taken / total_defender_res))
        else:
            loot = {k: 0 for k in defender_resources}
        
        result = "victory"
        casualties = random.randint(0, max(1, sum(u.count for u in game_state.village.army.values()) // 10))
    else:
        # Defeat
        loot = {k: 0 for k in defender_resources}
        result = "defeat"
        casualties = random.randint(1, max(1, sum(u.count for u in game_state.village.army.values()) // 5))
    
    # Apply casualties (simplified - remove from random units)
    if casualties > 0:
        for unit in game_state.village.army.values():
            if unit.count > 0:
                lost = min(casualties, unit.count)
                unit.count -= lost
                casualties -= lost
                if casualties <= 0:
                    break
    
    # Add loot
    for res_type, amount in loot.items():
        setattr(game_state.village.resources, res_type, 
                getattr(game_state.village.resources, res_type) + amount)
    
    game_state.save()
    
    return {
        "result": result,
        "attacker_power": attacker_power,
        "defender_power": defender_power,
        "loot": loot,
        "casualties": sum(1 for u in game_state.village.army.values() if u.count == 0),
        "state": game_state.village.to_dict()
    }


@app.get("/map")
async def get_map():
    """Get world map (simplified)"""
    # Generate some dummy villages
    import random
    villages = []
    for i in range(10):
        villages.append({
            "name": f"Village {i+1}",
            "coordinates": (random.randint(-50, 50), random.randint(-50, 50)),
            "player": f"Player {random.randint(1, 5)}",
            "population": random.randint(50, 500),
        })
    
    return {
        "current_village": {
            "name": game_state.village.name if game_state.village else "None",
            "coordinates": game_state.village.coordinates if game_state.village else (0, 0),
        },
        "nearby_villages": villages,
    }


@app.post("/tick")
async def manual_tick():
    """Manually trigger a game tick"""
    if not game_state.village:
        raise HTTPException(status_code=404, detail="No active game")
    
    game_state.tick()
    return {"success": True, "message": "Game tick processed", "state": game_state.village.to_dict()}