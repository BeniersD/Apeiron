"""
CROSS-DOMAIN SYNTHESIS DEMO
Demonstrates the killer feature in action
"""

import sys
sys.path.insert(0, '/mnt/user-data/outputs')

from cross_domain_synthesis import CrossDomainSynthesizer, DomainProfile
from layers_11_to_17 import Layer12_Reconciliation, Layer13_Ontogenesis, Layer11_MetaContextualization
from seventeen_layers_framework import SeventeenLayerFramework

def create_mock_memory():
    """Create mock memory for demonstration."""
    class MockMemory:
        def query(self, query_texts, n_results):
            # Return mock results
            return {
                'documents': [['mock document'] * n_results],
                'metadatas': [[{'title': 'Mock Paper', 'step': i} for i in range(n_results)]]
            }
    
    return MockMemory()


def demo_synthesis():
    """
    Demonstrate Cross-Domain Synthesis with realistic examples.
    """
    
    print("\n" + "="*80)
    print(" "*25 + "CROSS-DOMAIN SYNTHESIS")
    print(" "*30 + "DEMO")
    print("="*80 + "\n")
    
    # Initialize framework
    print("Phase 1: Initializing 17-Layer Framework...")
    framework = SeventeenLayerFramework()
    
    # Initialize higher layers
    layer11 = Layer11_MetaContextualization(framework.layer10)
    layer12 = Layer12_Reconciliation(layer11)
    layer13 = Layer13_Ontogenesis(layer12)
    
    # Create mock memory
    memory = create_mock_memory()
    
    # Initialize synthesizer
    print("✓ Initializing Cross-Domain Synthesis Engine...\n")
    synthesizer = CrossDomainSynthesizer(layer12, layer13, memory)
    
    # ========================================================================
    # EXAMPLE 1: Quantum Computing × Protein Folding
    # ========================================================================
    
    print("="*80)
    print("EXAMPLE 1: Quantum Computing × Protein Folding")
    print("="*80)
    
    # Mock papers for Quantum Computing
    quantum_papers = [
        {
            'title': 'Quantum Annealing for Optimization Problems',
            'summary': 'We explore quantum annealing techniques for solving complex optimization problems using quantum superposition and tunneling effects.',
            'id': 'qc_1'
        },
        {
            'title': 'Quantum Error Correction in NISQ Devices',
            'summary': 'Novel error correction codes for near-term quantum computers using topological methods and redundancy.',
            'id': 'qc_2'
        },
        {
            'title': 'Variational Quantum Eigensolver Applications',
            'summary': 'Applications of VQE algorithm in chemistry and materials science using hybrid quantum-classical optimization.',
            'id': 'qc_3'
        }
    ]
    
    # Mock papers for Protein Folding
    protein_papers = [
        {
            'title': 'Protein Folding Energy Landscapes',
            'summary': 'Exploration of energy landscapes in protein folding using computational methods and optimization techniques to predict stable conformations.',
            'id': 'pf_1'
        },
        {
            'title': 'Machine Learning for Structure Prediction',
            'summary': 'Deep learning approaches for predicting protein structures from sequence using neural networks and optimization.',
            'id': 'pf_2'
        },
        {
            'title': 'Conformational Search in Protein Design',
            'summary': 'Methods for efficiently searching conformational space in de novo protein design using heuristic optimization.',
            'id': 'pf_3'
        }
    ]
    
    # Build domain profiles
    print("\n📊 Building domain profiles...")
    profile_qc = synthesizer.build_domain_profile("Quantum Computing", quantum_papers)
    profile_pf = synthesizer.build_domain_profile("Protein Folding", protein_papers)
    
    # Find bridges
    print("\n🌉 Discovering conceptual bridges...")
    bridges_1 = synthesizer.find_bridges("Quantum Computing", "Protein Folding")
    
    # Generate hypotheses
    print("\n💡 Generating novel hypotheses...")
    hypotheses_1 = synthesizer.generate_hypotheses(bridges_1, max_hypotheses=3)
    
    # ========================================================================
    # EXAMPLE 2: Neural Networks × Social Networks
    # ========================================================================
    
    print("\n\n" + "="*80)
    print("EXAMPLE 2: Neural Networks × Social Networks")
    print("="*80)
    
    # Mock papers for Neural Networks
    neural_papers = [
        {
            'title': 'Graph Neural Networks for Node Classification',
            'summary': 'Novel graph neural network architectures for node classification using message passing and attention mechanisms.',
            'id': 'nn_1'
        },
        {
            'title': 'Attention Mechanisms in Deep Learning',
            'summary': 'Attention mechanisms enable networks to focus on relevant features using weighted aggregation of information.',
            'id': 'nn_2'
        },
        {
            'title': 'Network Topology and Learning Dynamics',
            'summary': 'How network topology affects learning dynamics and information propagation in neural architectures.',
            'id': 'nn_3'
        }
    ]
    
    # Mock papers for Social Networks
    social_papers = [
        {
            'title': 'Information Propagation in Social Networks',
            'summary': 'Studying how information spreads through social networks using graph analysis and propagation models.',
            'id': 'sn_1'
        },
        {
            'title': 'Influence Maximization in Networks',
            'summary': 'Algorithms for identifying influential nodes in social networks to maximize information spread.',
            'id': 'sn_2'
        },
        {
            'title': 'Community Detection Using Graph Methods',
            'summary': 'Graph-based methods for detecting communities in social networks using clustering and modularity optimization.',
            'id': 'sn_3'
        }
    ]
    
    # Build profiles
    print("\n📊 Building domain profiles...")
    profile_nn = synthesizer.build_domain_profile("Neural Networks", neural_papers)
    profile_sn = synthesizer.build_domain_profile("Social Networks", social_papers)
    
    # Find bridges
    print("\n🌉 Discovering conceptual bridges...")
    bridges_2 = synthesizer.find_bridges("Neural Networks", "Social Networks")
    
    # Generate hypotheses
    print("\n💡 Generating novel hypotheses...")
    hypotheses_2 = synthesizer.generate_hypotheses(bridges_2, max_hypotheses=3)
    
    # ========================================================================
    # EXAMPLE 3: Climate Science × Blockchain
    # ========================================================================
    
    print("\n\n" + "="*80)
    print("EXAMPLE 3: Climate Science × Blockchain")
    print("="*80)
    
    # Mock papers for Climate Science
    climate_papers = [
        {
            'title': 'Distributed Climate Monitoring Networks',
            'summary': 'Networks of distributed sensors for real-time climate monitoring using decentralized data collection.',
            'id': 'cl_1'
        },
        {
            'title': 'Carbon Credit Verification Systems',
            'summary': 'Methods for verifying and tracking carbon credits using transparent and auditable systems.',
            'id': 'cl_2'
        },
        {
            'title': 'Climate Data Transparency and Trust',
            'summary': 'Ensuring transparency and trust in climate data through immutable record-keeping.',
            'id': 'cl_3'
        }
    ]
    
    # Mock papers for Blockchain
    blockchain_papers = [
        {
            'title': 'Decentralized Consensus Mechanisms',
            'summary': 'Novel consensus mechanisms for decentralized networks ensuring security and immutability.',
            'id': 'bc_1'
        },
        {
            'title': 'Smart Contracts for Automated Verification',
            'summary': 'Smart contracts enable automated verification and execution of agreements using blockchain technology.',
            'id': 'bc_2'
        },
        {
            'title': 'Blockchain for Supply Chain Transparency',
            'summary': 'Using blockchain for transparent and auditable supply chain tracking and verification.',
            'id': 'bc_3'
        }
    ]
    
    # Build profiles
    print("\n📊 Building domain profiles...")
    profile_cl = synthesizer.build_domain_profile("Climate Science", climate_papers)
    profile_bc = synthesizer.build_domain_profile("Blockchain", blockchain_papers)
    
    # Find bridges
    print("\n🌉 Discovering conceptual bridges...")
    bridges_3 = synthesizer.find_bridges("Climate Science", "Blockchain")
    
    # Generate hypotheses
    print("\n💡 Generating novel hypotheses...")
    hypotheses_3 = synthesizer.generate_hypotheses(bridges_3, max_hypotheses=3)
    
    # ========================================================================
    # SUMMARY & ANALYSIS
    # ========================================================================
    
    print("\n\n" + "="*80)
    print("SYNTHESIS SUMMARY")
    print("="*80)
    
    synthesizer.print_top_discoveries(n=3)
    
    # Export report
    print("\n\n📄 Exporting comprehensive synthesis report...")
    report = synthesizer.export_synthesis_report("demo_synthesis_report.json")
    
    # Print statistics
    print("\n📊 STATISTICS:")
    print(f"  Total Domains Analyzed: {report['statistics']['total_domains']}")
    print(f"  Total Bridges Found: {report['statistics']['total_bridges']}")
    print(f"  Total Hypotheses Generated: {report['statistics']['total_hypotheses']}")
    print(f"  Average Bridge Strength: {report['statistics']['avg_bridge_strength']:.3f}")
    
    # Print rankings
    print("\n🏆 HYPOTHESIS RANKINGS:")
    print("\n  By Impact Potential:")
    by_impact = synthesizer.rank_hypotheses('impact')[:3]
    for i, h in enumerate(by_impact, 1):
        print(f"    {i}. {h.description[:80]}... (impact: {h.impact_potential:.2f})")
    
    print("\n  By Feasibility:")
    by_feasibility = synthesizer.rank_hypotheses('feasibility')[:3]
    for i, h in enumerate(by_feasibility, 1):
        print(f"    {i}. {h.description[:80]}... (feasibility: {h.feasibility_score:.2f})")
    
    print("\n  By Combined Score:")
    by_combined = synthesizer.rank_hypotheses('combined')[:3]
    for i, h in enumerate(by_combined, 1):
        combined_score = (h.impact_potential * h.feasibility_score * h.novelty_score) ** (1/3)
        print(f"    {i}. {h.description[:80]}... (combined: {combined_score:.2f})")
    
    # ========================================================================
    # PRACTICAL APPLICATIONS
    # ========================================================================
    
    print("\n\n" + "="*80)
    print("PRACTICAL APPLICATIONS")
    print("="*80)
    
    print("""
This Cross-Domain Synthesis Engine can be used for:

1. 🔬 RESEARCH ACCELERATION
   - Find unexpected connections between fields
   - Generate novel research directions
   - Identify transferable methodologies

2. 💡 INNOVATION DISCOVERY
   - Spot cross-industry innovation opportunities
   - Identify analogous solutions from other domains
   - Generate breakthrough product ideas

3. 🎓 GRANT WRITING
   - Find interdisciplinary angles
   - Identify collaboration opportunities
   - Strengthen novelty arguments

4. 💼 COMPETITIVE INTELLIGENCE
   - Spot emerging cross-domain trends
   - Identify potential disruptions
   - Find non-obvious competitors

5. 🏢 STRATEGIC PLANNING
   - Identify domain convergence opportunities
   - Spot technology transfer possibilities
   - Predict future intersections
    """)
    
    print("\n" + "="*80)
    print("✨ DEMO COMPLETE - Cross-Domain Synthesis Engine Operational!")
    print("="*80 + "\n")


if __name__ == "__main__":
    demo_synthesis()
