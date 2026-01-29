# models/cost_benefit_optimizer.py
"""
Cost-Benefit Optimization for Infrastructure Projects
Mixed Integer Programming model for budget-constrained optimization
"""

from typing import List, Dict, Any
import numpy as np


class CostBenefitOptimizer:
    """
    Mixed Integer Programming model for budget-constrained optimization
    Maximize total benefit under budget constraints
    """
    
    def __init__(self):
        self.selected_projects = []
        
    def optimize(self, projects: List[Dict], budget_constraint: float) -> Dict[str, Any]:
        """
        Optimize project portfolio selection
        
        projects: List of candidate projects with:
            - cost
            - benefit_score
            - urgency
            - dependencies
        
        Returns: Optimal project portfolio
        """
        try:
            import pulp
            return self._optimize_with_pulp(projects, budget_constraint)
        except ImportError:
            return self._optimize_greedy(projects, budget_constraint)
    
    def _optimize_with_pulp(self, projects: List[Dict], budget_constraint: float) -> Dict[str, Any]:
        """Optimize using PuLP linear programming"""
        import pulp
        
        # Create optimization problem
        prob = pulp.LpProblem("Infrastructure_Optimization", pulp.LpMaximize)
        
        # Decision variables (binary: build or not)
        x = {i: pulp.LpVariable(f"project_{i}", cat='Binary') for i in range(len(projects))}
        
        # Objective: Maximize total benefit
        prob += pulp.lpSum([projects[i]['benefit_score'] * x[i] for i in range(len(projects))])
        
        # Constraints
        # 1. Budget constraint
        prob += pulp.lpSum([projects[i]['cost'] * x[i] for i in range(len(projects))]) <= budget_constraint
        
        # 2. Dependency constraints (if project B depends on A)
        for i, project in enumerate(projects):
            for dep in project.get('dependencies', []):
                if dep < len(projects):
                    prob += x[i] <= x[dep]
        
        # Solve
        prob.solve(pulp.PULP_CBC_CMD(msg=False))
        
        # Extract solution
        selected_projects = [i for i in range(len(projects)) if pulp.value(x[i]) == 1]
        
        total_cost = sum(projects[i]['cost'] for i in selected_projects)
        total_benefit = sum(projects[i]['benefit_score'] for i in selected_projects)
        
        return {
            'selected_projects': [projects[i] for i in selected_projects],
            'selected_indices': selected_projects,
            'total_cost': total_cost,
            'total_benefit': total_benefit,
            'roi': total_benefit / total_cost if total_cost > 0 else 0,
            'budget_utilization': total_cost / budget_constraint * 100
        }
    
    def _optimize_greedy(self, projects: List[Dict], budget_constraint: float) -> Dict[str, Any]:
        """Greedy optimization when PuLP is not available"""
        # Calculate benefit/cost ratio for each project
        for i, project in enumerate(projects):
            project['index'] = i
            project['ratio'] = project['benefit_score'] / max(project['cost'], 0.001)
        
        # Sort by ratio (descending)
        sorted_projects = sorted(projects, key=lambda x: x['ratio'], reverse=True)
        
        selected = []
        total_cost = 0
        total_benefit = 0
        
        for project in sorted_projects:
            if total_cost + project['cost'] <= budget_constraint:
                selected.append(project)
                total_cost += project['cost']
                total_benefit += project['benefit_score']
        
        return {
            'selected_projects': selected,
            'selected_indices': [p['index'] for p in selected],
            'total_cost': total_cost,
            'total_benefit': total_benefit,
            'roi': total_benefit / total_cost if total_cost > 0 else 0,
            'budget_utilization': total_cost / budget_constraint * 100
        }
    
    def sensitivity_analysis(self, projects: List[Dict], budget_range: List[float]) -> List[Dict]:
        """Analyze how results change with different budgets"""
        results = []
        
        for budget in budget_range:
            result = self.optimize(projects, budget)
            result['budget'] = budget
            results.append(result)
        
        return results
    
    def generate_report(self, optimization_result: Dict) -> str:
        """Generate a human-readable report"""
        report = []
        report.append("=" * 60)
        report.append("INFRASTRUCTURE OPTIMIZATION REPORT")
        report.append("=" * 60)
        report.append("")
        report.append(f"Total Projects Selected: {len(optimization_result['selected_projects'])}")
        report.append(f"Total Cost: ${optimization_result['total_cost']:.2f}M")
        report.append(f"Total Benefit Score: {optimization_result['total_benefit']:.2f}")
        report.append(f"ROI: {optimization_result['roi']:.2f}x")
        report.append(f"Budget Utilization: {optimization_result['budget_utilization']:.1f}%")
        report.append("")
        report.append("-" * 60)
        report.append("SELECTED PROJECTS:")
        report.append("-" * 60)
        
        for i, project in enumerate(optimization_result['selected_projects'], 1):
            report.append(f"\n{i}. {project.get('name', f'Project {i}')}")
            report.append(f"   Action: {project.get('action', 'N/A')}")
            report.append(f"   Cost: ${project.get('cost', 0):.2f}M")
            report.append(f"   Benefit: {project.get('benefit_score', 0):.2f}")
            report.append(f"   Priority: {project.get('priority', 'N/A')}")
        
        return "\n".join(report)


class ProjectPrioritizer:
    """
    Prioritize projects based on multiple criteria
    """
    
    def __init__(self, weights: Dict[str, float] = None):
        self.weights = weights or {
            'stress_reduction': 0.35,
            'cost_efficiency': 0.25,
            'population_impact': 0.20,
            'safety_improvement': 0.15,
            'strategic_value': 0.05
        }
    
    def calculate_priority_score(self, project: Dict) -> float:
        """Calculate priority score for a project"""
        scores = {
            'stress_reduction': project.get('stress_reduction', 0),
            'cost_efficiency': 1 / max(project.get('cost', 1), 0.1),
            'population_impact': project.get('population_affected', 0) / 100000,
            'safety_improvement': project.get('safety_improvement', 0),
            'strategic_value': project.get('strategic_value', 0.5)
        }
        
        # Normalize scores to 0-1 range
        for key in scores:
            scores[key] = min(1.0, max(0, scores[key]))
        
        # Calculate weighted sum
        priority_score = sum(
            self.weights[key] * scores[key] 
            for key in self.weights
        )
        
        return priority_score
    
    def prioritize(self, projects: List[Dict]) -> List[Dict]:
        """Sort projects by priority score"""
        for project in projects:
            project['priority_score'] = self.calculate_priority_score(project)
        
        return sorted(projects, key=lambda x: x['priority_score'], reverse=True)
