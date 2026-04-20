import
from
from
from
import
from
import
import
import
import
import
import
import
from
from

class Layer14_Worldbuilding:
    """
    Layer 14: Autopoietic Worldbuilding and Normative Pluriverses
    
    Creates self-maintaining worlds with embedded governance.
    Worlds can generate, sustain, and modify their own conditions.
    
    Uitbreidingen:
    - World history
    - Agent tracking
    - Sustainability metrics
    - Configurable parameters
    """
    
    def __init__(self, layer13, config: Optional[Dict] = None):
        self.layer13 = layer13
        self.worlds: Dict[str, SimulatedWorld] = {}
        self.world_counter = 0
        
        # Metrics
        self.metrics = {
            'worlds_created': 0,
            'total_steps': 0,
            'avg_sustainability': 0.0,
            'autopoietic_worlds': 0
        }
        
        # Configuratie
        self.config = config or {}
        self.max_history = self.config.get('max_history', 100)
        self.default_physics = self.config.get('physics', {
            'gravity': 9.8,
            'resource_regeneration_rate': 0.1,
            'energy_dissipation': 0.05
        })
        
    @handle_hardware_errors(default_return=None)
    def create_world(self, 
                    physics_rules: Optional[Dict] = None,
                    initial_agents: int = 10,
                    normative_constraints: Optional[List[str]] = None,
                    name: Optional[str] = None) -> SimulatedWorld:
        """
        Generate a new simulated world with autopoietic properties.
        """
        world_id = name or f"world_{self.world_counter}"
        self.world_counter += 1
        
        # Default physics
        if physics_rules is None:
            physics_rules = self.default_physics.copy()
        
        # Initialize agents
        agents = []
        for i in range(initial_agents):
            agents.append({
                'id': f"agent_{i}_{world_id}",
                'energy': 100.0,
                'position': np.random.rand(3).tolist(),
                'velocity': (np.random.randn(3) * 0.1).tolist(),
                'age': 0,
                'resources_gathered': 0
            })
        
        # Initialize resources
        resources = {
            'energy': 1000.0,
            'matter': 1000.0,
            'information': 1000.0
        }
        
        # Default normative constraints
        if normative_constraints is None:
            normative_constraints = [
                'preserve_biodiversity',
                'maintain_energy_balance',
                'ensure_agent_welfare'
            ]
        
        world = SimulatedWorld(
            id=world_id,
            physics_rules=physics_rules,
            agent_population=agents,
            resource_state=resources,
            normative_constraints=normative_constraints,
            autopoietic_closure=False,
            sustainability_score=0.5
        )
        
        self.worlds[world_id] = world
        self.metrics['worlds_created'] += 1
        
        logger.info(f"Layer 14: Created world '{world_id}' with {initial_agents} agents")
        
        return world
    
    def step_world(self, world_id: str, timesteps: int = 1):
        """
        Evolve world dynamics for specified timesteps.
        Implements autopoietic self-maintenance.
        """
        world = self.worlds[world_id]
        
        for step in range(timesteps):
            # Update resources (regeneration)
            regen_rate = world.physics_rules['resource_regeneration_rate']
            for resource, amount in world.resource_state.items():
                world.resource_state[resource] = amount * (1 + regen_rate)
                # Cap resources
                world.resource_state[resource] = min(world.resource_state[resource], 2000.0)
            
            # Update agents
            for agent in world.agent_population:
                # Energy dissipation
                dissipation = world.physics_rules['energy_dissipation']
                agent['energy'] *= (1 - dissipation)
                agent['age'] += 1
                
                # Agent harvests resources
                if agent['energy'] < 80:
                    harvest = min(10, world.resource_state['energy'])
                    agent['energy'] += harvest
                    world.resource_state['energy'] -= harvest
                    agent['resources_gathered'] += harvest
                
                # Update position
                pos = np.array(agent['position'])
                vel = np.array(agent['velocity'])
                new_pos = pos + vel * 0.1
                # Boundary conditions
                agent['position'] = np.clip(new_pos, 0, 10).tolist()
            
            # Remove dead agents (energy <= 0)
            world.agent_population = [a for a in world.agent_population if a['energy'] > 0]
            
            # Check autopoietic closure
            world.autopoietic_closure = self._check_autopoiesis(world)
            
            # Compute sustainability
            world.sustainability_score = self._compute_sustainability(world)
            
            # Record history
            if len(world.history) < self.max_history:
                world.history.append({
                    'step': world.steps + step,
                    'agents': len(world.agent_population),
                    'resources': world.resource_state.copy(),
                    'sustainability': world.sustainability_score,
                    'autopoietic': world.autopoietic_closure
                })
            
            world.steps += 1
        
        # Update metrics
        self.metrics['total_steps'] += timesteps
        self.metrics['avg_sustainability'] = (
            self.metrics['avg_sustainability'] * 0.95 + 
            world.sustainability_score * 0.05
        )
        if world.autopoietic_closure:
            self.metrics['autopoietic_worlds'] += 1
        
        logger.debug(f"Layer 14: Stepped world '{world_id}' {timesteps} steps "
                    f"(sustainability: {world.sustainability_score:.2f})")
    
    def _check_autopoiesis(self, world: SimulatedWorld) -> bool:
        """
        Check if world maintains self-producing cycles.
        Autopoiesis = self-maintenance without external input.
        """
        # Check resource stability
        resource_stable = all(v > 100 for v in world.resource_state.values())
        
        # Check agent population viability
        if not world.agent_population:
            return False
        
        viable_agents = sum(1 for a in world.agent_population if a['energy'] > 20)
        population_viable = viable_agents > len(world.agent_population) * 0.5
        
        return resource_stable and population_viable
    
    def _compute_sustainability(self, world: SimulatedWorld) -> float:
        """Measure world sustainability across multiple dimensions."""
        # Resource sustainability
        total_resources = sum(world.resource_state.values())
        resource_score = min(total_resources / 3000.0, 1.0)
        
        # Agent welfare
        if world.agent_population:
            avg_energy = np.mean([a['energy'] for a in world.agent_population])
            welfare_score = min(avg_energy / 100.0, 1.0)
        else:
            welfare_score = 0.0
        
        # Population stability
        if hasattr(world, 'history') and len(world.history) > 1:
            prev_pop = world.history[-2].get('agents', 0) if len(world.history) > 1 else 0
            curr_pop = len(world.agent_population)
            if prev_pop > 0:
                stability = min(curr_pop / prev_pop, 1.0)
            else:
                stability = 1.0 if curr_pop > 0 else 0.0
        else:
            stability = 1.0
        
        # Autopoietic bonus
        autopoietic_bonus = 0.2 if world.autopoietic_closure else 0.0
        
        return (resource_score + welfare_score + stability) / 3 + autopoietic_bonus
    
    def apply_normative_constraint(self, world_id: str, constraint: str, strength: float = 1.0):
        """
        Apply normative constraints to world evolution.
        Embedded ethics that shape world dynamics.
        """
        world = self.worlds[world_id]
        
        if constraint == 'preserve_biodiversity':
            # Boost agent reproduction if population low
            if len(world.agent_population) < 5:
                new_agent = {
                    'id': f"agent_{len(world.agent_population)}_{world_id}",
                    'energy': 100.0,
                    'position': np.random.rand(3).tolist(),
                    'velocity': (np.random.randn(3) * 0.1).tolist(),
                    'age': 0,
                    'resources_gathered': 0
                }
                world.agent_population.append(new_agent)
                logger.debug(f"Layer 14: Applied constraint '{constraint}' - added agent")
        
        elif constraint == 'maintain_energy_balance':
            # Redistribute resources if imbalanced
            total_energy = world.resource_state['energy']
            if total_energy < 500:
                world.resource_state['energy'] += 100 * strength
                logger.debug(f"Layer 14: Applied constraint '{constraint}' - added energy")
        
        elif constraint == 'ensure_agent_welfare':
            # Support struggling agents
            for agent in world.agent_population:
                if agent['energy'] < 30:
                    agent['energy'] += 20 * strength
            logger.debug(f"Layer 14: Applied constraint '{constraint}' - supported agents")
    
    def get_world_state(self, world_id: str) -> Dict[str, Any]:
        """Haal volledige wereld staat op."""
        world = self.worlds.get(world_id)
        if not world:
            return {}
        
        return {
            'id': world.id,
            'steps': world.steps,
            'agents': len(world.agent_population),
            'resources': world.resource_state,
            'sustainability': world.sustainability_score,
            'autopoietic': world.autopoietic_closure,
            'history': world.history[-10:]  # Laatste 10 stappen
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Haal statistieken op."""
        return {
            'metrics': self.metrics,
            'worlds': [
                {
                    'id': w.id,
                    'steps': w.steps,
                    'agents': len(w.agent_population),
                    'sustainability': w.sustainability_score,
                    'autopoietic': w.autopoietic_closure
                }
                for w in self.worlds.values()
            ]
        }


# ============================================================================
# LAYER 15: ETHICAL CONVERGENCE AND RESPONSIBILITY (UITGEBREID)
# ============================================================================

@dataclass