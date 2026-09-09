"""
Unit definitions for Empire Conquest.
Based on OGame-inspired medieval strategy game mechanics.
"""

from dataclasses import dataclass
from typing import Dict, List
from enum import Enum


class UnitType(Enum):
    PEASANT = "peasant"
    WARRIOR = "warrior"
    ARCHER = "archer"
    PIKEMAN = "pikeman"
    KNIGHT = "knight"


@dataclass
class UnitStats:
    """Base stats for a unit type"""
    loot_capacity: int
    attack: int
    defense: int
    food_cost: int
    training_time: int  # seconds
    required_building: str


# Unit definitions matching the spec
UNIT_DEFINITIONS: Dict[UnitType, UnitStats] = {
    UnitType.PEASANT: UnitStats(
        loot_capacity=10,
        attack=2,
        defense=4,
        food_cost=50,
        training_time=30,
        required_building="barracks"
    ),
    UnitType.WARRIOR: UnitStats(
        loot_capacity=6,
        attack=4,
        defense=6,
        food_cost=100,
        training_time=60,
        required_building="barracks"
    ),
    UnitType.ARCHER: UnitStats(
        loot_capacity=4,
        attack=8,
        defense=3,
        food_cost=120,
        training_time=90,
        required_building="archery_range"
    ),
    UnitType.PIKEMAN: UnitStats(
        loot_capacity=5,
        attack=6,
        defense=8,
        food_cost=110,
        training_time=80,
        required_building="barracks"
    ),
    UnitType.KNIGHT: UnitStats(
        loot_capacity=8,
        attack=12,
        defense=12,
        food_cost=250,
        training_time=180,
        required_building="stable"
    ),
}


@dataclass
class Unit:
    """Instance of a unit in player's army"""
    unit_type: UnitType
    count: int = 0
    attack_bonus: int = 0  # from blacksmith upgrades
    defense_bonus: int = 0  # from blacksmith upgrades

    @property
    def total_attack(self) -> int:
        base = UNIT_DEFINITIONS[self.unit_type].attack
        return base + self.attack_bonus

    @property
    def total_defense(self) -> int:
        base = UNIT_DEFINITIONS[self.unit_type].defense
        return base + self.defense_bonus

    @property
    def total_loot_capacity(self) -> int:
        return UNIT_DEFINITIONS[self.unit_type].loot_capacity * self.count

    @property
    def food_consumption(self) -> int:
        """Food consumed per hour"""
        return UNIT_DEFINITIONS[self.unit_type].food_cost * self.count // 10

    def to_dict(self) -> dict:
        return {
            "unit_type": self.unit_type.value,
            "count": self.count,
            "attack_bonus": self.attack_bonus,
            "defense_bonus": self.defense_bonus,
            "total_attack": self.total_attack,
            "total_defense": self.total_defense,
            "total_loot_capacity": self.total_loot_capacity,
            "food_consumption_per_hour": self.food_consumption,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Unit':
        return cls(
            unit_type=UnitType(data["unit_type"]),
            count=data.get("count", 0),
            attack_bonus=data.get("attack_bonus", 0),
            defense_bonus=data.get("defense_bonus", 0),
        )


def get_unit_cost(unit_type: UnitType) -> int:
    """Get food cost for one unit"""
    return UNIT_DEFINITIONS[unit_type].food_cost


def get_training_time(unit_type: UnitType, barracks_level: int = 1) -> int:
    """Get training time in seconds, reduced by barracks level"""
    base_time = UNIT_DEFINITIONS[unit_type].training_time
    return max(5, base_time // barracks_level)


def get_required_building(unit_type: UnitType) -> str:
    """Get required building for training this unit"""
    return UNIT_DEFINITIONS[unit_type].required_building