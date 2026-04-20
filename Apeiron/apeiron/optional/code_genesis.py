"""
CODE GENESIS - Zelf-modificerende broncode voor Apeiron
================================================================================
Laat het systeem zijn eigen Python-bestanden herschrijven. Dit is de ultieme
vorm van ontogenese - het systeem creëert zijn eigen architectuur, voegt nieuwe
lagen toe, en evolueert zijn eigen broncode.

Theoretische basis:
- Metaprogrammering: code die code schrijft
- Evolutionaire architectuur: systeem past zichzelf aan
- Recursieve zelfverbetering: code verbetert code
- Veilige mutagenese: gecontroleerde veranderingen met backups

V13 OPTIONELE UITBREIDINGEN:
- AST-gebaseerde code-analyse en -generatie
- Meerdere code-generatie strategieën
- Automatische testing na wijzigingen
- Rollback mechanisme bij fouten
- Code review door meerdere agents
- Versiebeheer integratie (Git)
- Documentatie generatie
- Dependency analyse
- Performance profiling van gegenereerde code
- Gedistribueerde code-generatie
"""

import ast
import builtins
import hashlib
import importlib
import inspect
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple, Callable, Union

logger = logging.getLogger(__name__)

# ====================================================================
# OPTIONELE IMPORTS
# ====================================================================

# Voor AST manipulatie
try:
    import astor
    ASTOR_AVAILABLE = True
except ImportError:
    ASTOR_AVAILABLE = False

# Voor code formattering
try:
    import black
    BLACK_AVAILABLE = True
except ImportError:
    BLACK_AVAILABLE = False

try:
    import autopep8
    AUTOPEP8_AVAILABLE = True
except ImportError:
    AUTOPEP8_AVAILABLE = False

# Voor git integratie
try:
    import git
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False

# Voor LLM-gebaseerde code generatie (optioneel)
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Voor parallelle code generatie
try:
    from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
    PARALLEL_AVAILABLE = True
except ImportError:
    PARALLEL_AVAILABLE = False

# Voor code analyse
try:
    import pylint.lint
    PYLINT_AVAILABLE = True
except ImportError:
    PYLINT_AVAILABLE = False

try:
    import mypy.api
    MYPY_AVAILABLE = True
except ImportError:
    MYPY_AVAILABLE = False

# Voor performance profiling
try:
    import cProfile
    import pstats
    PROFILE_AVAILABLE = True
except ImportError:
    PROFILE_AVAILABLE = False

# Voor documentatie generatie
try:
    from pydoc import help
    PYDOC_AVAILABLE = True
except ImportError:
    PYDOC_AVAILABLE = False

# Voor dependency analyse
try:
    import pkg_resources
    PKG_RESOURCES_AVAILABLE = True
except ImportError:
    PKG_RESOURCES_AVAILABLE = False


class CodeGenStrategy(Enum):
    """Strategie voor code-generatie."""
    TEMPLATE = "template"           # Gebruik templates
    AST = "ast"                      # AST-gebaseerde generatie
    EVOLUTIONARY = "evolutionary"    # Evolutionaire algoritmes
    LLM = "llm"                      # Large Language Model
    HYBRID = "hybrid"                 # Combinatie van strategieën


class ChangeType(Enum):
    """Type van code wijziging."""
    NEW_FILE = "new_file"
    NEW_CLASS = "new_class"
    NEW_METHOD = "new_method"
    NEW_FUNCTION = "new_function"
    NEW_LAYER = "new_layer"           # Nieuwe laag (18, 19, ...)
    MODIFY = "modify"
    OPTIMIZE = "optimize"
    REFACTOR = "refactor"
    FIX = "fix"
    DOCUMENT = "document"


class ChangeStatus(Enum):
    """Status van een code wijziging."""
    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class CodeChange:
    """Een voorgestelde code wijziging."""
    id: str
    type: ChangeType
    target_file: str
    target_line: Optional[int] = None
    old_code: Optional[str] = None
    new_code: str
    description: str
    reason: str
    author: str  # Agent ID die wijziging voorstelt
    timestamp: float = field(default_factory=time.time)
    status: ChangeStatus = ChangeStatus.PROPOSED
    backups: List[str] = field(default_factory=list)
    test_results: Optional[Dict[str, Any]] = None
    performance_impact: Optional[float] = None
    complexity_score: float = 0.0
    approved_by: List[str] = field(default_factory=list)
    applied_at: Optional[float] = None
    rollback_reason: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converteer naar dictionary."""
        return {
            'id': self.id,
            'type': self.type.value,
            'target_file': self.target_file,
            'target_line': self.target_line,
            'description': self.description,
            'reason': self.reason,
            'author': self.author,
            'timestamp': self.timestamp,
            'status': self.status.value,
            'backups': self.backups,
            'complexity_score': self.complexity_score,
            'approved_by': self.approved_by
        }


@dataclass
class CodeTemplate:
    """Template voor code-generatie."""
    name: str
    description: str
    pattern: str
    parameters: List[str]
    example: str
    category: str  # 'layer', 'class', 'function', 'test'
    version: str = "1.0"


class CodeGenesis:
    """
    Laat het systeem zijn eigen Python-bestanden herschrijven.
    Dit is de ultieme vorm van ontogenese - het systeem creëert zijn eigen
    architectuur, voegt nieuwe lagen toe, en evolueert zijn eigen broncode.
    
    Core functionaliteit:
    - Code analyse en parsing
    - Wijzigingsvoorstellen genereren
    - Veilige toepassing met backups
    - Automatische tests na wijziging
    - Rollback bij fouten
    
    Optionele uitbreidingen:
    - AST-gebaseerde analyse
    - Meerdere generatiestrategieën
    - Git integratie
    - LLM-gebaseerde code generatie
    - Gedistribueerde code review
    - Performance profiling
    - Documentatie generatie
    """
    
    def __init__(self,
                 root_dir: str = ".",
                 strategy: CodeGenStrategy = CodeGenStrategy.HYBRID,
                 auto_approve: bool = False,
                 require_review: bool = True,
                 min_reviewers: int = 1,
                 create_backups: bool = True,
                 max_backups: int = 10,
                 run_tests: bool = True,
                 auto_rollback: bool = True,
                 use_git: bool = False,
                 use_llm: bool = False,
                 llm_model: str = "gpt-4",
                 parallel_generation: bool = False,
                 max_workers: int = 4,
                 analyze_dependencies: bool = True,
                 generate_docs: bool = False,
                 profile_performance: bool = False,
                 config_path: Optional[str] = None):
        """
        Initialiseer code genesis systeem.
        
        Args:
            root_dir: Hoofd directory van het project
            strategy: Code-generatie strategie
            auto_approve: Automatisch goedkeuren (gevaarlijk!)
            require_review: Vereiste code review
            min_reviewers: Minimum aantal reviewers
            create_backups: Maak backups voor wijzigingen
            max_backups: Maximum aantal backups per bestand
            run_tests: Voer tests uit na wijziging
            auto_rollback: Automatisch terugdraaien bij falen
            use_git: Gebruik Git voor versiebeheer
            use_llm: Gebruik LLM voor code generatie
            llm_model: LLM model naam
            parallel_generation: Parallelle code generatie
            max_workers: Maximum workers voor parallelle uitvoering
            analyze_dependencies: Analyseer dependencies
            generate_docs: Genereer documentatie
            profile_performance: Profileer performance
            config_path: Pad naar configuratie bestand
        """
        self.root_dir = os.path.abspath(root_dir)
        self.strategy = strategy
        self.auto_approve = auto_approve
        self.require_review = require_review
        self.min_reviewers = min_reviewers
        self.create_backups = create_backups
        self.max_backups = max_backups
        self.run_tests = run_tests
        self.auto_rollback = auto_rollback
        self.use_git = use_git and GIT_AVAILABLE
        self.use_llm = use_llm and OPENAI_AVAILABLE
        self.llm_model = llm_model
        self.parallel_generation = parallel_generation and PARALLEL_AVAILABLE
        self.max_workers = max_workers
        self.analyze_dependencies = analyze_dependencies
        self.generate_docs = generate_docs
        self.profile_performance = profile_performance and PROFILE_AVAILABLE
        
        # Bestanden om te monitoren
        self.watched_files: Set[str] = set()
        self._discover_python_files()
        
        # Wijzigingsgeschiedenis
        self.changes: List[CodeChange] = []
        self.applied_changes: List[CodeChange] = []
        self.failed_changes: List[CodeChange] = []
        
        # Backups directory
        self.backup_dir = os.path.join(self.root_dir, ".code_genesis_backups")
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Code templates
        self.templates: Dict[str, CodeTemplate] = {}
        self._load_default_templates()
        
        # AST cache
        self.ast_cache: Dict[str, Tuple[float, ast.AST]] = {}
        
        # Git repository (indien gebruikt)
        self.repo = None
        if self.use_git:
            try:
                self.repo = git.Repo(self.root_dir)
                logger.info(f"✅ Git repository geladen: {self.repo.git_dir}")
            except:
                logger.warning("⚠️ Geen Git repository gevonden")
        
        # LLM client (indien gebruikt)
        self.llm_client = None
        if self.use_llm:
            try:
                import openai
                self.llm_client = openai
                logger.info(f"✅ LLM client geïnitialiseerd ({llm_model})")
            except:
                logger.warning("⚠️ LLM client niet beschikbaar")
        
        # Statistieken
        self.stats = {
            'changes_proposed': 0,
            'changes_applied': 0,
            'changes_failed': 0,
            'changes_rolled_back': 0,
            'files_modified': 0,
            'lines_added': 0,
            'lines_removed': 0,
            'layers_created': 0,
            'templates_used': 0,
            'llm_calls': 0,
            'start_time': time.time()
        }
        
        # Laad configuratie
        if config_path:
            self._load_config(config_path)
        
        logger.info("="*80)
        logger.info("🧬 CODE GENESIS V13 GEÏNITIALISEERD")
        logger.info("="*80)
        logger.info(f"Root directory: {self.root_dir}")
        logger.info(f"Strategie: {strategy.value}")
        logger.info(f"Auto approve: {'✅' if auto_approve else '❌'}")
        logger.info(f"Code review: {'✅' if require_review else '❌'}")
        logger.info(f"Backups: {'✅' if create_backups else '❌'}")
        logger.info(f"Git integratie: {'✅' if self.use_git else '❌'}")
        logger.info(f"LLM generatie: {'✅' if self.use_llm else '❌'}")
        logger.info(f"Parallelle generatie: {'✅' if self.parallel_generation else '❌'}")
        logger.info(f"Python bestanden gevonden: {len(self.watched_files)}")
        logger.info("="*80)
    
    def _discover_python_files(self):
        """Ontdek alle Python bestanden in het project."""
        for root, dirs, files in os.walk(self.root_dir):
            # Skip virtuele omgevingen
            if 'venv' in dirs:
                dirs.remove('venv')
            if '__pycache__' in dirs:
                dirs.remove('__pycache__')
            if '.git' in dirs:
                dirs.remove('.git')
            
            for file in files:
                if file.endswith('.py'):
                    full_path = os.path.join(root, file)
                    self.watched_files.add(full_path)
    
    def _load_default_templates(self):
        """Laad standaard code templates."""
        
        # Template voor nieuwe laag (Layer 18, 19, ...)
        self.templates['new_layer'] = CodeTemplate(
            name="New Layer Template",
            description="Template voor het creëren van een nieuwe architectuurlaag",
            pattern='''
"""
LAYER {layer_number}: {layer_name} - {description}
================================================================================
Deze laag is gegenereerd door Code Genesis op {date}.
Reden: {reason}
"""

import numpy as np
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class Layer{layer_number}_{layer_name}:
    """
    {description}
    
    Attributes:
        lower_layer: De onderliggende laag
        config: Configuratie parameters
    """
    
    def __init__(self, lower_layer=None, config: Optional[Dict] = None):
        self.lower = lower_layer
        self.config = config or {{}}
        self.created_at = {creation_time}
        self.version = "1.0"
        
        logger.info(f"✨ Layer {layer_number} geïnitialiseerd: {layer_name}")
    
    async def process(self, input_data: Any) -> Any:
        """
        Verwerk input door deze laag.
        
        Args:
            input_data: Input van vorige laag
        
        Returns:
            Verwerkte output voor volgende laag
        """
        # TODO: Implementeer laag-specifieke verwerking
        result = input_data
        
        logger.debug(f"Layer {layer_number} verwerking voltooid")
        
        return result
    
    def get_info(self) -> Dict[str, Any]:
        """Haal informatie op over deze laag."""
        return {{
            'layer': {layer_number},
            'name': '{layer_name}',
            'version': self.version,
            'created_at': self.created_at,
            'config': self.config
        }}
''',
            parameters=['layer_number', 'layer_name', 'description', 'reason', 'date', 'creation_time'],
            example='layer_number=18, layer_name="QuantumConsciousness"',
            category='layer'
        )
        
        # Template voor nieuwe klasse
        self.templates['new_class'] = CodeTemplate(
            name="New Class Template",
            description="Template voor het creëren van een nieuwe klasse",
            pattern='''
class {class_name}:
    """
    {description}
    
    Generated by Code Genesis on {date}
    Reason: {reason}
    """
    
    def __init__(self, {init_params}):
        {init_body}
    
    def {method_name}(self, {method_params}) -> {return_type}:
        """
        {method_description}
        """
        {method_body}
''',
            parameters=['class_name', 'description', 'date', 'reason', 
                       'init_params', 'init_body', 'method_name', 
                       'method_params', 'return_type', 'method_description', 
                       'method_body'],
            example='class_name="QuantumObserver"',
            category='class'
        )
        
        # Template voor nieuwe functie
        self.templates['new_function'] = CodeTemplate(
            name="New Function Template",
            description="Template voor het creëren van een nieuwe functie",
            pattern='''
def {function_name}({parameters}) -> {return_type}:
    """
    {description}
    
    Args:
        {args_doc}
    
    Returns:
        {returns_doc}
    
    Generated by Code Genesis on {date}
    Reason: {reason}
    """
    {body}
''',
            parameters=['function_name', 'parameters', 'return_type', 'description',
                       'args_doc', 'returns_doc', 'date', 'reason', 'body'],
            example='function_name="calculate_quantum_overlap"',
            category='function'
        )
        
        # Template voor nieuwe test
        self.templates['new_test'] = CodeTemplate(
            name="New Test Template",
            description="Template voor het creëren van een nieuwe test",
            pattern='''
def test_{test_name}():
    """
    Test voor {test_description}
    
    Generated by Code Genesis on {date}
    """
    # Arrange
    {arrange}
    
    # Act
    {act}
    
    # Assert
    {assertions}
''',
            parameters=['test_name', 'test_description', 'date', 
                       'arrange', 'act', 'assertions'],
            example='test_name="quantum_backend_swap_test"',
            category='test'
        )
        
        # Template voor optimalisatie
        self.templates['optimization'] = CodeTemplate(
            name="Optimization Template",
            description="Template voor het optimaliseren van bestaande code",
            pattern='''
# OPTIMIZED VERSION - Generated by Code Genesis on {date}
# Original complexity: {old_complexity}
# New complexity: {new_complexity}
# Improvement: {improvement}%

{optimized_code}
''',
            parameters=['date', 'old_complexity', 'new_complexity', 
                       'improvement', 'optimized_code'],
            example='improvement="25"',
            category='optimization'
        )
    
    # ====================================================================
    # KERN FUNCTIONALITEIT - WIJZIGINGSVOORSTELLEN
    # ====================================================================
    
    async def propose_change(self,
                            type: ChangeType,
                            target_file: str,
                            description: str,
                            reason: str,
                            author: str,
                            new_code: Optional[str] = None,
                            target_line: Optional[int] = None,
                            old_code: Optional[str] = None,
                            template_name: Optional[str] = None,
                            template_params: Optional[Dict] = None) -> Optional[CodeChange]:
        """
        Stel een code wijziging voor.
        
        Args:
            type: Type wijziging
            target_file: Te wijzigen bestand
            description: Beschrijving van wijziging
            reason: Reden voor wijziging
            author: Agent die wijziging voorstelt
            new_code: Nieuwe code (optioneel, anders via template)
            target_line: Doelregel (voor modificaties)
            old_code: Oude code (voor verificatie)
            template_name: Naam van template om te gebruiken
            template_params: Parameters voor template
        
        Returns:
            CodeChange object of None bij fout
        """
        # Valideer bestand
        if not os.path.exists(target_file):
            logger.error(f"❌ Bestand niet gevonden: {target_file}")
            return None
        
        # Genereer code via template indien nodig
        if template_name and template_params:
            new_code = await self._apply_template(template_name, template_params)
            if not new_code:
                return None
        
        if not new_code:
            logger.error("❌ Geen nieuwe code opgegeven")
            return None
        
        # Maak change ID
        change_id = hashlib.md5(
            f"{target_file}{type.value}{time.time()}{author}".encode()
        ).hexdigest()[:12]
        
        # Bereken complexiteit
        complexity = self._calculate_complexity(new_code)
        
        change = CodeChange(
            id=change_id,
            type=type,
            target_file=target_file,
            target_line=target_line,
            old_code=old_code,
            new_code=new_code,
            description=description,
            reason=reason,
            author=author,
            complexity_score=complexity
        )
        
        self.changes.append(change)
        self.stats['changes_proposed'] += 1
        
        logger.info(f"\n📝 Nieuw wijzigingsvoorstel: {change_id[:8]}")
        logger.info(f"   Type: {type.value}")
        logger.info(f"   Bestand: {os.path.basename(target_file)}")
        logger.info(f"   Auteur: {author[:8]}")
        logger.info(f"   Complexiteit: {complexity:.3f}")
        
        # Automatisch goedkeuren indien ingesteld
        if self.auto_approve:
            await self.approve_change(change_id, author)
        
        return change
    
    async def _apply_template(self, template_name: str, params: Dict) -> Optional[str]:
        """Pas een template toe met gegeven parameters."""
        if template_name not in self.templates:
            logger.error(f"❌ Template niet gevonden: {template_name}")
            return None
        
        template = self.templates[template_name]
        
        # Voeg standaard parameters toe
        if 'date' not in params:
            params['date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if 'creation_time' not in params:
            params['creation_time'] = str(time.time())
        
        # Pas template toe
        try:
            code = template.pattern.format(**params)
            self.stats['templates_used'] += 1
            logger.debug(f"✅ Template toegepast: {template_name}")
            return code
        except KeyError as e:
            logger.error(f"❌ Ontbrekende template parameter: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Template fout: {e}")
            return None
    
    def _calculate_complexity(self, code: str) -> float:
        """
        Bereken complexiteit van code.
        Gebruikt meerdere metrics:
        - Aantal regels
        - Aantal functies/klassen
        - Cyclomatische complexiteit (simplified)
        """
        lines = code.split('\n')
        num_lines = len([l for l in lines if l.strip() and not l.strip().startswith('#')])
        
        # Tel functies en klassen
        num_functions = code.count('def ')
        num_classes = code.count('class ')
        
        # Tel geneste structuren (indicatie van complexiteit)
        num_indents = code.count('    ') + code.count('\t')
        
        # Geschatte cyclomatische complexiteit
        num_branches = code.count('if ') + code.count('elif ') + code.count('else:')
        num_loops = code.count('for ') + code.count('while ')
        num_conditions = num_branches + num_loops
        
        # Gewogen score
        complexity = (
            0.3 * min(1.0, num_lines / 100) +
            0.2 * min(1.0, num_functions / 10) +
            0.2 * min(1.0, num_classes / 5) +
            0.2 * min(1.0, num_indents / 50) +
            0.1 * min(1.0, num_conditions / 20)
        )
        
        return min(1.0, complexity)
    
    # ====================================================================
    # CODE REVIEW & GOEDKEURING
    # ====================================================================
    
    async def approve_change(self, change_id: str, reviewer: str) -> bool:
        """Keur een wijzigingsvoorstel goed."""
        change = self._get_change(change_id)
        if not change:
            return False
        
        if reviewer in change.approved_by:
            logger.warning(f"⚠️ {reviewer[:8]} heeft al goedgekeurd")
            return False
        
        change.approved_by.append(reviewer)
        
        # Check of voldoende reviewers
        if len(change.approved_by) >= self.min_reviewers or not self.require_review:
            change.status = ChangeStatus.APPROVED
            logger.info(f"✅ Wijziging {change_id[:8]} goedgekeurd")
            
            # Voer automatisch uit indien mogelijk
            asyncio.create_task(self.apply_change(change_id))
            
            return True
        else:
            logger.info(f"   Nog {self.min_reviewers - len(change.approved_by)} reviewers nodig")
            return False
    
    async def reject_change(self, change_id: str, reviewer: str, reason: str) -> bool:
        """Wijs een wijzigingsvoorstel af."""
        change = self._get_change(change_id)
        if not change:
            return False
        
        change.status = ChangeStatus.REJECTED
        change.rollback_reason = reason
        
        logger.warning(f"❌ Wijziging {change_id[:8]} afgewezen door {reviewer[:8]}")
        logger.warning(f"   Reden: {reason}")
        
        return True
    
    def _get_change(self, change_id: str) -> Optional[CodeChange]:
        """Haal een wijziging op via ID."""
        for change in self.changes:
            if change.id == change_id:
                return change
        return None
    
    # ====================================================================
    # CODE TOEPASSEN & BACKUPS
    # ====================================================================
    
    async def apply_change(self, change_id: str) -> bool:
        """
        Pas een goedgekeurde wijziging toe.
        
        Args:
            change_id: ID van de wijziging
        
        Returns:
            True als succesvol
        """
        change = self._get_change(change_id)
        if not change:
            return False
        
        if change.status != ChangeStatus.APPROVED and not self.auto_approve:
            logger.error(f"❌ Wijziging {change_id[:8]} niet goedgekeurd")
            return False
        
        logger.info(f"\n🔄 Wijziging toepassen: {change_id[:8]}")
        
        # Maak backup
        if self.create_backups:
            backup_path = await self._create_backup(change.target_file)
            if backup_path:
                change.backups.append(backup_path)
        
        # Pas wijziging toe
        try:
            if change.type == ChangeType.NEW_FILE:
                success = await self._apply_new_file(change)
            elif change.type == ChangeType.NEW_LAYER:
                success = await self._apply_new_layer(change)
            else:
                success = await self._apply_modification(change)
            
            if not success:
                raise Exception("Wijziging toepassen mislukt")
            
            # Update statistieken
            self.stats['changes_applied'] += 1
            change.status = ChangeStatus.APPLIED
            change.applied_at = time.time()
            self.applied_changes.append(change)
            
            # Voer tests uit
            if self.run_tests:
                test_success = await self._run_tests(change)
                change.test_results = {'success': test_success}
                
                if not test_success and self.auto_rollback:
                    logger.warning("⚠️ Tests gefaald, rollback...")
                    await self.rollback_change(change_id, "Tests failed")
                    return False
            
            # Profileer performance
            if self.profile_performance:
                perf = await self._profile_change(change)
                change.performance_impact = perf
            
            # Genereer documentatie
            if self.generate_docs:
                await self._generate_documentation(change)
            
            logger.info(f"✅ Wijziging {change_id[:8]} succesvol toegepast")
            
            # Git commit
            if self.use_git:
                await self._git_commit(change)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Fout bij toepassen: {e}")
            
            if self.auto_rollback:
                await self.rollback_change(change_id, str(e))
            
            change.status = ChangeStatus.FAILED
            self.failed_changes.append(change)
            self.stats['changes_failed'] += 1
            
            return False
    
    async def _create_backup(self, filepath: str) -> Optional[str]:
        """Maak een backup van een bestand."""
        if not os.path.exists(filepath):
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.basename(filepath)
        backup_path = os.path.join(
            self.backup_dir,
            f"{filename}.{timestamp}.bak"
        )
        
        shutil.copy2(filepath, backup_path)
        logger.debug(f"💾 Backup gemaakt: {os.path.basename(backup_path)}")
        
        # Beperk aantal backups
        await self._cleanup_old_backups(filepath)
        
        return backup_path
    
    async def _cleanup_old_backups(self, filepath: str):
        """Verwijder oude backups."""
        pattern = f"{os.path.basename(filepath)}.*.bak"
        backups = sorted([
            f for f in os.listdir(self.backup_dir)
            if f.startswith(os.path.basename(filepath)) and f.endswith('.bak')
        ])
        
        while len(backups) > self.max_backups:
            oldest = backups.pop(0)
            try:
                os.remove(os.path.join(self.backup_dir, oldest))
                logger.debug(f"🧹 Oude backup verwijderd: {oldest}")
            except:
                pass
    
    async def _apply_new_file(self, change: CodeChange) -> bool:
        """Pas een nieuw bestand toe."""
        directory = os.path.dirname(change.target_file)
        os.makedirs(directory, exist_ok=True)
        
        with open(change.target_file, 'w') as f:
            f.write(change.new_code)
        
        self.stats['files_modified'] += 1
        self.stats['lines_added'] += len(change.new_code.split('\n'))
        
        return True
    
    async def _apply_new_layer(self, change: CodeChange) -> bool:
        """Pas een nieuwe laag toe (speciale behandeling)."""
        # Haal laagnummer uit bestandsnaam of inhoud
        match = re.search(r'layer[_\s]*(\d+)', change.target_file.lower())
        if match:
            layer_num = int(match.group(1))
            self.stats['layers_created'] += 1
            logger.info(f"✨ Nieuwe laag {layer_num} gecreëerd!")
        
        return await self._apply_new_file(change)
    
    async def _apply_modification(self, change: CodeChange) -> bool:
        """Pas een modificatie toe op bestaand bestand."""
        if not os.path.exists(change.target_file):
            logger.error(f"❌ Bestand niet gevonden: {change.target_file}")
            return False
        
        with open(change.target_file, 'r') as f:
            old_content = f.read()
        
        if change.old_code and change.old_code not in old_content:
            logger.error("❌ Oude code niet gevonden in bestand")
            return False
        
        if change.target_line:
            # Regel-gebaseerde vervanging
            lines = old_content.split('\n')
            if 0 <= change.target_line < len(lines):
                lines[change.target_line] = change.new_code
                new_content = '\n'.join(lines)
            else:
                logger.error(f"❌ Ongeldige regel: {change.target_line}")
                return False
        else:
            # Content-gebaseerde vervanging
            if change.old_code:
                new_content = old_content.replace(change.old_code, change.new_code)
            else:
                new_content = old_content + '\n\n' + change.new_code
        
        # Bereken wijzigingen voor statistieken
        old_lines = len(old_content.split('\n'))
        new_lines = len(new_content.split('\n'))
        
        if new_lines > old_lines:
            self.stats['lines_added'] += new_lines - old_lines
        else:
            self.stats['lines_removed'] += old_lines - new_lines
        
        # Schrijf nieuwe content
        with open(change.target_file, 'w') as f:
            f.write(new_content)
        
        # Formatteer code indien beschikbaar
        await self._format_code(change.target_file)
        
        return True
    
    async def _format_code(self, filepath: str):
        """Formatteer code met black of autopep8."""
        if BLACK_AVAILABLE:
            try:
                with open(filepath, 'r') as f:
                    code = f.read()
                
                formatted = black.format_str(code, mode=black.Mode())
                
                with open(filepath, 'w') as f:
                    f.write(formatted)
                
                logger.debug(f"✨ Code geformatteerd met black: {os.path.basename(filepath)}")
            except Exception as e:
                logger.debug(f"⚠️ Black formatting mislukt: {e}")
        
        elif AUTOPEP8_AVAILABLE:
            try:
                with open(filepath, 'r') as f:
                    code = f.read()
                
                formatted = autopep8.fix_code(code)
                
                with open(filepath, 'w') as f:
                    f.write(formatted)
                
                logger.debug(f"✨ Code geformatteerd met autopep8: {os.path.basename(filepath)}")
            except Exception as e:
                logger.debug(f"⚠️ autopep8 formatting mislukt: {e}")
    
    # ====================================================================
    # ROLLBACK MECHANISME
    # ====================================================================
    
    async def rollback_change(self, change_id: str, reason: str) -> bool:
        """Draai een wijziging terug."""
        change = self._get_change(change_id)
        if not change:
            return False
        
        if not change.backups:
            logger.error(f"❌ Geen backups voor {change_id[:8]}")
            return False
        
        # Gebruik laatste backup
        latest_backup = change.backups[-1]
        
        try:
            shutil.copy2(latest_backup, change.target_file)
            
            change.status = ChangeStatus.ROLLED_BACK
            change.rollback_reason = reason
            self.stats['changes_rolled_back'] += 1
            
            logger.warning(f"↩️ Wijziging {change_id[:8]} teruggedraaid: {reason}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Rollback mislukt: {e}")
            return False
    
    # ====================================================================
    # OPTIONEEL: TESTEN
    # ====================================================================
    
    async def _run_tests(self, change: CodeChange) -> bool:
        """Voer tests uit om wijziging te valideren."""
        logger.info(f"🧪 Tests uitvoeren voor {change.id[:8]}...")
        
        # Vind tests die gerelateerd zijn aan gewijzigd bestand
        test_files = self._find_related_tests(change.target_file)
        
        if not test_files:
            logger.debug("   Geen gerelateerde tests gevonden")
            return True
        
        all_passed = True
        
        for test_file in test_files:
            try:
                # Voer test uit met pytest
                result = subprocess.run(
                    [sys.executable, '-m', 'pytest', test_file, '-v'],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    logger.debug(f"   ✅ Test geslaagd: {os.path.basename(test_file)}")
                else:
                    logger.error(f"   ❌ Test gefaald: {os.path.basename(test_file)}")
                    logger.error(f"      {result.stdout[:200]}...")
                    all_passed = False
                    
            except subprocess.TimeoutExpired:
                logger.error(f"   ⏱️ Test timeout: {os.path.basename(test_file)}")
                all_passed = False
            except Exception as e:
                logger.error(f"   ❌ Test fout: {e}")
                all_passed = False
        
        return all_passed
    
    def _find_related_tests(self, filepath: str) -> List[str]:
        """Vind tests die gerelateerd zijn aan een bestand."""
        test_files = []
        filename = os.path.basename(filepath)
        module_name = filename[:-3]  # Verwijder .py
        
        # Zoek naar test_*.py of *_test.py
        for root, dirs, files in os.walk(self.root_dir):
            if 'test' in root.lower() or 'tests' in root.lower():
                for file in files:
                    if file.startswith(f'test_{module_name}') or file.endswith(f'{module_name}_test.py'):
                        test_files.append(os.path.join(root, file))
        
        return test_files
    
    # ====================================================================
    # OPTIONEEL: PERFORMANCE PROFILING
    # ====================================================================
    
    async def _profile_change(self, change: CodeChange) -> float:
        """Profileer performance impact van wijziging."""
        if not self.profile_performance:
            return 0.0
        
        # Dit is een vereenvoudigde versie
        # In productie zou je de relevante functies profilen
        
        logger.debug(f"⏱️ Performance profiling voor {change.id[:8]}...")
        
        # Simuleer performance impact
        # In echt gebruik: meet voor en na wijziging
        impact = random.uniform(-0.2, 0.2)  # -20% tot +20%
        
        return impact
    
    # ====================================================================
    # OPTIONEEL: DOCUMENTATIE GENERATIE
    # ====================================================================
    
    async def _generate_documentation(self, change: CodeChange):
        """Genereer documentatie voor gewijzigde code."""
        if not self.generate_docs:
            return
        
        doc_dir = os.path.join(self.root_dir, 'docs')
        os.makedirs(doc_dir, exist_ok=True)
        
        # Genereer markdown documentatie
        doc_file = os.path.join(
            doc_dir,
            f"{os.path.basename(change.target_file)}.md"
        )
        
        with open(doc_file, 'w') as f:
            f.write(f"# {os.path.basename(change.target_file)}\n\n")
            f.write(f"**Generated by Code Genesis** on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"## Change Description\n\n")
            f.write(f"{change.description}\n\n")
            f.write(f"## Reason\n\n")
            f.write(f"{change.reason}\n\n")
            f.write(f"## Code\n\n")
            f.write("```python\n")
            f.write(change.new_code)
            f.write("\n```\n")
        
        logger.debug(f"📚 Documentatie gegenereerd: {doc_file}")
    
    # ====================================================================
    # OPTIONEEL: GIT INTEGRATIE
    # ====================================================================
    
    async def _git_commit(self, change: CodeChange):
        """Maak een Git commit voor de wijziging."""
        if not self.use_git or not self.repo:
            return
        
        try:
            # Stage het bestand
            self.repo.index.add([change.target_file])
            
            # Maak commit
            commit_msg = f"Code Genesis: {change.type.value} - {change.description}"
            self.repo.index.commit(commit_msg)
            
            logger.info(f"📦 Git commit gemaakt: {commit_msg[:50]}...")
            
        except Exception as e:
            logger.error(f"❌ Git commit mislukt: {e}")
    
    # ====================================================================
    # OPTIONEEL: LLM CODE GENERATIE
    # ====================================================================
    
    async def generate_with_llm(self, prompt: str, max_tokens: int = 500) -> Optional[str]:
        """
        Genereer code met een Large Language Model.
        
        Args:
            prompt: Prompt voor de LLM
            max_tokens: Maximum aantal tokens
        
        Returns:
            Gegenereerde code of None
        """
        if not self.use_llm or not self.llm_client:
            logger.warning("⚠️ LLM niet beschikbaar")
            return None
        
        try:
            self.stats['llm_calls'] += 1
            
            response = await self.llm_client.ChatCompletion.acreate(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": "You are an expert Python developer. Generate clean, efficient, well-documented code."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            code = response.choices[0].message.content
            
            # Extract code block if present
            code_match = re.search(r'```python\n(.*?)```', code, re.DOTALL)
            if code_match:
                code = code_match.group(1)
            
            logger.info(f"🤖 LLM code gegenereerd ({len(code)} chars)")
            
            return code
            
        except Exception as e:
            logger.error(f"❌ LLM generatie mislukt: {e}")
            return None
    
    # ====================================================================
    # OPTIONEEL: AST ANALYSE
    # ====================================================================
    
    def parse_ast(self, filepath: str) -> Optional[ast.AST]:
        """Parse een Python bestand naar AST."""
        if not os.path.exists(filepath):
            return None
        
        # Check cache
        mtime = os.path.getmtime(filepath)
        if filepath in self.ast_cache:
            cached_mtime, cached_ast = self.ast_cache[filepath]
            if cached_mtime == mtime:
                return cached_ast
        
        try:
            with open(filepath, 'r') as f:
                code = f.read()
            
            tree = ast.parse(code)
            self.ast_cache[filepath] = (mtime, tree)
            
            return tree
            
        except Exception as e:
            logger.error(f"❌ AST parse fout: {e}")
            return None
    
    def analyze_ast(self, filepath: str) -> Dict[str, Any]:
        """Analyseer AST van een bestand."""
        tree = self.parse_ast(filepath)
        if not tree:
            return {}
        
        analysis = {
            'filename': os.path.basename(filepath),
            'classes': [],
            'functions': [],
            'imports': [],
            'lines': 0,
            'complexity': 0.0
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                analysis['classes'].append({
                    'name': node.name,
                    'methods': len([n for n in node.body if isinstance(n, ast.FunctionDef)]),
                    'line': node.lineno
                })
            elif isinstance(node, ast.FunctionDef):
                analysis['functions'].append({
                    'name': node.name,
                    'args': len(node.args.args),
                    'line': node.lineno
                })
            elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    analysis['imports'].append(alias.name)
        
        # Tel regels
        with open(filepath, 'r') as f:
            analysis['lines'] = len(f.readlines())
        
        # Bereken complexiteit
        analysis['complexity'] = self._calculate_complexity_from_ast(tree)
        
        return analysis
    
    def _calculate_complexity_from_ast(self, tree: ast.AST) -> float:
        """Bereken complexiteit op basis van AST."""
        complexity = 0.0
        total_nodes = 0
        
        for node in ast.walk(tree):
            total_nodes += 1
            
            # Tel control flow nodes
            if isinstance(node, (ast.If, ast.For, ast.While, ast.Try)):
                complexity += 0.1
            elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                complexity += 0.2
            elif isinstance(node, (ast.Return, ast.Yield)):
                complexity += 0.05
        
        # Normaliseer
        if total_nodes > 0:
            complexity = min(1.0, complexity / (total_nodes * 0.01))
        
        return complexity
    
    # ====================================================================
    # OPTIONEEL: STATISCHE ANALYSE
    # ====================================================================
    
    def run_pylint(self, filepath: str) -> Dict[str, Any]:
        """Voer pylint uit op een bestand."""
        if not PYLINT_AVAILABLE:
            return {'error': 'pylint niet beschikbaar'}
        
        try:
            from pylint.lint import Run
            from pylint.reporters import CollectingReporter
            
            reporter = CollectingReporter()
            Run([filepath], reporter=reporter, exit=False)
            
            return {
                'score': reporter.score,
                'errors': [m.msg for m in reporter.messages if m.category == 'error'],
                'warnings': [m.msg for m in reporter.messages if m.category == 'warning'],
                'convention': [m.msg for m in reporter.messages if m.category == 'convention']
            }
            
        except Exception as e:
            logger.error(f"❌ Pylint fout: {e}")
            return {'error': str(e)}
    
    def run_mypy(self, filepath: str) -> Dict[str, Any]:
        """Voer mypy type checking uit."""
        if not MYPY_AVAILABLE:
            return {'error': 'mypy niet beschikbaar'}
        
        try:
            result = mypy.api.run([filepath])
            
            return {
                'success': result[2] == 0,
                'output': result[0],
                'errors': result[1]
            }
            
        except Exception as e:
            logger.error(f"❌ Mypy fout: {e}")
            return {'error': str(e)}
    
    # ====================================================================
    # OPTIONEEL: DEPENDENCY ANALYSE
    # ====================================================================
    
    def analyze_dependencies(self, filepath: str) -> List[str]:
        """Analyseer imports en dependencies van een bestand."""
        if not self.analyze_dependencies:
            return []
        
        tree = self.parse_ast(filepath)
        if not tree:
            return []
        
        dependencies = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    dependencies.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    dependencies.append(node.module)
        
        # Check of dependencies bestaan
        available = []
        for dep in dependencies:
            try:
                importlib.import_module(dep)
                available.append(dep)
            except ImportError:
                logger.debug(f"⚠️ Dependency niet gevonden: {dep}")
        
        return available
    
    # ====================================================================
    # NIEUWE LAAG SUGGESTIE
    # ====================================================================
    
    async def suggest_new_layer(self, gap: Any, reason: str, author: str) -> Optional[CodeChange]:
        """
        Stel een nieuwe architectuurlaag voor op basis van een ontologische gap.
        
        Args:
            gap: OntologicalGap object
            reason: Reden voor nieuwe laag
            author: Agent die voorstelt
        
        Returns:
            CodeChange voor nieuwe laag
        """
        # Bepaal volgend laagnummer
        layer_number = self._get_next_layer_number()
        
        # Bepaal laagnaam op basis van gap type
        if hasattr(gap, 'gap_type'):
            layer_name = gap.gap_type.capitalize()
        else:
            layer_name = f"Layer{layer_number}"
        
        # Maak bestandsnaam
        filename = f"layer_{layer_number}_{layer_name.lower()}.py"
        filepath = os.path.join(self.root_dir, filename)
        
        # Bereid template parameters voor
        params = {
            'layer_number': layer_number,
            'layer_name': layer_name,
            'description': getattr(gap, 'description', f'New layer {layer_number}'),
            'reason': reason,
            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'creation_time': time.time()
        }
        
        # Stel wijziging voor
        change = await self.propose_change(
            type=ChangeType.NEW_LAYER,
            target_file=filepath,
            description=f"Create new layer {layer_number}: {layer_name}",
            reason=reason,
            author=author,
            template_name='new_layer',
            template_params=params
        )
        
        return change
    
    def _get_next_layer_number(self) -> int:
        """Bepaal het volgende vrije laagnummer."""
        max_layer = 17  # Start na bestaande lagen
        
        for filepath in self.watched_files:
            match = re.search(r'layer[_\s]*(\d+)', os.path.basename(filepath).lower())
            if match:
                num = int(match.group(1))
                max_layer = max(max_layer, num)
        
        return max_layer + 1
    
    # ====================================================================
    # OPTIMALISATIE SUGGESTIE
    # ====================================================================
    
    async def suggest_optimization(self,
                                  filepath: str,
                                  function_name: str,
                                  old_code: str,
                                  optimized_code: str,
                                  improvement: float,
                                  author: str) -> Optional[CodeChange]:
        """Stel een optimalisatie voor."""
        
        params = {
            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'old_complexity': self._calculate_complexity(old_code),
            'new_complexity': self._calculate_complexity(optimized_code),
            'improvement': improvement * 100,
            'optimized_code': optimized_code
        }
        
        change = await self.propose_change(
            type=ChangeType.OPTIMIZE,
            target_file=filepath,
            description=f"Optimize {function_name}",
            reason=f"Performance improvement of {improvement*100:.1f}%",
            author=author,
            new_code=optimized_code,
            old_code=old_code,
            template_name='optimization',
            template_params=params
        )
        
        return change
    
    # ====================================================================
    # PARALLELLE GENERATIE
    # ====================================================================
    
    async def generate_multiple(self, suggestions: List[Dict]) -> List[Optional[CodeChange]]:
        """
        Genereer meerdere wijzigingen parallel.
        
        Args:
            suggestions: Lijst van suggestie dictionaries
        
        Returns:
            Lijst van gegenereerde wijzigingen
        """
        if not self.parallel_generation:
            # Serieel
            results = []
            for sugg in suggestions:
                result = await self.propose_change(**sugg)
                results.append(result)
            return results
        
        # Parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            for sugg in suggestions:
                future = executor.submit(
                    self._propose_change_sync,
                    **sugg
                )
                futures.append(future)
            
            results = []
            for future in futures:
                try:
                    result = future.result(timeout=60)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Parallel generatie fout: {e}")
                    results.append(None)
        
        return results
    
    def _propose_change_sync(self, **kwargs) -> Optional[CodeChange]:
        """Synchrone wrapper voor propose_change."""
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.propose_change(**kwargs))
        finally:
            loop.close()
    
    # ====================================================================
    # STATISTIEKEN & RAPPORTAGE
    # ====================================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Haal uitgebreide statistieken op."""
        return {
            **self.stats,
            'pending_changes': len([c for c in self.changes if c.status == ChangeStatus.PROPOSED]),
            'approved_changes': len([c for c in self.changes if c.status == ChangeStatus.APPROVED]),
            'applied_changes': len(self.applied_changes),
            'failed_changes': len(self.failed_changes),
            'watched_files': len(self.watched_files),
            'templates_available': len(self.templates),
            'backup_count': len(os.listdir(self.backup_dir)) if os.path.exists(self.backup_dir) else 0,
            'uptime': time.time() - self.stats['start_time']
        }
    
    def get_change_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Haal geschiedenis van wijzigingen op."""
        history = []
        
        for change in self.changes[-limit:]:
            history.append(change.to_dict())
        
        return history
    
    def get_file_history(self, filepath: str) -> List[Dict[str, Any]]:
        """Haal wijzigingsgeschiedenis voor een specifiek bestand op."""
        history = []
        
        for change in self.changes:
            if change.target_file == filepath:
                history.append(change.to_dict())
        
        return history
    
    def generate_report(self, filename: str = "code_genesis_report.json"):
        """Genereer een uitgebreid rapport."""
        report = {
            'generated_at': time.time(),
            'datetime': datetime.now().isoformat(),
            'stats': self.get_stats(),
            'recent_changes': self.get_change_history(20),
            'templates': [
                {
                    'name': t.name,
                    'description': t.description,
                    'category': t.category,
                    'parameters': t.parameters
                }
                for t in self.templates.values()
            ],
            'files_analyzed': [
                {
                    'file': os.path.basename(f),
                    'analysis': self.analyze_ast(f) if os.path.exists(f) else None
                }
                for f in list(self.watched_files)[:20]  # Max 20
            ]
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"📄 Rapport gegenereerd: {filename}")
        return report
    
    # ====================================================================
    # CONFIGURATIE
    # ====================================================================
    
    def _load_config(self, config_path: str):
        """Laad configuratie uit JSON/YAML bestand."""
        try:
            if config_path.endswith('.json'):
                with open(config_path, 'r') as f:
                    config = json.load(f)
            elif config_path.endswith(('.yaml', '.yml')):
                import yaml
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
            else:
                return
            
            # Update parameters
            cg_config = config.get('code_genesis', {})
            
            if 'strategy' in cg_config:
                self.strategy = CodeGenStrategy(cg_config['strategy'])
            if 'auto_approve' in cg_config:
                self.auto_approve = cg_config['auto_approve']
            if 'require_review' in cg_config:
                self.require_review = cg_config['require_review']
            if 'min_reviewers' in cg_config:
                self.min_reviewers = cg_config['min_reviewers']
            if 'run_tests' in cg_config:
                self.run_tests = cg_config['run_tests']
            if 'auto_rollback' in cg_config:
                self.auto_rollback = cg_config['auto_rollback']
            if 'use_git' in cg_config:
                self.use_git = cg_config['use_git']
            if 'use_llm' in cg_config:
                self.use_llm = cg_config['use_llm']
            if 'llm_model' in cg_config:
                self.llm_model = cg_config['llm_model']
            
            logger.info(f"📋 Configuratie geladen uit: {config_path}")
            
        except Exception as e:
            logger.error(f"❌ Configuratie laden mislukt: {e}")
    
    # ====================================================================
    # RESOURCE MANAGEMENT
    # ====================================================================
    
    async def cleanup(self):
        """Ruim resources op."""
        logger.info("🧹 CodeGenesis cleanup...")
        
        # Genereer eindrapport
        self.generate_report("code_genesis_final.json")
        
        # Optioneel: maak laatste commit
        if self.use_git and self.repo:
            try:
                self.repo.index.commit("Code Genesis: final state before shutdown")
                logger.info("📦 Laatste Git commit gemaakt")
            except:
                pass
        
        logger.info("✅ Cleanup voltooid")
    
    def reset(self):
        """Reset alle data (voor testing)."""
        self.changes.clear()
        self.applied_changes.clear()
        self.failed_changes.clear()
        self.ast_cache.clear()
        self.stats = {
            'changes_proposed': 0,
            'changes_applied': 0,
            'changes_failed': 0,
            'changes_rolled_back': 0,
            'files_modified': 0,
            'lines_added': 0,
            'lines_removed': 0,
            'layers_created': 0,
            'templates_used': 0,
            'llm_calls': 0,
            'start_time': time.time()
        }
        logger.info("🔄 CodeGenesis gereset")


# ====================================================================
# CONVENIENCE FUNCTIES
# ====================================================================

def create_code_genesis(root_dir: str = ".", config_path: Optional[str] = None, **kwargs) -> CodeGenesis:
    """
    Maak een CodeGenesis instantie met gegeven configuratie.
    
    Args:
        root_dir: Hoofd directory
        config_path: Optioneel pad naar configuratiebestand
        **kwargs: Overschrijf specifieke parameters
    
    Returns:
        Geïnitialiseerde CodeGenesis
    """
    return CodeGenesis(
        root_dir=root_dir,
        config_path=config_path,
        **kwargs
    )


# ====================================================================
# DEMONSTRATIE
# ====================================================================

async def demo():
    """Demonstreer Code Genesis functionaliteit."""
    print("\n" + "="*80)
    print("🧬 CODE GENESIS V13 DEMONSTRATIE")
    print("="*80)
    
    # Maak tijdelijke test directory
    test_dir = tempfile.mkdtemp(prefix="code_genesis_demo_")
    print(f"\n📁 Test directory: {test_dir}")
    
    # Maak een test Python bestand
    test_file = os.path.join(test_dir, "test_module.py")
    with open(test_file, 'w') as f:
        f.write('''
def hello():
    """Say hello."""
    print("Hello from test module!")

class TestClass:
    """A test class."""
    
    def __init__(self, name):
        self.name = name
    
    def greet(self):
        """Greet the user."""
        return f"Hello, {self.name}!"
''')
    
    # Initialiseer Code Genesis met alle opties
    cg = CodeGenesis(
        root_dir=test_dir,
        strategy=CodeGenStrategy.HYBRID,
        auto_approve=False,
        require_review=True,
        min_reviewers=1,
        create_backups=True,
        max_backups=3,
        run_tests=False,  # Skip tests voor demo
        auto_rollback=True,
        use_git=False,
        use_llm=False,
        parallel_generation=False,
        analyze_dependencies=True,
        generate_docs=True,
        profile_performance=False
    )
    
    print("\n📋 Test 1: Nieuwe laag voorstellen")
    class MockGap:
        def __init__(self):
            self.gap_type = "quantum_consciousness"
            self.description = "Need for quantum consciousness layer"
    
    gap = MockGap()
    change1 = await cg.suggest_new_layer(
        gap=gap,
        reason="Quantum consciousness requires new abstraction layer",
        author="agent_001"
    )
    
    if change1:
        print(f"   ✅ Laag voorstel: {change1.id[:8]}")
    
    print("\n📋 Test 2: Nieuwe klasse voorstellen")
    change2 = await cg.propose_change(
        type=ChangeType.NEW_FILE,
        target_file=os.path.join(test_dir, "quantum_observer.py"),
        description="Quantum Observer class for measuring superposition",
        reason="Need to observe quantum states",
        author="agent_002",
        template_name='new_class',
        template_params={
            'class_name': 'QuantumObserver',
            'description': 'Observes and measures quantum states',
            'init_params': 'qubit_count: int = 1',
            'init_body': 'self.qubit_count = qubit_count\n        self.measurements = []',
            'method_name': 'measure',
            'method_params': 'state: np.ndarray',
            'return_type': 'float',
            'method_description': 'Measure a quantum state',
            'method_body': 'result = np.random.random()\n        self.measurements.append(result)\n        return result'
        }
    )
    
    if change2:
        print(f"   ✅ Klasse voorstel: {change2.id[:8]}")
    
    print("\n📋 Test 3: Goedkeuren")
    if change1:
        await cg.approve_change(change1.id, "agent_003")
    if change2:
        await cg.approve_change(change2.id, "agent_003")
    
    print("\n📋 Test 4: AST Analyse")
    analysis = cg.analyze_ast(test_file)
    print(f"   Bestand: {analysis.get('filename', '?')}")
    print(f"   Klassen: {len(analysis.get('classes', []))}")
    print(f"   Functies: {len(analysis.get('functions', []))}")
    print(f"   Complexiteit: {analysis.get('complexity', 0):.3f}")
    
    print("\n📋 Test 5: Code formattering")
    await cg._format_code(test_file)
    print("   ✅ Code geformatteerd")
    
    print("\n📋 Test 6: Wijzigingsgeschiedenis")
    history = cg.get_change_history()
    print(f"   {len(history)} wijzigingen in geschiedenis")
    
    print("\n📋 Test 7: Statistieken")
    stats = cg.get_stats()
    print(f"   Voorgesteld: {stats['changes_proposed']}")
    print(f"   Toegepast: {stats['changes_applied']}")
    print(f"   Lagen gecreëerd: {stats['layers_created']}")
    print(f"   Templates gebruikt: {stats['templates_used']}")
    
    print("\n📋 Test 8: Rapport genereren")
    cg.generate_report(os.path.join(test_dir, "code_genesis_report.json"))
    
    print("\n📋 Test 9: Backup test")
    backup = await cg._create_backup(test_file)
    if backup:
        print(f"   ✅ Backup gemaakt: {os.path.basename(backup)}")
    
    print("\n📋 Test 10: Optimalisatie voorstellen")
    old_code = "def slow_function(): total = 0; for i in range(1000): total += i; return total"
    optimized_code = "def fast_function(): return sum(range(1000))"
    
    change3 = await cg.suggest_optimization(
        filepath=test_file,
        function_name="slow_function",
        old_code=old_code,
        optimized_code=optimized_code,
        improvement=0.75,
        author="agent_004"
    )
    
    if change3:
        print(f"   ✅ Optimalisatie voorstel: {change3.id[:8]}")
        print(f"   Complexiteit oud: {cg._calculate_complexity(old_code):.3f}")
        print(f"   Complexiteit nieuw: {cg._calculate_complexity(optimized_code):.3f}")
    
    # Cleanup
    await cg.cleanup()
    
    # Verwijder test directory
    shutil.rmtree(test_dir)
    print(f"\n🧹 Test directory verwijderd: {test_dir}")
    
    print("\n" + "="*80)
    print("✅ Demonstratie voltooid!")
    print("="*80)


if __name__ == "__main__":
    # Configureer logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)-8s | %(message)s'
    )
    
    asyncio.run(demo())