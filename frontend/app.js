/**
 * Empire Conquest - Frontend Application
 * OGame-inspired medieval browser strategy game
 */

const API_BASE = '/api';

// State
let state = {
    village: null,
    buildings: {},
    army: {},
    units: {},
    map: null
};

// DOM Elements
const elements = {
    villageName: document.getElementById('village-name'),
    villageCoords: document.getElementById('village-coords'),
    resources: {
        food: document.getElementById('food'),
        wood: document.getElementById('wood'),
        stone: document.getElementById('stone'),
        gold: document.getElementById('gold'),
        population: document.getElementById('population'),
        maxPopulation: document.getElementById('max-population')
    },
    buildingsList: document.getElementById('buildings-list'),
    buildingSlots: document.getElementById('building-slots'),
    armyUnits: document.getElementById('army-units'),
    unitsList: document.getElementById('units-list'),
    totalAttack: document.getElementById('total-attack'),
    totalDefense: document.getElementById('total-defense'),
    totalLoot: document.getElementById('total-loot'),
    armyPop: document.getElementById('army-pop'),
    categoryBtns: document.querySelectorAll('.category-btn'),
    buildingSlots: document.getElementById('building-slots'),
    btnTick: document.getElementById('btn-tick'),
    btnSave: document.getElementById('btn-save'),
    btnMap: document.getElementById('btn-map'),
    btnAttack: document.getElementById('btn-attack'),
    attackTarget: document.getElementById('attack-target'),
    modalMap: document.getElementById('modal-map'),
    modalBuilding: document.getElementById('modal-building'),
    modalAttackResult: document.getElementById('modal-attack-result'),
    closeMap: document.getElementById('close-map'),
    closeBuilding: document.getElementById('close-building'),
    closeAttackResult: document.getElementById('close-attack-result'),
    mapContent: document.getElementById('map-content'),
    modalBuildingTitle: document.getElementById('modal-building-title'),
    modalBuildingContent: document.getElementById('modal-building-content'),
    attackResultContent: document.getElementById('attack-result-content'),
    notifications: document.getElementById('notifications')
};

// Current building category filter
let currentCategory = 'resource';

// Category mapping
const buildingCategories = {
    resource: [BuildingType.FARM],
    military: [BuildingType.BARRACKS, BuildingType.ARCHERY_RANGE, BuildingType.STABLE],
    upgrade: [BuildingType.BLACKSMITH],
    defense: [BuildingType.TOWER, BuildingType.MOAT]
};

// Initialize
async function init() {
    setupEventListeners();
    await loadUnits();
    await loadBuildings();
    await loadState();
    startAutoTick();
    showNotification('Welcome to Empire Conquest!', 'info');
}

// Event Listeners
function setupEventListeners() {
    // Category buttons
    elements.categoryBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            elements.categoryBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentCategory = btn.dataset.category;
            renderBuildings();
        });
    });

    // Header actions
    elements.btnTick.addEventListener('click', doTick);
    elements.btnSave.addEventListener('click', saveGame);
    elements.btnMap.addEventListener('click', () => openModal(elements.modalMap));
    elements.btnAttack.addEventListener('click', doAttack);

    // Modals
    elements.closeMap.addEventListener('click', () => closeModal(elements.modalMap));
    elements.closeBuilding.addEventListener('click', () => closeModal(elements.modalBuilding));
    elements.closeAttackResult.addEventListener('click', () => closeModal(elements.modalAttackResult));

    // Close modals on backdrop click
    [elements.modalMap, elements.modalBuilding, elements.modalAttackResult].forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) closeModal(modal);
        });
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            [elements.modalMap, elements.modalBuilding, elements.modalAttackResult].forEach(closeModal);
        }
        if (e.key === 't' || e.key === 'T') doTick();
        if (e.key === 's' && (e.ctrlKey || e.metaKey)) {
            e.preventDefault();
            saveGame();
        }
    });
}

// API Helpers
async function api(endpoint, options = {}) {
    const response = await fetch(`${API_BASE}${endpoint}`, {
        headers: { 'Content-Type': 'application/json' },
        ...options
    });
    if (!response.ok) {
        const err = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(err.detail || `HTTP ${response.status}`);
    }
    return response.json();
}

// Load initial data
async function loadUnits() {
    try {
        const data = await api('/units');
        state.units = data;
    } catch (e) {
        console.error('Failed to load units:', e);
    }
}

async function loadBuildings() {
    try {
        const data = await api('/buildings');
        state.buildings = data;
    } catch (e) {
        console.error('Failed to load buildings:', e);
    }
}

async function loadState() {
    try {
        state.village = await api('/state');
        renderAll();
    } catch (e) {
        // No active game, show new game prompt
        showNewGamePrompt();
    }
}

// Rendering
function renderAll() {
    if (!state.village) return;
    renderResources();
    renderVillageInfo();
    renderBuildings();
    renderBuildingSlots();
    renderArmy();
    renderUnits();
}

function renderResources() {
    const r = state.village.resources;
    elements.resources.food.textContent = formatNumber(r.food);
    elements.resources.wood.textContent = formatNumber(r.wood);
    elements.resources.stone.textContent = formatNumber(r.stone);
    elements.resources.gold.textContent = formatNumber(r.gold);
    elements.resources.population.textContent = state.village.population;
    elements.resources.maxPopulation.textContent = state.village.max_population;
}

function renderVillageInfo() {
    elements.villageName.textContent = state.village.name;
    elements.villageCoords.textContent = `(${state.village.coordinates[0]}, ${state.village.coordinates[1]})`;
}

function renderBuildings() {
    const categoryBuildings = buildingCategories[currentCategory] || [];
    elements.buildingsList.innerHTML = '';

    categoryBuildings.forEach(btype => {
        const building = state.village.buildings[btype];
        const defn = state.buildings[btype];
        if (!defn) return;

        const card = document.createElement('div');
        card.className = `building-card ${building.level === 0 ? '' : ''} ${building.is_building ? 'building' : ''}`;
        card.innerHTML = `
            <h3>
                ${defn.name}
                ${building.level > 0 ? `<span class="building-level">Lv. ${building.level}</span>` : '<span class="building-level" style="background: var(--text-muted);">Not Built</span>'}
            </h3>
            <div class="building-info">
                ${building.level > 0 ? `<span class="building-time">⏱️ ${formatTime(building.next_level_time)}</span>` : ''}
                ${building.level < defn.max_level ? `
                    <span class="building-cost">🌾 ${formatNumber(building.next_level_cost.food)}</span>
                    <span class="building-cost">🪵 ${formatNumber(building.next_level_cost.wood)}</span>
                    <span class="building-cost">🪨 ${formatNumber(building.next_level_cost.stone)}</span>
                    <span class="building-cost">💰 ${formatNumber(building.next_level_cost.gold)}</span>
                ` : '<span style="color: var(--accent-green);">Max Level</span>'}
            </div>
            ${building.is_building ? `
                <div style="margin-top: 0.5rem; font-size: 0.75rem; color: var(--accent-blue);">
                    🏗️ Building... finishes in ${formatTimeRemaining(building.build_finish_time)}
                </div>
            ` : ''}
        `;

        card.addEventListener('click', () => openBuildingModal(btype));
        elements.buildingsList.appendChild(card);
    });
}

function renderBuildingSlots() {
    const slotOrder = [
        BuildingType.FARM,
        BuildingType.BARRACKS,
        BuildingType.ARCHERY_RANGE,
        BuildingType.STABLE,
        BuildingType.BLACKSMITH,
        BuildingType.TOWER,
        BuildingType.MOAT
    ];

    elements.buildingSlots.innerHTML = '';

    slotOrder.forEach(btype => {
        const building = state.village.buildings[btype];
        const defn = state.buildings[btype];
        if (!defn) return;

        const slot = document.createElement('div');
        slot.className = `building-slot ${building.level > 0 ? 'occupied' : ''}`;
        slot.innerHTML = `
            <div class="slot-icon">${getBuildingIcon(btype)}</div>
            <div class="slot-name">${defn.name}</div>
            ${building.level > 0 ? `<div class="slot-level">Level ${building.level}</div>` : '<div class="slot-level">Empty</div>'}
        `;
        slot.addEventListener('click', () => openBuildingModal(btype));
        elements.buildingSlots.appendChild(slot);
    });
}

function renderArmy() {
    if (!state.village) return;

    // Update summary stats
    elements.totalAttack.textContent = formatNumber(state.village.getTotalAttackPower());
    elements.totalDefense.textContent = formatNumber(state.village.getTotalDefensePower());
    elements.totalLoot.textContent = formatNumber(state.village.getTotalLootCapacity());

    let armyPop = 0;
    elements.armyUnits.innerHTML = '';

    Object.entries(state.village.army).forEach(([utype, unit]) => {
        if (unit.count > 0) {
            armyPop += unit.count;
            const div = document.createElement('div');
            div.className = 'army-unit';
            div.innerHTML = `
                <span class="unit-count">${unit.count}</span>
                <span>${getUnitIcon(utype)} ${formatUnitName(utype)}</span>
                <span style="margin-left: auto; color: var(--text-muted); font-size: 0.7rem;">
                    Atk: ${unit.total_attack} | Def: ${unit.total_defense}
                </span>
            `;
            elements.armyUnits.appendChild(div);
        }
    });

    elements.armyPop.textContent = armyPop;
}

function renderUnits() {
    elements.unitsList.innerHTML = '';

    Object.entries(state.units).forEach(([utype, defn]) => {
        const card = document.createElement('div');
        card.className = 'unit-card';
        card.innerHTML = `
            <div class="unit-header">
                <h3>${getUnitIcon(utype)} ${formatUnitName(utype)}</h3>
                <span class="unit-cost">🌾 ${defn.food_cost}</span>
            </div>
            <div class="unit-stats">
                <span>⚔️ Atk: ${defn.attack}</span>
                <span>🛡️ Def: ${defn.defense}</span>
                <span>💰 Loot: ${defn.loot_capacity}</span>
                <span>⏱️ ${formatTime(defn.training_time)}</span>
                <span>🏗️ ${formatBuildingName(defn.required_building)}</span>
            </div>
            <button class="train-btn" onclick="trainUnit('${utype}')" ${!canTrainUnit(utype) ? 'disabled' : ''}>
                ${canTrainUnit(utype) ? 'Train' : 'Requirements Not Met'}
            </button>
        `;
        elements.unitsList.appendChild(card);
    });
}

// Building Modal
function openBuildingModal(btype) {
    const building = state.village.buildings[btype];
    const defn = state.buildings[btype];
    if (!defn) return;

    elements.modalBuildingTitle.textContent = `${getBuildingIcon(btype)} ${defn.name}`;

    let content = `
        <p style="color: var(--text-secondary); margin-bottom: 1rem;">${defn.description}</p>
        <div style="margin-bottom: 1rem;">
            <strong>Current Level: </strong>${building.level} / ${defn.max_level}
        </div>
    `;

    if (building.level < defn.max_level) {
        content += `
            <div style="background: var(--bg-tertiary); border: 1px solid var(--border-color); border-radius: 8px; padding: 1rem; margin-bottom: 1rem;">
                <h4 style="color: var(--accent-gold); margin-bottom: 0.5rem;">Next Level (${building.level + 1})</h4>
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.5rem; margin-bottom: 0.5rem;">
                    <span>🌾 Food: ${formatNumber(building.next_level_cost.food)}</span>
                    <span>🪵 Wood: ${formatNumber(building.next_level_cost.wood)}</span>
                    <span>🪨 Stone: ${formatNumber(building.next_level_cost.stone)}</span>
                    <span>💰 Gold: ${formatNumber(building.next_level_cost.gold)}</span>
                </div>
                <div style="margin-bottom: 0.5rem;">
                    <strong>Build Time: </strong>${formatTime(building.next_level_time)}
                </div>
        `;

        // Prerequisites
        if (Object.keys(defn.prerequisite_buildings).length > 0) {
            content += '<div style="margin-top: 0.5rem; font-size: 0.8rem; color: var(--text-muted);"><strong>Requires:</strong><br>';
            Object.entries(defn.prerequisite_buildings).forEach(([b, lvl]) => {
                const reqDef = state.buildings[BuildingType[b]];
                const reqBuilding = state.village.buildings[BuildingType[b]];
                const met = reqBuilding && reqBuilding.level >= lvl;
                content += `<span style="color: ${met ? 'var(--accent-green)' : 'var(--accent-red)'}">${reqDef?.name || b} Lv.${lvl} ${met ? '✓' : '✗'}</span><br>`;
            });
            content += '</div>';
        }

        content += `
                <button class="btn btn-primary btn-full" onclick="startBuilding('${btype}')" ${!canBuild(btype) ? 'disabled' : ''}>
                    ${state.village.buildings[btype].is_building ? 'Building...' : `Upgrade to Level ${building.level + 1}`}
                </button>
            </div>
        `;
    } else {
        content += `
            <div style="background: rgba(39, 174, 96, 0.1); border: 1px solid var(--accent-green); border-radius: 8px; padding: 1rem; text-align: center; color: var(--accent-green);">
                <strong>Maximum Level Reached!</strong>
            </div>
        `;
    }

    // Effects
    content += `
        <div style="margin-top: 1.5rem;">
            <h4 style="color: var(--accent-gold); margin-bottom: 0.5rem;">Effects at Current Level</h4>
            <div style="font-size: 0.85rem; color: var(--text-secondary);">
    `;

    const effects = building.current_effects;
    if (effects.food_production) content += `<div>🌾 Food Production: +${effects.food_production}/hr</div>`;
    if (effects.population_capacity) content += `<div>👥 Population Capacity: +${effects.population_capacity}</div>`;
    if (effects.training_speed_bonus > 0) content += `<div>⚔️ Training Speed: ${(effects.training_speed_bonus + 1).toFixed(1)}x</div>`;
    if (effects.recruitment_slots) content += `<div>🏗️ Recruitment Slots: +${effects.recruitment_slots}</div>`;
    if (effects.unit_attack_bonus) content += `<div>⚔️ Unit Attack Bonus: +${effects.unit_attack_bonus}</div>`;
    if (effects.unit_defense_bonus) content += `<div>🛡️ Unit Defense Bonus: +${effects.unit_defense_bonus}</div>`;
    if (effects.ranged_defense) content += `<div>🏰 Ranged Defense: +${effects.ranged_defense}</div>`;
    if (effects.melee_damage_reduction) content += `<div>🛡️ Melee Damage Reduction: ${(effects.melee_damage_reduction * 100).toFixed(0)}%</div>`;

    content += '</div></div>';

    elements.modalBuildingContent.innerHTML = content;
    openModal(elements.modalBuilding);
}

// Game Actions
async function doTick() {
    try {
        elements.btnTick.disabled = true;
        elements.btnTick.textContent = '⏱️ Processing...';
        const result = await api('/tick', { method: 'POST' });
        state.village = result.state;
        renderAll();
        showNotification('Game tick processed', 'success');
    } catch (e) {
        showNotification(e.message, 'error');
    } finally {
        elements.btnTick.disabled = false;
        elements.btnTick.textContent = '⏱️ Tick';
    }
}

async function saveGame() {
    try {
        await api('/tick', { method: 'POST' }); // Tick also saves
        showNotification('Game saved!', 'success');
    } catch (e) {
        showNotification(e.message, 'error');
    }
}

async function startBuilding(btype) {
    try {
        const result = await api('/build', {
            method: 'POST',
            body: JSON.stringify({ building_type: btype })
        });
        state.village = result.state;
        renderAll();
        closeModal(elements.modalBuilding);
        showNotification(`Building started!`, 'success');
    } catch (e) {
        showNotification(e.message, 'error');
    }
}

async function trainUnit(utype) {
    try {
        const result = await api('/train', {
            method: 'POST',
            body: JSON.stringify({ unit_type: utype, count: 1 })
        });
        state.village = result.state;
        renderAll();
        showNotification('Unit trained!', 'success');
    } catch (e) {
        showNotification(e.message, 'error');
    }
}

async function doAttack() {
    const target = elements.attackTarget.value.trim();
    if (!target) {
        showNotification('Enter a target village name or coordinates', 'error');
        return;
    }

    try {
        elements.btnAttack.disabled = true;
        elements.btnAttack.textContent = '⚔️ Attacking...';
        const result = await api('/attack', {
            method: 'POST',
            body: JSON.stringify({ target_village: target })
        });

        state.village = result.state;
        renderAll();

        const content = `
            <div style="text-align: center; padding: 1rem;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">${result.result === 'victory' ? '🏆' : '💀'}</div>
                <h3 style="color: ${result.result === 'victory' ? 'var(--accent-green)' : 'var(--accent-red)'};">
                    ${result.result === 'victory' ? 'VICTORY!' : 'DEFEAT'}
                </h3>
                <div style="margin: 1rem 0; display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                    <div style="background: var(--bg-primary); padding: 1rem; border-radius: 8px;">
                        <strong>Your Power:</strong> ${formatNumber(result.attacker_power)}
                    </div>
                    <div style="background: var(--bg-primary); padding: 1rem; border-radius: 8px;">
                        <strong>Enemy Power:</strong> ${formatNumber(result.defender_power)}
                    </div>
                </div>
                <div style="margin-top: 1rem;">
                    <strong>Loot Gained:</strong>
                    <div style="display: flex; gap: 1rem; justify-content: center; margin-top: 0.5rem;">
                        <span>🌾 ${formatNumber(result.loot.food)}</span>
                        <span>🪵 ${formatNumber(result.loot.wood)}</span>
                        <span>🪨 ${formatNumber(result.loot.stone)}</span>
                        <span>💰 ${formatNumber(result.loot.gold)}</span>
                    </div>
                </div>
                ${result.casualties > 0 ? `<div style="margin-top: 1rem; color: var(--accent-red);">Casualties: ${result.casualties} units lost</div>` : ''}
            </div>
        `;

        elements.attackResultContent.innerHTML = content;
        openModal(elements.modalAttackResult);
        elements.attackTarget.value = '';
        showNotification(result.result === 'victory' ? 'Victory!' : 'Defeat', result.result === 'victory' ? 'success' : 'error');

    } catch (e) {
        showNotification(e.message, 'error');
    } finally {
        elements.btnAttack.disabled = false;
        elements.btnAttack.textContent = '⚔️ Launch Attack';
    }
}

async function openMap() {
    try {
        const data = await api('/map');
        elements.mapContent.innerHTML = `
            <div style="margin-bottom: 1rem;">
                <strong>Your Village:</strong> ${data.current_village.name} at ${data.current_village.coordinates}
            </div>
            <div style="max-height: 400px; overflow-y: auto;">
                ${data.nearby_villages.map(v => `
                    <div style="background: var(--bg-tertiary); border: 1px solid var(--border-color); border-radius: 8px; padding: 0.75rem; margin-bottom: 0.5rem; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong>${v.name}</strong> (${v.coordinates[0]}, ${v.coordinates[1]})
                            <br><small style="color: var(--text-muted);">${v.player} • Pop: ${v.population}</small>
                        </div>
                        <button class="btn btn-danger" style="padding: 0.3rem 0.8rem; font-size: 0.8rem;" onclick="elements.attackTarget.value='${v.name}'; closeModal(elements.modalMap);">Attack</button>
                    </div>
                `).join('')}
            </div>
        `;
        openModal(elements.modalMap);
    } catch (e) {
        showNotification(e.message, 'error');
    }
}

// Modal Helpers
function openModal(modal) {
    modal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
}

function closeModal(modal) {
    modal.classList.add('hidden');
    document.body.style.overflow = '';
}

function closeAllModals() {
    [elements.modalMap, elements.modalBuilding, elements.modalAttackResult].forEach(closeModal);
}

// Helper Functions
function canTrainUnit(utype) {
    if (!state.village) return false;
    const defn = state.units[utype];
    if (!defn) return false;

    // Check required building
    const reqBuilding = state.village.buildings[defn.required_building];
    if (!reqBuilding || reqBuilding.level === 0) return false;

    // Check food
    if (state.village.resources.food < defn.food_cost) return false;

    // Check population
    if (state.village.population >= state.village.max_population) return false;

    return true;
}

function canBuild(btype) {
    if (!state.village) return false;
    const building = state.village.buildings[btype];
    if (!building || building.level >= state.buildings[btype].max_level || building.is_building) return false;

    // Check prerequisites
    const defn = state.buildings[btype];
    for (const [reqType, minLevel] of Object.entries(defn.prerequisite_buildings)) {
        const reqBuilding = state.village.buildings[BuildingType[reqType]];
        if (!reqBuilding || reqBuilding.level < minLevel) return false;
    }

    // Check resources
    const cost = building.next_level_cost;
    const r = state.village.resources;
    return r.food >= cost.food && r.wood >= cost.wood && r.stone >= cost.stone && r.gold >= cost.gold;
}

function getBuildingIcon(btype) {
    const icons = {
        [BuildingType.FARM]: '🌾',
        [BuildingType.BARRACKS]: '🏰',
        [BuildingType.ARCHERY_RANGE]: '🏹',
        [BuildingType.STABLE]: '🐎',
        [BuildingType.BLACKSMITH]: '⚒️',
        [BuildingType.TOWER]: '🗼',
        [BuildingType.MOAT]: '🌊'
    };
    return icons[btype] || '🏗️';
}

function getUnitIcon(utype) {
    const icons = {
        [UnitType.PEASANT]: '👨‍🌾',
        [UnitType.WARRIOR]: '⚔️',
        [UnitType.ARCHER]: '🏹',
        [UnitType.PIKEMAN]: '🛡️',
        [UnitType.KNIGHT]: '🤺'
    };
    return icons[utype] || '❓';
}

function formatUnitName(utype) {
    const names = {
        [UnitType.PEASANT]: 'Peasant',
        [UnitType.WARRIOR]: 'Warrior',
        [UnitType.ARCHER]: 'Archer',
        [UnitType.PIKEMAN]: 'Pikeman',
        [UnitType.KNIGHT]: 'Knight'
    };
    return names[utype] || utype;
}

function formatBuildingName(btype) {
    const names = {
        [BuildingType.FARM]: 'Farm',
        [BuildingType.BARRACKS]: 'Barracks',
        [BuildingType.ARCHERY_RANGE]: 'Archery Range',
        [BuildingType.STABLE]: 'Stable',
        [BuildingType.BLACKSMITH]: 'Blacksmith',
        [BuildingType.TOWER]: 'Tower',
        [BuildingType.MOAT]: 'Moat'
    };
    return names[btype] || btype;
}

function formatNumber(num) {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
}

function formatTime(seconds) {
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    return `${h}h ${m}m`;
}

function formatTimeRemaining(finishTime) {
    const remaining = finishTime - Date.now() / 1000;
    if (remaining <= 0) return '0s';
    return formatTime(Math.ceil(remaining));
}

function showNotification(message, type = 'info') {
    const notif = document.createElement('div');
    notif.className = `notification ${type}`;
    notif.textContent = message;
    elements.notifications.appendChild(notif);

    setTimeout(() => {
        notif.style.animation = 'slideIn 0.3s ease reverse';
        setTimeout(() => notif.remove(), 300);
    }, 4000);
}

function showNewGamePrompt() {
    const name = prompt('Enter your village name to start a new game:', 'My Village');
    if (name) {
        api('/new-game', {
            method: 'POST',
            body: JSON.stringify({ village_name: name })
        }).then(village => {
            state.village = village;
            renderAll();
            showNotification('New game started!', 'success');
        }).catch(e => showNotification(e.message, 'error'));
    }
}

// Auto-tick every 30 seconds
function startAutoTick() {
    setInterval(() => {
        if (state.village && !elements.btnTick.disabled) {
            doTick();
        }
    }, 30000);
}

// Global functions for inline onclick
window.trainUnit = trainUnit;
window.startBuilding = startBuilding;

// Start
document.addEventListener('DOMContentLoaded', init);