"""Warmup Automated Main Program - Supervised Rule Generation System"""

import os
import sys
from dotenv import load_dotenv
from pathlib import Path
import json
from datetime import datetime

# Reuse original system components
from agents.generator import GeneratorAgent
from agents.curator import CuratorAgent
from utils.playbook_manager import PlaybookManager

# Use warmup-specific components
from warmup.agents.feedback_agent import FeedbackAgent
from warmup.agents.warmup_reflector import WarmupReflectorAgent
from warmup.utils.warmup_dataset_loader import WarmupDatasetLoader

# Load environment variables
load_dotenv()


class WarmupFactCheckSystem:
    """Supervised Rule Generation System - Train rule base using Warmup dataset"""
    
    def __init__(self, dataset_path: str = "data/warmup.csv"):
        # Use independent warmup_playbook directory
        warmup_playbook_dir = "data/warmup_playbook"
        
        # Create Playbook manager (using independent directory)
        playbook_manager = PlaybookManager(
            playbook_dir=warmup_playbook_dir,
            use_empty_playbook=True  # warmup starts from empty rule base
        )
        
        # Reuse original system's Generator and Curator
        self.generator = GeneratorAgent(playbook_manager=playbook_manager)
        self.curator = CuratorAgent(playbook_manager=playbook_manager)
        
        # Use warmup-specific components
        self.reflector = WarmupReflectorAgent()
        self.feedback_agent = FeedbackAgent()
        
        # Keep reference for status display
        self.playbook_manager = playbook_manager
        self.dataset_loader = WarmupDatasetLoader(dataset_path)
        
        # Create log directories
        self.log_dir = Path("data/warmup_cases")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create run log
        self.run_log_dir = Path("data/warmup_runs")
        self.run_log_dir.mkdir(parents=True, exist_ok=True)
        self.current_run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_run_dir = self.run_log_dir / self.current_run_id
        self.current_run_dir.mkdir(exist_ok=True)
        
        # Statistics
        self.stats = {
            "total_cases": 0,
            "correct_verdicts": 0,
            "incorrect_verdicts": 0,
            "correct_reasoning": 0,
            "incorrect_reasoning": 0,
            "start_time": datetime.now().isoformat(),
            "cases_detail": []
        }
    
    def run_single_case(self, case, case_index: int, total_cases: int) -> None:
        """Run complete loop for a single case"""
        
        print(f"\n{'='*80}")
        print(f"Case {case_index + 1}/{total_cases} (row {case.row_number})")
        print(f"{'='*80}\n")
        print(f"Claim to verify: {case.statement}\n")
        
        # Step 1: Generator generates verdict (reuse original system)
        print("=" * 80)
        print("Step 1: Generator executes fact-checking")
        print("=" * 80)
        verdict = self.generator.execute(case.statement)
        
        # Save verdict
        case_file = self.current_run_dir / f"{verdict.case_id}_verdict.json"
        with open(case_file, 'w', encoding='utf-8') as f:
            json.dump(verdict.model_dump(), f, ensure_ascii=False, indent=2, default=str)
        
        # Step 2: FeedbackAgent generates feedback (warmup-specific)
        print("\n" + "=" * 80)
        print("Step 2: FeedbackAgent generates automated feedback")
        print("=" * 80)
        
        feedback = self.feedback_agent.generate_feedback(
            verdict=verdict,
            rating=case.rating,
            full_analysis=case.full_analysis
        )
        
        # Save feedback
        feedback_file = self.current_run_dir / f"{verdict.case_id}_feedback.json"
        with open(feedback_file, 'w', encoding='utf-8') as f:
            json.dump(feedback.model_dump(), f, ensure_ascii=False, indent=2, default=str)
        
        # Step 3: WarmupReflector reflects (warmup-specific, with supervision signal)
        print("\n" + "=" * 80)
        print("Step 3: WarmupReflector supervised reflection analysis")
        print("=" * 80)
        insight = self.reflector.reflect(verdict, feedback)
        
        # Save insight
        insight_file = self.current_run_dir / f"{verdict.case_id}_insight.json"
        with open(insight_file, 'w', encoding='utf-8') as f:
            json.dump(insight.model_dump(), f, ensure_ascii=False, indent=2, default=str)
        
        # Step 4: Curator curates (reuse original system, pass ground_truth as verdict_value)
        print("\n" + "=" * 80)
        print("Step 4: Curator generates rule update")
        print("=" * 80)
        
        # Important: Use ground_truth as verdict_value for label-based memory classification
        delta = self.curator.curate(
            insight, 
            verdict.case_id, 
            verdict_value=feedback.ground_truth  # True->trust, False->detection
        )
        
        # Save delta
        delta_file = self.current_run_dir / f"{verdict.case_id}_delta.json"
        with open(delta_file, 'w', encoding='utf-8') as f:
            json.dump(delta.model_dump(), f, ensure_ascii=False, indent=2, default=str)
        
        # Step 5: Apply update
        print("\n" + "=" * 80)
        print("Step 5: Apply update to Warmup Playbook")
        print("=" * 80)
        self.curator.apply_update(delta)
        
        # Update statistics
        self._update_stats(verdict, feedback, case)
        
        print(f"\n{'='*80}")
        print(f"Case {verdict.case_id} processing complete")
        print(f"{'='*80}\n")
    
    def run_full_dataset(self) -> None:
        """Run full dataset"""
        
        print(f"\n{'#'*80}")
        print(f"# Starting Warmup Supervised Rule Generation")
        print(f"# Run ID: {self.current_run_id}")
        print(f"{'#'*80}\n")
        
        # Show initial rule base status
        playbook = self.playbook_manager.load_playbook()
        print(f"Initial state: {playbook.version}, {len(playbook.get_active_rules())} active rules\n")
        
        # Load dataset
        print("Loading dataset...")
        cases = self.dataset_loader.load_warmup_dataset()
        self.stats["total_cases"] = len(cases)
        
        # Process each case
        for idx, case in enumerate(cases):
            try:
                self.run_single_case(case, idx, len(cases))
                
                # Show current rule count
                playbook = self.playbook_manager.load_playbook()
                active_rules = playbook.get_active_rules()
                print(f"Current rule base state: {playbook.version}, {len(active_rules)} active rules\n")
                
            except Exception as e:
                print(f"Case {idx + 1} processing failed: {e}")
                self.stats["cases_detail"].append({
                    "case_index": idx + 1,
                    "row_number": case.row_number,
                    "statement": case.statement,
                    "error": str(e),
                    "status": "failed"
                })
                continue
        
        # Final summary
        self._print_final_summary()
        self._save_run_report()
    
    def _update_stats(self, verdict, feedback, case) -> None:
        """Update statistics"""
        
        verdict_correct = (verdict.verdict == feedback.ground_truth)
        reasoning_correct = "correct_reasoning" in feedback.feedback_type
        
        if verdict_correct:
            self.stats["correct_verdicts"] += 1
        else:
            self.stats["incorrect_verdicts"] += 1
        
        if reasoning_correct:
            self.stats["correct_reasoning"] += 1
        else:
            self.stats["incorrect_reasoning"] += 1
        
        self.stats["cases_detail"].append({
            "case_id": verdict.case_id,
            "row_number": case.row_number,
            "statement": case.statement[:100] + "...",
            "agent_verdict": verdict.verdict,
            "ground_truth": feedback.ground_truth,
            "verdict_correct": verdict_correct,
            "reasoning_correct": reasoning_correct,
            "feedback_type": feedback.feedback_type
        })
    
    def _print_final_summary(self) -> None:
        """Print final summary"""
        
        playbook = self.playbook_manager.load_playbook()
        
        # Calculate accuracy
        total = self.stats['total_cases']
        if total == 0:
            return
        
        verdict_acc = self.stats['correct_verdicts'] / total * 100
        reasoning_acc = self.stats['correct_reasoning'] / total * 100
        
        # Print complete report
        print("\n" + "=" * 80)
        print("Warmup Rule Generation Complete!")
        print("=" * 80)
        
        print("\nRun Statistics:")
        print(f"  Total cases: {total}")
        print(f"  Correct verdicts: {self.stats['correct_verdicts']} ({verdict_acc:.1f}%)")
        print(f"  Incorrect verdicts: {self.stats['incorrect_verdicts']} ({100-verdict_acc:.1f}%)")
        print(f"  Correct reasoning: {self.stats['correct_reasoning']} ({reasoning_acc:.1f}%)")
        print(f"  Incorrect reasoning: {self.stats['incorrect_reasoning']} ({100-reasoning_acc:.1f}%)")
        
        print("\nRule Base Evolution:")
        # Get rule count by memory type
        detection_count = len([r for r in playbook.rules if r.active and r.memory_type == "detection"])
        trust_count = len([r for r in playbook.rules if r.active and r.memory_type == "trust"])
        
        print(f"  Initial version: v1.0 (0 rules)")
        print(f"  Final version: {playbook.version}")
        print(f"  - Detection rules: {detection_count}")
        print(f"  - Trust rules: {trust_count}")
        print(f"  - Total: {len(playbook.get_active_rules())} active rules")
        
        print("\nOutput Files:")
        print(f"  Case details: {self.current_run_dir}")
        print(f"  Run report: {self.current_run_dir / 'run_report.json'}")
        print(f"  Rule base: data/warmup_playbook/")
        
        print("\n" + "=" * 80 + "\n")
    
    def _save_run_report(self) -> None:
        """Save run report"""
        
        self.stats["end_time"] = datetime.now().isoformat()
        
        playbook = self.playbook_manager.load_playbook()
        
        report = {
            "run_id": self.current_run_id,
            "statistics": self.stats,
            "final_playbook_version": playbook.version,
            "final_rules_count": len(playbook.get_active_rules()),
            "detection_rules_count": len([r for r in playbook.rules if r.active and r.memory_type == "detection"]),
            "trust_rules_count": len([r for r in playbook.rules if r.active and r.memory_type == "trust"]),
        }
        
        report_file = self.current_run_dir / "run_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"Run report saved: {report_file}")


def main():
    """Main function"""
    
    print("\n" + "="*80)
    print("Warmup Supervised Rule Generation System")
    print("=" * 80)
    print("Using FeedbackAgent to simulate human feedback")
    print("Dataset: data/warmup.csv")
    print("Rule base: data/warmup_playbook/")
    print("=" * 80 + "\n")
    
    # Confirm to continue
    confirm = input("Start Warmup rule generation? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Cancelled")
        return
    
    # Initialize system
    try:
        system = WarmupFactCheckSystem()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("\nPlease ensure data/warmup.csv file exists")
        print("File format requirements:")
        print("  - First row is header: Statement,Rating,Full_Analysis")
        print("  - Statement: claim to verify")
        print("  - Rating: rating (True/False)")
        print("  - Full_Analysis: complete fact-check analysis")
        return
    except Exception as e:
        print(f"Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Run full dataset
    try:
        system.run_full_dataset()
    except KeyboardInterrupt:
        print("\n\nUser interrupted")
        print("Processed cases have been saved")
        system._print_final_summary()
        system._save_run_report()
    except Exception as e:
        print(f"\nError during execution: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
