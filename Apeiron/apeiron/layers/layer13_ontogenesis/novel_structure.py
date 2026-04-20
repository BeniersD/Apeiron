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

class NovelStructure:
    """Represents a genuinely new emergent structure."""
    id: str
    origin_cycle: int
    structure_type: str
    generative_rules: List[str]
    stability_score: float
    causal_efficacy: float
    created_at: float = field(default_factory=time.time)
    iterations: int = 0
    
