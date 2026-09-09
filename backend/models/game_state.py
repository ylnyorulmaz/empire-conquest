"""
Game state management for Empire Conquest.
Handles player village, resources, army, buildings, and game loop.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
import time
from pathlib import Path

from .units import Unit, UnitType, UNIT_DEFINITIONS
from .buildings import Building, BuildingType, BUILDING_DEFINITIONS, check_prerequisites


@dataclass
class Resources:
    """Player resources"""
    food: int = 1000
    wood: int = 500
    stone: int = 200
    gold: int = 100
    
    def can_afford(self, cost) -> bool:
        return (self.food >= cost.food and 
                self.wood >= cost.wood and 
                self.stone >= cost.stone and 
                self.gold >= cost.gold)
    
    def deduct(self, cost):
        self.food -= cost.food
        self.wood -= cost.wood
        self.stone -= cost.stone
        self.gold -= cost.gold
    
    def add(self, other):
        self.food += other.food
        self.wood += other.wood
        self.stone += other.stone
        self.gold += other.gold
    
    def to_dict(self) -> dict:
        return {
            "food": self.food,
            "wood": self.wood,
            "stone": self.stone,
            "gold": self.gold,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Resources':
        return cls(
            food=data.get("food", 1000),
            wood=data.get("wood", 500),
            stone=data.get("stone", 200),
            gold=data.get("gold", 100),
        )


@dataclass
class Village:
    """Player's village state"""
    name: str = "My Village"
    coordinates: tuple = (0, 0)  # x, y on world map
    
    # Resources
    resources: Resources = field(default_factory=Resources)
    resource_production: Resources = field(default_factory=Resources)
    last_resource_update: int = field(default_factory=lambda: int(time.time()))
    
    # Population
    population: int = 0
    max_population: int = 0
    
    # Buildings
    buildings: Dict[BuildingType, Building] = field(default_factory=dict)
    
    # Army
    army: Dict[UnitType, Unit] = field(default_factory=dict)
    
    # Research/Upgrades
    attack_level: int = 0
    defense_level: int = 0
    
    def __post_init__(self):
        # Initialize all buildings at level 0
        for btype in BuildingType:
            if btype not in self.buildings:
                self.buildings[btype] = Building(building_type=btype)
        
        # Initialize all units at count 0
        for utype in UnitType:
            if utype not in self.army:
                self.army[utype] = Unit(unit_type=utype)
    
    def update_resources(self, current_time: int = None):
        """Update resources based on production rates"""
        if current_time is None:
            current_time = int(time.time())
        
        elapsed = current_time - self.last_resource_update
        if elapsed <= 0:
            return
        
        # Convert hourly production to per-second
        hours = elapsed / 3600.0
        
        # Food production from farms
        farm = self.buildings.get(BuildingType.FARM)
        if farm and farm.level > 0:
            food_per_hour = farm.current_effects.food_production
            self.resources.food += int(food_per_hour * hours)
        
        # Population growth (slow, based on food surplus)
        # Simplified: population grows when food > population * 10
        pass
        
        # Unit food consumption
        total_food_consumption = sum(u.food_consumption for u in self.army.values())
        self.resources.food -= int(total_food_consumption * hours)
        self.resources.food = max(0, self.resources.food)
        
        self.last_resource_update = current_time
    
    def get_total_attack_power(self) -> int:
        """Calculate total army attack power"""
        total = 0
        for unit in self.army.values():
            total += unit.total_attack * unit.count
        return total
    
    def get_total_defense_power(self) -> int:
        """Calculate total defense power (army + defensive buildings)"""
        army_defense = sum(u.total_defense * u.count for u in self.army.values())
        
        # Add defensive building bonuses
        tower = self.buildings.get(BuildingType.TOWER)
        moat = self.buildings.get(BuildingType.MOAT)
        
        building_defense = 0
        if tower:
            building_defense += tower.current_effects.ranged_defense
        if moat:
            # Moat reduces enemy attack, modeled as effective defense
            building_defense += int(self.get_total_attack_power() * moat.current_effects.melee_damage_reduction)
        
        return army_defense + building_defense
    
    def get_total_loot_capacity(self) -> int:
        return sum(u.total_loot_capacity for u in self.army.values())
    
    def can_train_unit(self, unit_type: UnitType) -> tuple[bool, str]:
        """Check if unit can be trained"""
        unit_def = UNIT_DEFINITIONS[unit_type]
        
        # Check required building
        required_building_type = BuildingType(unit_def.required_building)
        building = self.buildings.get(required_building_type)
        if not building or building.level == 0:
            return False, f"Requires {required_building_type.value} level 1+"
        
        # Check resources
        cost = Resources(food=unit_def.food_cost)
        if not self.resources.can_afford(cost):
            return False, f"Not enough food (need {unit_def.food_cost})"
        
        # Check population
        if self.population >= self.max_population:
            return False, "Population limit reached"
        
        return True, "OK"
    
    def train_unit(self, unit_type: UnitType, count: int = 1) -> tuple[bool, str]:
        """Train units"""
        can, msg = self.can_train_unit(unit_type)
        if not can:
            return False, msg
        
        unit_def = UNIT_DEFINITIONS[unit_type]
        total_cost = unit_def.food_cost * count
        
        if not self.resources.can_afford(Resources(food=total_cost)):
            return False, f"Not enough food for {count} units"
        
        self.resources.deduct(Resources(food=total_cost))
        
        if unit_type not in self.army:
            self.army[unit_type] = Unit(unit_type=unit_type)
        self.army[unit_type].count += count
        self.population += count
        
        # Apply blacksmith bonuses
        blacksmith = self.buildings.get(BuildingType.BLACKSMITH)
        if blacksmith and blacksmith.level > 0:
            self.army[unit_type].attack_bonus = blacksmith.current_effects.unit_attack_bonus
            self.army[unit_type].defense_bonus = blacksmith.current_effects.unit_defense_bonus
        
        return True, f"Training {count} {unit_type.value}(s)"
    
    def can_build(self, building_type: BuildingType) -> tuple[bool, str]:
        """Check if building can be constructed/upgraded"""
        building = self.buildings.get(building_type)
        if not building:
            building = Building(building_type=building_type)
        
        if not building.can_upgrade:
            return False, "Building at max level or already building"
        
        # Check prerequisites
        can, msg = check_prerequisites(self.buildings, building_type)
        if not can:
            return False, msg
        
        # Check resources
        cost = building.next_level_cost
        resources_cost = Resources(
            food=cost.food,
            wood=cost.wood,
            stone=cost.stone,
            gold=cost.gold,
        )
        if not self.resources.can_afford(resources_cost):
            return False, f"Not enough resources (food: {cost.food}, wood: {cost.wood}, stone: {cost.stone}, gold: {cost.gold})"
        
        return True, "OK"
    
    def start_building(self, building_type: BuildingType) -> tuple[bool, str]:
        """Start building/upgrading"""
        can, msg = self.can_build(building_type)
        if not can:
            return False, msg
        
        building = self.buildings[building_type]
        cost = building.next_level_cost
        self.resources.deduct(Resources(
            food=cost.food,
            wood=cost.wood,
            stone=cost.stone,
            gold=cost.gold,
        ))
        
        building.is_building = True
        building.build_finish_time = int(time.time()) + building.next_level_time
        
        return True, f"Building {building.name} to level {building.level + 1}"
    
    def complete_building(self, building_type: BuildingType) -> bool:
        """Complete building if time has passed"""
        building = self.buildings.get(building_type)
        if not building or not building.is_building:
            return False
        
        if int(time.time()) >= building.build_finish_time:
            building.level += 1
            building.is_building = False
            building.build_finish_time = 0
            
            # Update population capacity from farms
            if building_type == BuildingType.FARM:
                self.max_population = building.current_effects.population_capacity
            
            return True
        return False
    
    def process_all_buildings(self):
        """Process all building queues"""
        for btype in BuildingType:
            self.complete_building(btype)
    
    def apply_blacksmith_bonuses(self):
        """Apply blacksmith upgrades to all units"""
        blacksmith = self.buildings.get(BuildingType.BLACKSMITH)
        if blacksmith and blacksmith.level > 0:
            for unit in self.army.values():
                unit.attack_bonus = blacksmith.current_effects.unit_attack_bonus
                unit.defense_bonus = blacksmith.current_effects.unit_defense_bonus
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "coordinates": self.coordinates,
            "resources": self.resources.to_dict(),
            "resource_production": self.resource_production.to_dict(),
            "last_resource_update": self.last_resource_update,
            "population": self.population,
            "max_population": self.max_population,
            "buildings": {k.value: v.to_dict() for k, v in self.buildings.items()},
            "army": {k.value: v.to_dict() for k, v in self.army.items()},
            "attack_level": self.attack_level,
            "defense_level": self.defense_level,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Village':
        village = cls(
            name=data.get("name", "My Village"),
            coordinates=tuple(data.get("coordinates", [0, 0])),
            resources=Resources.from_dict(data.get("resources", {})),
            resource_production=Resources.from_dict(data.get("resource_production", {})),
            last_resource_update=data.get("last_resource_update", int(time.time())),
            population=data.get("population", 0),
            max_population=data.get("max_population", 0),
        )
        
        # Load buildings
        for btype_str, bdata in data.get("buildings", {}).items():
            btype = BuildingType(btype_str)
            village.buildings[btype] = Building.from_dict(bdata)
        
        # Load army
        for utype_str, udata in data.get("army", {}).items():
            utype = UnitType(utype_str)
            village.army[utype] = Unit.from_dict(udata)
        
        village.attack_level = data.get("attack_level", 0)
        village.defense_level = data.get("defense_level", 0)
        
        return village


class GameState:
    """Global game state manager"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.state_file = self.data_dir / "game_state.json"
        self.village: Optional[Village] = None
        self.load()
    
    def load(self) -> bool:
        """Load game state from file"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                self.village = Village.from_dict(data)
                return True
            except Exception as e:
                print(f"Failed to load game state: {e}")
        return False
    
    def save(self):
        """Save game state to file"""
        if self.village:
            try:
                with open(self.state_file, 'w') as f:
                    json.dump(self.village.to_dict(), f, indent=2)
            except Exception as e:
                print(f"Failed to save game state: {e}")
    
    def new_game(self, village_name: str = "My Village") -> Village:
        """Create new game"""
        self.village = Village(name=village_name)
        # Start with a level 1 farm
        self.village.buildings[BuildingType.FARM] = Building(
            building_type=BuildingType.FARM, level=1
        )
        self.village.max_population = 20
        self.save()
        return self.village
    
    def tick(self):
        """Game loop tick - call periodically"""
        if self.village:
            self.village.update_resources()
            self.village.process_all_buildings()
            self.village.apply_blacksmith_bonuses()
            self.save()