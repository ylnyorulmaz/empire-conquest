"""
Building definitions for Empire Conquest.
Resource, military, upgrade, and defensive buildings.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum


class BuildingType(Enum):
    # Resource buildings
    FARM = "farm"
    
    # Military buildings
    BARRACKS = "barracks"
    ARCHERY_RANGE = "archery_range"
    STABLE = "stable"
    
    # Upgrade buildings
    BLACKSMITH = "blacksmith"
    
    # Defensive buildings
    TOWER = "tower"
    MOAT = "moat"


@dataclass
class BuildingCost:
    """Resource costs for building construction/upgrade"""
    food: int = 0
    wood: int = 0
    stone: int = 0
    gold: int = 0


@dataclass
class BuildingEffect:
    """Effects provided by this building at a given level"""
    food_production: int = 0          # Farm
    population_capacity: int = 0      # Farm
    training_speed_bonus: float = 1.0 # Barracks/Archery Range/Stable
    unit_attack_bonus: int = 0        # Blacksmith
    unit_defense_bonus: int = 0       # Blacksmith
    ranged_defense: int = 0           # Tower
    melee_damage_reduction: float = 0 # Moat
    recruitment_slots: int = 0        # Military buildings


@dataclass
class BuildingDefinition:
    """Complete building definition with costs and effects per level"""
    name: str
    description: str
    base_cost: BuildingCost
    cost_multiplier: float = 1.5
    base_build_time: int = 60  # seconds
    max_level: int = 20
    effects_per_level: Dict[int, BuildingEffect] = field(default_factory=dict)
    prerequisite_buildings: Dict[str, int] = field(default_factory=dict)  # building_type -> min_level
    
    def get_cost_at_level(self, level: int) -> BuildingCost:
        """Calculate cost for a specific level"""
        if level <= 0:
            return BuildingCost()
        mult = self.cost_multiplier ** (level - 1)
        return BuildingCost(
            food=int(self.base_cost.food * mult),
            wood=int(self.base_cost.wood * mult),
            stone=int(self.base_cost.stone * mult),
            gold=int(self.base_cost.gold * mult),
        )
    
    def get_build_time(self, level: int) -> int:
        """Calculate build time for a specific level"""
        return int(self.base_build_time * (self.cost_multiplier ** (level - 1)))
    
    def get_effects_at_level(self, level: int) -> BuildingEffect:
        """Get cumulative effects at a specific level"""
        total = BuildingEffect()
        for lvl in range(1, level + 1):
            if lvl in self.effects_per_level:
                eff = self.effects_per_level[lvl]
                total.food_production += eff.food_production
                total.population_capacity += eff.population_capacity
                total.training_speed_bonus += eff.training_speed_bonus - 1.0
                total.unit_attack_bonus += eff.unit_attack_bonus
                total.unit_defense_bonus += eff.unit_defense_bonus
                total.ranged_defense += eff.ranged_defense
                total.melee_damage_reduction += eff.melee_damage_reduction
                total.recruitment_slots += eff.recruitment_slots
        return total


# Building definitions
BUILDING_DEFINITIONS: Dict[BuildingType, BuildingDefinition] = {
    BuildingType.FARM: BuildingDefinition(
        name="Farm",
        description="Produces food and supports population growth",
        base_cost=BuildingCost(food=0, wood=50, stone=20, gold=10),
        cost_multiplier=1.5,
        base_build_time=30,
        max_level=20,
        effects_per_level={
            1: BuildingEffect(food_production=10, population_capacity=20),
            # Each level adds more
        },
        prerequisite_buildings={},
    ),
    
    BuildingType.BARRACKS: BuildingDefinition(
        name="Barracks",
        description="Trains peasants, warriors, and pikemen",
        base_cost=BuildingCost(food=100, wood=100, stone=50, gold=20),
        cost_multiplier=1.6,
        base_build_time=120,
        max_level=20,
        effects_per_level={
            1: BuildingEffect(training_speed_bonus=1.0, recruitment_slots=1),
        },
        prerequisite_buildings={BuildingType.FARM.value: 1},
    ),
    
    BuildingType.ARCHERY_RANGE: BuildingDefinition(
        name="Archery Range",
        description="Trains archers",
        base_cost=BuildingCost(food=150, wood=150, stone=50, gold=50),
        cost_multiplier=1.7,
        base_build_time=180,
        max_level=20,
        effects_per_level={
            1: BuildingEffect(training_speed_bonus=1.0, recruitment_slots=1),
        },
        prerequisite_buildings={BuildingType.BARRACKS.value: 2, BuildingType.FARM.value: 2},
    ),
    
    BuildingType.STABLE: BuildingDefinition(
        name="Stable",
        description="Trains knights",
        base_cost=BuildingCost(food=300, wood=200, stone=100, gold=100),
        cost_multiplier=1.8,
        base_build_time=300,
        max_level=20,
        effects_per_level={
            1: BuildingEffect(training_speed_bonus=1.0, recruitment_slots=1),
        },
        prerequisite_buildings={BuildingType.BARRACKS.value: 5, BuildingType.FARM.value: 5},
    ),
    
    BuildingType.BLACKSMITH: BuildingDefinition(
        name="Blacksmith",
        description="Upgrades unit attack and defense",
        base_cost=BuildingCost(food=200, wood=100, stone=150, gold=50),
        cost_multiplier=1.6,
        base_build_time=240,
        max_level=20,
        effects_per_level={
            1: BuildingEffect(unit_attack_bonus=1, unit_defense_bonus=1),
        },
        prerequisite_buildings={BuildingType.BARRACKS.value: 3},
    ),
    
    BuildingType.TOWER: BuildingDefinition(
        name="Watchtower",
        description="Provides ranged defense against attackers",
        base_cost=BuildingCost(food=50, wood=100, stone=200, gold=30),
        cost_multiplier=1.5,
        base_build_time=120,
        max_level=10,
        effects_per_level={
            1: BuildingEffect(ranged_defense=10),
        },
        prerequisite_buildings={BuildingType.FARM.value: 3},
    ),
    
    BuildingType.MOAT: BuildingDefinition(
        name="Moat",
        description="Reduces effectiveness of enemy melee attacks",
        base_cost=BuildingCost(food=30, wood=50, stone=300, gold=20),
        cost_multiplier=1.5,
        base_build_time=180,
        max_level=10,
        effects_per_level={
            1: BuildingEffect(melee_damage_reduction=0.1),  # 10% reduction
        },
        prerequisite_buildings={BuildingType.FARM.value: 4, BuildingType.TOWER.value: 1},
    ),
}


@dataclass
class Building:
    """Instance of a building in player's village"""
    building_type: BuildingType
    level: int = 0
    is_building: bool = False
    build_finish_time: int = 0  # Unix timestamp
    
    @property
    def definition(self) -> BuildingDefinition:
        return BUILDING_DEFINITIONS[self.building_type]
    
    @property
    def name(self) -> str:
        return self.definition.name
    
    @property
    def next_level_cost(self) -> 'BuildingCost':
        return self.definition.get_cost_at_level(self.level + 1)
    
    @property
    def next_level_time(self) -> int:
        return self.definition.get_build_time(self.level + 1)
    
    @property
    def current_effects(self) -> BuildingEffect:
        return self.definition.get_effects_at_level(self.level)
    
    @property
    def can_upgrade(self) -> bool:
        return self.level < self.definition.max_level and not self.is_building
    
    def to_dict(self) -> dict:
        return {
            "building_type": self.building_type.value,
            "level": self.level,
            "is_building": self.is_building,
            "build_finish_time": self.build_finish_time,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Building':
        return cls(
            building_type=BuildingType(data["building_type"]),
            level=data.get("level", 0),
            is_building=data.get("is_building", False),
            build_finish_time=data.get("build_finish_time", 0),
        )


def get_building_definition(building_type: BuildingType) -> BuildingDefinition:
    return BUILDING_DEFINITIONS[building_type]


def check_prerequisites(player_buildings: Dict[BuildingType, 'Building'], 
                        building_type: BuildingType) -> tuple[bool, str]:
    """Check if player meets prerequisites for building"""
    definition = BUILDING_DEFINITIONS[building_type]
    for prereq_type_str, min_level in definition.prerequisite_buildings.items():
        prereq_type = BuildingType(prereq_type_str)
        if prereq_type not in player_buildings:
            return False, f"Requires {prereq_type_str} level {min_level}"
        if player_buildings[prereq_type].level < min_level:
            return False, f"Requires {prereq_type_str} level {min_level} (current: {player_buildings[prereq_type].level})"
    return True, "OK"