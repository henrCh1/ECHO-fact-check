"""Benchmark Main Program - Self-Evolving System Without Feedback"""

import os
import sys
import argparse
from dotenv import load_dotenv
from pathlib import Path
import json
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib
import time
import io
from contextlib import redirect_stdout, redirect_stderr
matplotlib.use('Agg')  # Non-interactive backend

from agents.generator import GeneratorAgent
from agents.reflector import ReflectorAgent
from agents.curator import CuratorAgent
from utils.playbook_manager import PlaybookManager
from utils.benchmark_loader import BenchmarkLoader
from utils.metrics_calculator import MetricsCalculator, Metrics
from utils.feishu_notifier import FeishuNotifier

# Load environment variables
load_dotenv()

class BenchmarkSystem:
    """Benchmark Test System - Self-Evolving Without Feedback"""
    
    def __init__(self, dataset_path: str = "data/benchmark.csv", use_empty_playbook: bool = False):
        # Create shared PlaybookManager instance
        self.playbook_manager = PlaybookManager(use_empty_playbook=use_empty_playbook)
        
        # Pass PlaybookManager to all Agents that need it
        self.generator = GeneratorAgent(playbook_manager=self.playbook_manager)
        self.reflector = ReflectorAgent()
        self.curator = CuratorAgent(playbook_manager=self.playbook_manager)
        
        self.benchmark_loader = BenchmarkLoader(dataset_path)
        self.metrics_calculator = MetricsCalculator()
        self.use_empty_playbook = use_empty_playbook
        
        # Feishu webhook configuration
        self.feishu_webhook_url = "https://www.feishu.cn/flow/api/trigger-webhook/0620524d60f9b87ba8fb458ef30f68ac"
        self.notify_interval = 10  # Notify every 10 cases
        self.feishu_notifier = FeishuNotifier(self.feishu_webhook_url)
        
        # Time tracking
        self.start_time = None
        
        # Log file configuration
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        self.log_file = self.log_dir / f"benchmark_full_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        # Create run log
        self.run_log_dir = Path("data/benchmark_runs")
        self.run_log_dir.mkdir(parents=True, exist_ok=True)
        self.current_run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_run_dir = self.run_log_dir / self.current_run_id
        self.current_run_dir.mkdir(exist_ok=True)
        
        # Store all prediction results
        self.predictions = []
        
        # Evolution curve data
        self.evolution_data = {
            'case_numbers': [],
            'global_accuracy': []
        }
    
    def run_single_case(self, case, case_index: int, total_cases: int) -> None:
        """Run single case"""
        
        # Create output buffer to capture terminal output
        case_output_buffer = io.StringIO()
        
        # Save original stdout/stderr
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        
        # Create a Tee class to output to both terminal and buffer
        class TeeOutput:
            def __init__(self, *outputs):
                self.outputs = outputs
            
            def write(self, data):
                for output in self.outputs:
                    output.write(data)
                    output.flush()
            
            def flush(self):
                for output in self.outputs:
                    output.flush()
        
        # Redirect output to both terminal and buffer
        sys.stdout = TeeOutput(original_stdout, case_output_buffer)
        sys.stderr = TeeOutput(original_stderr, case_output_buffer)
        
        try:
            print(f"\n{'='*80}")
            print(f"Case {case_index + 1}/{total_cases} (Row {case.row_number})")
            print(f"{'='*80}\n")
            print(f"Statement to verify: {case.statement}\n")
            
            # Step 1: AgentA generates verdict
            print("=" * 80)
            print("Step 1: AgentA Executing Fact-Check")
            print("=" * 80)
            verdict = self.generator.execute(case.statement)
            
            # Save verdict
            case_file = self.current_run_dir / f"{verdict.case_id}_verdict.json"
            with open(case_file, 'w', encoding='utf-8') as f:
                json.dump(verdict.model_dump(), f, ensure_ascii=False, indent=2, default=str)
            
            # Record prediction result
            self.predictions.append({
                'case_id': verdict.case_id,
                'row_number': case.row_number,
                'statement': case.statement,
                'ground_truth': case.rating,
                'prediction': verdict.verdict,
                'confidence': verdict.confidence
            })
            
            # Step 2: AgentB reflects (no feedback needed, directly based on reasoning process)
            print("\n" + "=" * 80)
            print("Step 2: AgentB Self-Reflection")
            print("=" * 80)
            insight = self.reflector.reflect(verdict)
            
            # Save insight
            insight_file = self.current_run_dir / f"{verdict.case_id}_insight.json"
            with open(insight_file, 'w', encoding='utf-8') as f:
                json.dump(insight.model_dump(), f, ensure_ascii=False, indent=2, default=str)
            
            # Step 3: AgentC curates
            print("\n" + "=" * 80)
            print("Step 3: AgentC Generating Rule Update")
            print("=" * 80)
            delta = self.curator.curate(insight, verdict.case_id, verdict.verdict)
            
            # Save delta
            delta_file = self.current_run_dir / f"{verdict.case_id}_delta.json"
            with open(delta_file, 'w', encoding='utf-8') as f:
                json.dump(delta.model_dump(), f, ensure_ascii=False, indent=2, default=str)
            
            # Step 4: Apply update
            print("\n" + "=" * 80)
            print("Step 4: Applying Update to Playbook")
            print("=" * 80)
            self.curator.apply_update(delta)
            
            # Calculate current cumulative metrics
            current_metrics = self._calculate_current_metrics()
            self.evolution_data['case_numbers'].append(case_index + 1)
            self.evolution_data['global_accuracy'].append(current_metrics.global_accuracy)
            
            print(f"\n{'='*80}")
            print(f"Case {verdict.case_id} Processing Complete")
            print(f"   Current Cumulative Accuracy: {current_metrics.global_accuracy:.2%}")
            print(f"{'='*80}\n")
            
        finally:
            # Restore original stdout/stderr
            sys.stdout = original_stdout
            sys.stderr = original_stderr
        
        # Get full terminal output
        full_output = case_output_buffer.getvalue()
        case_output_buffer.close()
        
        # Write to local log file (every case)
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*80}\n")
                f.write(f"Case {case_index + 1}/{total_cases} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"{'='*80}\n")
                f.write(full_output)
                f.write("\n")
        except Exception as e:
            print(f"[WARNING] Failed to write to log file: {e}")
        
        # Send Feishu notification every N cases
        if (case_index + 1) % self.notify_interval == 0:
            elapsed_time = time.time() - self.start_time
            playbook = self.playbook_manager.load_playbook()
            active_rules = playbook.get_active_rules()
            
            self.feishu_notifier.send_progress(
                current_case=case_index + 1,
                total_cases=total_cases,
                accuracy=f"{current_metrics.global_accuracy:.2%}",
                rule_base_info=f"{playbook.version}, {len(active_rules)} active rules",
                verdict=verdict.verdict,
                confidence=verdict.confidence,
                processing_time=self._format_time(elapsed_time),
                full_terminal_output=full_output
            )
    
    def run_full_benchmark(self) -> None:
        """Run full benchmark"""
        
        # Initialize start time
        self.start_time = time.time()
        
        print(f"\n{'#'*80}")
        print(f"# Starting Benchmark Test")
        print(f"# Run ID: {self.current_run_id}")
        if self.use_empty_playbook:
            print(f"# Mode: Empty Rule Base Test (0 initial rules)")
        else:
            print(f"# Mode: Standard Rule Base Test (5 initial rules)")
        print(f"{'#'*80}\n")
        
        # Display initial rule base status
        playbook = self.playbook_manager.load_playbook()
        print(f"Initial State: {playbook.version}, {len(playbook.get_active_rules())} active rules\n")
        
        # Load dataset
        print("Loading Benchmark dataset...")
        cases = self.benchmark_loader.load_benchmark_dataset()
        
        # Process each case
        for idx, case in enumerate(cases):
            try:
                self.run_single_case(case, idx, len(cases))
                
                # Display current rule count
                playbook = self.playbook_manager.load_playbook()
                active_rules = playbook.get_active_rules()
                print(f"Current Rule Base: {playbook.version}, {len(active_rules)} active rules\n")
                
                
            except Exception as e:
                # Check if it's a Pydantic ValidationError
                from pydantic import ValidationError
                
                if isinstance(e, ValidationError):
                    print(f"❌ Case {idx + 1} Playbook validation failed: {e}")
                    print("🔧 Attempting auto-fix with playbook validator...")
                    
                    try:
                        # Run health check and auto-fix
                        from utils.playbook_validator import PlaybookValidator
                        validator = PlaybookValidator()
                        
                        detection_path = Path('data/playbook/detection_memory.json')
                        trust_path = Path('data/playbook/trust_memory.json')
                        
                        result_detection = validator.validate_and_fix_file(detection_path)
                        result_trust = validator.validate_and_fix_file(trust_path)
                        
                        total_fixes = result_detection.get('fixes_applied', 0) + result_trust.get('fixes_applied', 0)
                        
                        if total_fixes > 0:
                            print(f"✅ Auto-fixed {total_fixes} issues")
                            
                            # Reload PlaybookManager with fixed data
                            self.playbook_manager = PlaybookManager(use_empty_playbook=self.use_empty_playbook)
                            self.generator.playbook_manager = self.playbook_manager
                            self.curator.playbook_manager = self.playbook_manager
                            
                            # Retry current case
                            print("🔄 Retrying current case...")
                            return self.run_single_case(case, idx, total_cases)
                        else:
                            print("⚠️  No auto-fixes available, skipping case")
                    
                    except Exception as fix_error:
                        print(f"❌ Auto-fix failed: {fix_error}")
                
                # For all other errors or if auto-fix failed
                print(f"❌ Case {idx + 1} processing failed: {e}")
                import traceback
                traceback.print_exc()
                
                # Record failed prediction (mark as Unverifiable)
                self.predictions.append({
                    'case_id': f'failed_{idx+1}',
                    'row_number': case.row_number,
                    'statement': case.statement,
                    'ground_truth': case.rating,
                    'prediction': 'Unverifiable',
                    'confidence': 0.0,
                    'error': str(e)
                })
                continue
        
        # Generate final report
        self._generate_final_report()
    
    def _calculate_current_metrics(self) -> Metrics:
        """Calculate current cumulative metrics"""
        cm = self.metrics_calculator.calculate_confusion_matrix(self.predictions)
        metrics = self.metrics_calculator.calculate_metrics(cm)
        return metrics
    
    def _format_time(self, seconds: float) -> str:
        """Format elapsed time into human-readable string"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
    
    def _generate_final_report(self) -> None:
        """Generate final report"""
        
        print("\n" + "="*80)
        print("Benchmark Test Complete!")
        print("="*80)
        
        # Calculate final metrics
        final_metrics = self._calculate_current_metrics()
        
        # Print metrics
        self.metrics_calculator.print_metrics(final_metrics)
        
        # Rule base evolution
        playbook = self.playbook_manager.load_playbook()
        print("\nRule Base Evolution:")
        print(f"   Initial Version: v1.0 (5 rules)")
        print(f"   Final Version: {playbook.version} ({len(playbook.get_active_rules())} active rules)")
        
        try:
            version_updates = int(playbook.version.split('.')[1])
            print(f"   Version Increments: {version_updates} updates")
        except:
            print(f"   Version Increments: Unknown")
        
        # Plot evolution curve
        self._plot_evolution_curve()
        
        # Save detailed report
        self._save_detailed_report(final_metrics)
        
        print("\nOutput Files:")
        print(f"   Case Details: {self.current_run_dir}")
        print(f"   Evaluation Report: {self.current_run_dir / 'benchmark_report.json'}")
        print(f"   Evolution Curve: {self.current_run_dir / 'evolution_curve.png'}")
        print("\n" + "="*80 + "\n")
    
    def _plot_evolution_curve(self) -> None:
        """Plot evolution curve"""
        
        try:
            plt.figure(figsize=(12, 6))
            plt.plot(
                self.evolution_data['case_numbers'],
                [acc * 100 for acc in self.evolution_data['global_accuracy']],
                marker='o',
                markersize=3,
                linewidth=2,
                color='#2E86AB'
            )
            
            plt.xlabel('Case Number', fontsize=12)
            plt.ylabel('Global Accuracy (%)', fontsize=12)
            plt.title('Self-Evolving System Accuracy Curve', fontsize=14, fontweight='bold')
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            # Save figure
            plot_file = self.current_run_dir / 'evolution_curve.png'
            plt.savefig(plot_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"\n📈 Evolution curve saved: {plot_file}")
            
        except Exception as e:
            print(f"⚠️  Failed to plot evolution curve: {e}")
    
    def _save_detailed_report(self, metrics: Metrics) -> None:
        """Save detailed report"""
        
        playbook = self.playbook_manager.load_playbook()
        
        report = {
            'run_id': self.current_run_id,
            'timestamp': datetime.now().isoformat(),
            'dataset_size': len(self.predictions),
            
            # Evaluation metrics
            'metrics': metrics.to_dict(),
            
            # All prediction results
            'predictions': self.predictions,
            
            # Evolution data
            'evolution': {
                'case_numbers': self.evolution_data['case_numbers'],
                'global_accuracy': self.evolution_data['global_accuracy']
            },
            
            # Rule base status
            'playbook': {
                'version': playbook.version,
                'total_rules': len(playbook.rules),
                'active_rules': len(playbook.get_active_rules()),
                'rules': [
                    {
                        'rule_id': r.rule_id,
                        'type': r.type,
                        'condition': r.condition,
                        'action': r.action,
                        'confidence': r.confidence,
                        'active': r.active
                    }
                    for r in playbook.rules
                ]
            }
        }
        
        # Save as JSON
        report_file = self.current_run_dir / 'benchmark_report.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"📄 Detailed report saved: {report_file}")


def main():
    """Main function"""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Benchmark Test System - Self-Evolving System Without Human Feedback",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--empty-playbook',
        action='store_true',
        help='Initialize with empty rule base (0 rules), for testing if system needs initial rules'
    )
    parser.add_argument(
        '--dataset',
        type=str,
        default='data/benchmark.csv',
        help='Benchmark dataset path (default: data/benchmark.csv)'
    )
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("Benchmark Test System")
    print("="*80)
    print("Feature: Self-Evolving System Without Human Feedback")
    print(f"Dataset: {args.dataset}")
    if args.empty_playbook:
        print("[WARNING] Mode: Empty Rule Base Test (0 initial rules)")
    else:
        print("[OK] Mode: Standard Rule Base Test (5 initial rules)")
    print("="*80 + "\n")
    
    # Confirm to continue
    if args.empty_playbook:
        print("[WARNING] Empty rule base mode will evolve from scratch, initial accuracy may be low")
    confirm = input("Start Benchmark test? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Cancelled")
        return
    
    # Initialize system
    try:
        system = BenchmarkSystem(
            dataset_path=args.dataset,
            use_empty_playbook=args.empty_playbook
        )
    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
        print(f"\nPlease ensure {args.dataset} file exists")
        print("File format requirements:")
        print("  - First row is header: Statement,Rating")
        print("  - Statement: Claim to verify")
        print("  - Rating: Ground truth (True/False)")
        return
    except Exception as e:
        print(f"[ERROR] Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Run benchmark
    try:
        system.run_full_benchmark()
    except KeyboardInterrupt:
        print("\n\n[WARNING] User interrupted")
        print("Processed cases have been saved")
        system._generate_final_report()
    except Exception as e:
        print(f"\n[ERROR] Error during execution: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()