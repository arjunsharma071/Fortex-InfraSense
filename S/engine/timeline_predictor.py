# engine/timeline_predictor.py
"""
InfraSense AI - Construction Timeline Predictor
Uses Monte Carlo simulation for realistic timeline predictions
Includes critical path analysis and risk assessment
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np
import random
from datetime import datetime, timedelta


class ProjectPhase(Enum):
    """Construction project phases"""
    PLANNING = "planning"
    DESIGN = "design"
    APPROVALS = "approvals"
    LAND_ACQUISITION = "land_acquisition"
    TENDERING = "tendering"
    MOBILIZATION = "mobilization"
    CONSTRUCTION = "construction"
    TESTING = "testing"
    COMMISSIONING = "commissioning"


@dataclass
class PhaseRisk:
    """Risk factors for a phase"""
    name: str
    probability: float  # 0-1
    impact_months: float
    mitigation: str


class ConstructionTimelinePredictor:
    """
    Predicts realistic construction timelines with Monte Carlo simulation
    Accounts for country-specific factors, approvals, and risks
    """
    
    # Phase durations in months [min, max] by country
    PHASE_DURATIONS = {
        'planning': {
            'IN': [3, 8],    # India - variable bureaucracy
            'US': [6, 12],   # USA - thorough planning required
            'DE': [4, 8],    # Germany - efficient but thorough
            'NG': [2, 12],   # Nigeria - unpredictable
            'BR': [4, 10],   # Brazil - moderate
            'AU': [5, 10],   # Australia
            'JP': [4, 8],    # Japan - efficient
            'CN': [2, 5],    # China - fast-tracked
            'UK': [5, 10],   # UK
            'FR': [4, 9],    # France
            'AE': [2, 5],    # UAE - expedited
            'MX': [3, 9],    # Mexico
            'ZA': [4, 10],   # South Africa
            'ID': [3, 10],   # Indonesia
            'SA': [2, 6],    # Saudi Arabia
        },
        'design': {
            'IN': [3, 6],
            'US': [4, 8],
            'DE': [4, 7],
            'NG': [2, 8],
            'BR': [3, 7],
            'AU': [4, 7],
            'JP': [3, 6],
            'CN': [2, 5],
            'UK': [4, 7],
            'FR': [3, 6],
            'AE': [2, 4],
            'MX': [2, 6],
            'ZA': [3, 7],
            'ID': [2, 7],
            'SA': [2, 5],
        },
        'approvals': {
            'IN': [6, 18],   # Can be very slow
            'US': [8, 24],   # Environmental reviews
            'DE': [4, 10],   # Efficient processes
            'NG': [4, 30],   # Highly unpredictable
            'BR': [8, 20],   # Environmental licensing complex
            'AU': [6, 14],
            'JP': [4, 10],
            'CN': [2, 6],    # Streamlined
            'UK': [6, 15],
            'FR': [5, 12],
            'AE': [2, 5],    # Fast-track possible
            'MX': [4, 14],
            'ZA': [5, 16],
            'ID': [4, 18],
            'SA': [2, 6],
        },
        'land_acquisition': {
            'IN': [6, 24],   # Major bottleneck
            'US': [3, 12],
            'DE': [2, 8],
            'NG': [3, 18],
            'BR': [4, 15],
            'AU': [2, 8],
            'JP': [4, 12],
            'CN': [1, 4],    # State-owned land
            'UK': [3, 10],
            'FR': [3, 10],
            'AE': [1, 3],    # State-owned
            'MX': [3, 12],
            'ZA': [4, 15],
            'ID': [4, 18],
            'SA': [1, 4],    # State-owned
        },
        'tendering': {
            'IN': [2, 4],
            'US': [3, 6],
            'DE': [2, 5],
            'NG': [2, 6],
            'BR': [2, 5],
            'AU': [2, 5],
            'JP': [2, 4],
            'CN': [1, 3],
            'UK': [2, 5],
            'FR': [2, 4],
            'AE': [1, 3],
            'MX': [2, 4],
            'ZA': [2, 5],
            'ID': [2, 5],
            'SA': [1, 3],
        },
        'commissioning': {
            'IN': [1, 3],
            'US': [2, 4],
            'DE': [1, 3],
            'NG': [1, 4],
            'BR': [1, 3],
            'AU': [1, 3],
            'JP': [1, 2],
            'CN': [1, 2],
            'UK': [1, 3],
            'FR': [1, 2],
            'AE': [1, 2],
            'MX': [1, 3],
            'ZA': [1, 4],
            'ID': [1, 4],
            'SA': [1, 2],
        }
    }
    
    # Construction rates (months per km) by project type
    CONSTRUCTION_RATES = {
        'road_widening': {
            'base_months_per_km': 1.2,
            'parallel_sections': 3,  # Can work on 3 sections simultaneously
        },
        'flyover': {
            'base_months_per_km': 4.5,
            'parallel_sections': 2,
        },
        'bridge': {
            'base_months_per_km': 6.0,
            'parallel_sections': 1,
        },
        'tunnel': {
            'base_months_per_km': 12.0,
            'parallel_sections': 1,
        },
        'interchange': {
            'base_months_total': 24,  # Fixed duration regardless of size
            'parallel_sections': 2,
        },
        'resurfacing': {
            'base_months_per_km': 0.3,
            'parallel_sections': 5,
        },
        'brt_corridor': {
            'base_months_per_km': 2.0,
            'parallel_sections': 3,
        }
    }
    
    # Country-specific efficiency factors
    EFFICIENCY_FACTORS = {
        'IN': 0.75,   # Delays common
        'US': 0.85,
        'DE': 0.95,   # Very efficient
        'NG': 0.55,   # Significant delays
        'BR': 0.70,
        'AU': 0.90,
        'JP': 0.98,   # Extremely efficient
        'CN': 0.92,   # Fast execution
        'UK': 0.85,
        'FR': 0.88,
        'AE': 0.90,   # Well-resourced
        'MX': 0.65,
        'ZA': 0.60,
        'ID': 0.60,
        'SA': 0.85,
    }
    
    # Risk factors by country
    COUNTRY_RISKS = {
        'IN': [
            PhaseRisk('Monsoon delays', 0.8, 3, 'Schedule work outside monsoon season'),
            PhaseRisk('Land disputes', 0.4, 6, 'Pre-emptive legal clearances'),
            PhaseRisk('Political changes', 0.2, 4, 'Multi-party consensus building'),
            PhaseRisk('Labor shortages', 0.3, 2, 'Contract with multiple vendors'),
        ],
        'US': [
            PhaseRisk('Environmental lawsuits', 0.3, 12, 'Early stakeholder engagement'),
            PhaseRisk('Labor strikes', 0.15, 2, 'Union negotiations'),
            PhaseRisk('Material supply chain', 0.2, 3, 'Diversified suppliers'),
            PhaseRisk('Regulatory changes', 0.1, 4, 'Legal buffer in contracts'),
        ],
        'BR': [
            PhaseRisk('Rain season delays', 0.7, 4, 'Seasonal scheduling'),
            PhaseRisk('Environmental licensing', 0.5, 8, 'Pre-filing environmental studies'),
            PhaseRisk('Corruption investigations', 0.2, 6, 'Compliance programs'),
            PhaseRisk('Economic instability', 0.3, 3, 'Currency hedging'),
        ],
        'NG': [
            PhaseRisk('Funding delays', 0.6, 8, 'Escrow arrangements'),
            PhaseRisk('Security issues', 0.4, 4, 'Security protocols'),
            PhaseRisk('Equipment import delays', 0.5, 3, 'Pre-position equipment'),
            PhaseRisk('Fuel shortages', 0.3, 2, 'Backup fuel storage'),
        ],
    }
    
    def __init__(self, simulation_runs: int = 1000):
        self.simulation_runs = simulation_runs
    
    def predict_timeline(self, 
                         project_type: str,
                         length_km: float,
                         country_code: str,
                         complexity: str = 'medium',
                         start_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Predict project timeline with Monte Carlo simulation
        """
        if start_date is None:
            start_date = datetime.now()
        
        # Get construction rate
        construction_config = self.CONSTRUCTION_RATES.get(
            project_type, 
            self.CONSTRUCTION_RATES['road_widening']
        )
        
        # Calculate construction duration
        if 'base_months_total' in construction_config:
            base_construction_months = construction_config['base_months_total']
        else:
            base_construction_months = (
                construction_config['base_months_per_km'] * length_km /
                construction_config['parallel_sections']
            )
        
        # Apply complexity factor
        complexity_factors = {'low': 0.8, 'medium': 1.0, 'high': 1.3, 'very_high': 1.6}
        complexity_mult = complexity_factors.get(complexity, 1.0)
        base_construction_months *= complexity_mult
        
        # Apply country efficiency
        efficiency = self.EFFICIENCY_FACTORS.get(country_code, 0.7)
        base_construction_months /= efficiency
        
        # Run Monte Carlo simulation
        timelines = self._run_monte_carlo(
            country_code, 
            base_construction_months,
            project_type
        )
        
        # Calculate statistics
        avg_timeline = np.mean(timelines)
        p10 = np.percentile(timelines, 10)   # Best case (10th percentile)
        p50 = np.percentile(timelines, 50)   # Most likely
        p90 = np.percentile(timelines, 90)   # Worst case
        std_dev = np.std(timelines)
        
        # Generate phase breakdown
        phases = self._generate_phase_breakdown(
            country_code, 
            base_construction_months,
            project_type,
            start_date
        )
        
        # Identify critical path
        critical_path = self._identify_critical_path(phases)
        
        # Get bottlenecks and risks
        bottlenecks = self._identify_bottlenecks(country_code, project_type)
        risks = self.COUNTRY_RISKS.get(country_code, [])
        
        # Calculate key dates
        estimated_completion = start_date + timedelta(days=int(avg_timeline * 30))
        best_case_completion = start_date + timedelta(days=int(p10 * 30))
        worst_case_completion = start_date + timedelta(days=int(p90 * 30))
        
        return {
            'project_type': project_type,
            'length_km': length_km,
            'country_code': country_code,
            'complexity': complexity,
            'start_date': start_date.isoformat(),
            'timeline_months': {
                'estimated': round(avg_timeline, 1),
                'best_case': round(p10, 1),
                'most_likely': round(p50, 1),
                'worst_case': round(p90, 1),
                'standard_deviation': round(std_dev, 1)
            },
            'completion_dates': {
                'estimated': estimated_completion.strftime('%Y-%m-%d'),
                'best_case': best_case_completion.strftime('%Y-%m-%d'),
                'worst_case': worst_case_completion.strftime('%Y-%m-%d')
            },
            'phases': phases,
            'critical_path': critical_path,
            'bottlenecks': bottlenecks,
            'risks': [
                {
                    'name': r.name,
                    'probability': f"{r.probability*100:.0f}%",
                    'impact': f"+{r.impact_months} months",
                    'mitigation': r.mitigation
                }
                for r in risks
            ],
            'acceleration_options': self._get_acceleration_strategies(country_code, phases),
            'gantt_chart_data': self._generate_gantt_data(phases),
            'confidence_level': self._calculate_confidence(country_code, project_type),
            'similar_projects': self._get_similar_projects(country_code, project_type, length_km)
        }
    
    def _run_monte_carlo(self, country_code: str, 
                         construction_months: float,
                         project_type: str) -> List[float]:
        """Run Monte Carlo simulation for timeline estimation"""
        timelines = []
        
        for _ in range(self.simulation_runs):
            total = 0
            
            # Add pre-construction phases
            for phase in ['planning', 'design', 'approvals', 'land_acquisition', 'tendering']:
                phase_config = self.PHASE_DURATIONS[phase]
                min_d, max_d = phase_config.get(country_code, phase_config.get('IN', [2, 6]))
                
                # Use triangular distribution (more realistic than uniform)
                mode = (min_d + max_d) / 2
                duration = np.random.triangular(min_d, mode, max_d)
                total += duration
            
            # Construction phase with variability
            construction_variability = construction_months * 0.2
            actual_construction = np.random.normal(
                construction_months, 
                construction_variability
            )
            actual_construction = max(construction_months * 0.7, actual_construction)
            total += actual_construction
            
            # Commissioning
            comm_config = self.PHASE_DURATIONS['commissioning']
            min_d, max_d = comm_config.get(country_code, comm_config.get('IN', [1, 3]))
            total += np.random.uniform(min_d, max_d)
            
            # Add risk events
            risks = self.COUNTRY_RISKS.get(country_code, [])
            for risk in risks:
                if random.random() < risk.probability:
                    total += risk.impact_months * random.uniform(0.5, 1.0)
            
            timelines.append(total)
        
        return timelines
    
    def _generate_phase_breakdown(self, country_code: str,
                                   construction_months: float,
                                   project_type: str,
                                   start_date: datetime) -> List[Dict]:
        """Generate detailed phase breakdown with dates"""
        phases = []
        current_date = start_date
        
        phase_order = ['planning', 'design', 'approvals', 'land_acquisition', 
                       'tendering', 'mobilization', 'construction', 'commissioning']
        
        for phase_name in phase_order:
            if phase_name == 'construction':
                duration = construction_months
            elif phase_name == 'mobilization':
                duration = 1.5  # Fixed mobilization period
            else:
                phase_config = self.PHASE_DURATIONS.get(phase_name, {'IN': [2, 4]})
                min_d, max_d = phase_config.get(country_code, phase_config.get('IN', [2, 4]))
                duration = (min_d + max_d) / 2
            
            end_date = current_date + timedelta(days=int(duration * 30))
            
            phases.append({
                'name': phase_name.replace('_', ' ').title(),
                'duration_months': round(duration, 1),
                'start_date': current_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'is_critical': phase_name in ['approvals', 'land_acquisition', 'construction'],
                'dependencies': self._get_phase_dependencies(phase_name),
                'resources': self._get_phase_resources(phase_name),
                'milestones': self._get_phase_milestones(phase_name)
            })
            
            current_date = end_date
        
        return phases
    
    def _get_phase_dependencies(self, phase_name: str) -> List[str]:
        """Get dependencies for a phase"""
        dependencies = {
            'planning': [],
            'design': ['planning'],
            'approvals': ['design'],
            'land_acquisition': ['approvals'],
            'tendering': ['design', 'approvals'],
            'mobilization': ['tendering', 'land_acquisition'],
            'construction': ['mobilization'],
            'commissioning': ['construction']
        }
        return dependencies.get(phase_name, [])
    
    def _get_phase_resources(self, phase_name: str) -> List[str]:
        """Get resource requirements for a phase"""
        resources = {
            'planning': ['Project Manager', 'Planning Team', 'Surveyors'],
            'design': ['Civil Engineers', 'Structural Engineers', 'CAD Operators'],
            'approvals': ['Legal Team', 'Environmental Consultants', 'Government Liaisons'],
            'land_acquisition': ['Land Officers', 'Legal Team', 'Valuers'],
            'tendering': ['Procurement Team', 'Technical Evaluators'],
            'mobilization': ['Site Manager', 'Equipment', 'Initial Workforce'],
            'construction': ['Full Construction Team', 'Heavy Equipment', 'Materials'],
            'commissioning': ['Testing Team', 'Quality Inspectors', 'Handover Team']
        }
        return resources.get(phase_name, [])
    
    def _get_phase_milestones(self, phase_name: str) -> List[str]:
        """Get key milestones for a phase"""
        milestones = {
            'planning': ['Feasibility Study Complete', 'DPR Approved'],
            'design': ['30% Design Review', '100% Design Complete'],
            'approvals': ['Environmental Clearance', 'All Permits Obtained'],
            'land_acquisition': ['Compensation Disbursed', 'Possession Taken'],
            'tendering': ['Bid Opening', 'Contract Award'],
            'mobilization': ['Site Handover', 'Equipment Ready'],
            'construction': ['Foundation Complete', 'Superstructure Complete', 'Finishing'],
            'commissioning': ['Testing Complete', 'Final Inspection', 'Opening Ceremony']
        }
        return milestones.get(phase_name, [])
    
    def _identify_critical_path(self, phases: List[Dict]) -> Dict[str, Any]:
        """Identify the critical path through the project"""
        critical_phases = [p for p in phases if p['is_critical']]
        total_critical_duration = sum(p['duration_months'] for p in critical_phases)
        
        return {
            'phases': [p['name'] for p in critical_phases],
            'total_duration_months': round(total_critical_duration, 1),
            'bottleneck_phase': max(critical_phases, key=lambda x: x['duration_months'])['name'],
            'float_available': False,  # Critical path has no float
            'description': 'Any delay in these phases will delay the entire project'
        }
    
    def _identify_bottlenecks(self, country_code: str, 
                               project_type: str) -> List[Dict[str, str]]:
        """Identify potential bottlenecks by country"""
        bottlenecks = {
            'IN': [
                {'phase': 'Land Acquisition', 'issue': 'Compensation disputes', 'severity': 'high'},
                {'phase': 'Approvals', 'issue': 'Multiple agency clearances', 'severity': 'high'},
                {'phase': 'Construction', 'issue': 'Monsoon season (Jun-Sep)', 'severity': 'medium'}
            ],
            'US': [
                {'phase': 'Approvals', 'issue': 'Environmental Impact Statement', 'severity': 'high'},
                {'phase': 'Planning', 'issue': 'Public consultation requirements', 'severity': 'medium'}
            ],
            'BR': [
                {'phase': 'Approvals', 'issue': 'Environmental licensing (IBAMA)', 'severity': 'high'},
                {'phase': 'Construction', 'issue': 'Rainy season (Nov-Mar)', 'severity': 'medium'}
            ],
            'NG': [
                {'phase': 'Approvals', 'issue': 'Bureaucratic delays', 'severity': 'high'},
                {'phase': 'Construction', 'issue': 'Funding disbursement', 'severity': 'high'},
                {'phase': 'Mobilization', 'issue': 'Equipment import', 'severity': 'medium'}
            ]
        }
        
        return bottlenecks.get(country_code, [
            {'phase': 'Approvals', 'issue': 'Regulatory clearances', 'severity': 'medium'}
        ])
    
    def _get_acceleration_strategies(self, country_code: str,
                                      phases: List[Dict]) -> List[Dict[str, Any]]:
        """Get strategies to accelerate the project"""
        strategies = [
            {
                'strategy': 'Fast-track design and approvals',
                'time_saved_months': 3,
                'cost_increase_percent': 10,
                'risk': 'Design changes during construction',
                'applicable_phases': ['Design', 'Approvals']
            },
            {
                'strategy': 'Pre-qualification of contractors',
                'time_saved_months': 2,
                'cost_increase_percent': 0,
                'risk': 'Limited competition',
                'applicable_phases': ['Tendering']
            },
            {
                'strategy': 'Multiple work fronts',
                'time_saved_months': 4,
                'cost_increase_percent': 15,
                'risk': 'Coordination complexity',
                'applicable_phases': ['Construction']
            },
            {
                'strategy': 'Night shift construction',
                'time_saved_months': 2,
                'cost_increase_percent': 20,
                'risk': 'Quality control, noise complaints',
                'applicable_phases': ['Construction']
            },
            {
                'strategy': 'Pre-cast elements',
                'time_saved_months': 3,
                'cost_increase_percent': 8,
                'risk': 'Transportation logistics',
                'applicable_phases': ['Construction']
            }
        ]
        
        # Add country-specific strategies
        if country_code in ['AE', 'SA', 'CN']:
            strategies.append({
                'strategy': 'Government priority designation',
                'time_saved_months': 6,
                'cost_increase_percent': 0,
                'risk': 'Political dependency',
                'applicable_phases': ['Approvals', 'Land Acquisition']
            })
        
        return strategies
    
    def _generate_gantt_data(self, phases: List[Dict]) -> Dict[str, Any]:
        """Generate data for Gantt chart visualization"""
        return {
            'tasks': [
                {
                    'id': i + 1,
                    'name': p['name'],
                    'start': p['start_date'],
                    'end': p['end_date'],
                    'duration': p['duration_months'],
                    'critical': p['is_critical'],
                    'progress': 0,  # For tracking actual progress
                    'dependencies': [phases.index(dep) + 1 for dep_name in p['dependencies'] 
                                    for dep in phases if dep['name'].lower() == dep_name]
                }
                for i, p in enumerate(phases)
            ],
            'milestones': [
                {'name': m, 'phase': p['name']}
                for p in phases
                for m in p['milestones']
            ]
        }
    
    def _calculate_confidence(self, country_code: str, 
                               project_type: str) -> Dict[str, Any]:
        """Calculate confidence level of the estimate"""
        # Base confidence by country data quality
        base_confidence = {
            'IN': 75, 'US': 92, 'DE': 95, 'NG': 50, 'BR': 70,
            'AU': 90, 'JP': 95, 'CN': 70, 'UK': 90, 'FR': 88
        }
        
        confidence = base_confidence.get(country_code, 65)
        
        # Adjust for project complexity
        if project_type in ['tunnel', 'interchange']:
            confidence -= 10
        elif project_type == 'resurfacing':
            confidence += 5
        
        return {
            'level': 'HIGH' if confidence >= 80 else ('MEDIUM' if confidence >= 60 else 'LOW'),
            'score': confidence,
            'factors': [
                f"Historical data quality: {'Good' if confidence >= 75 else 'Limited'}",
                f"Project complexity: {project_type.replace('_', ' ').title()}",
                f"Regulatory predictability: {'High' if country_code in ['DE', 'JP', 'US'] else 'Variable'}"
            ]
        }
    
    def _get_similar_projects(self, country_code: str,
                               project_type: str,
                               length_km: float) -> List[Dict[str, Any]]:
        """Get similar completed projects for reference"""
        similar_projects = {
            ('IN', 'flyover'): [
                {'name': 'Hyderabad PVNR Expressway', 'length_km': 11.6, 'actual_months': 42, 'year': 2020},
                {'name': 'Chennai Port-Maduravoyal Elevated', 'length_km': 19, 'actual_months': 54, 'year': 2021}
            ],
            ('IN', 'road_widening'): [
                {'name': 'NH-44 Hyderabad-Bangalore', 'length_km': 85, 'actual_months': 36, 'year': 2022},
                {'name': 'Mumbai-Pune Expressway Widening', 'length_km': 15, 'actual_months': 24, 'year': 2023}
            ],
            ('BR', 'road_widening'): [
                {'name': 'Marginal Pinheiros Widening', 'length_km': 12, 'actual_months': 30, 'year': 2021},
            ]
        }
        
        key = (country_code, project_type)
        return similar_projects.get(key, [
            {'name': 'Generic comparison project', 'note': 'Limited historical data for this region'}
        ])


# Singleton instance
timeline_predictor = ConstructionTimelinePredictor()
