"""Playbook Health Check and Auto-Fix Tool

This tool validates and automatically fixes common data errors in playbook JSON files.
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class PlaybookValidator:
    """Validator for Playbook JSON files with auto-fix capabilities"""
    
    VALID_TYPES = {"strategy", "tool_template", "pitfall"}
    VALID_MEMORIES = {"detection", "trust"}
    
    def __init__(self):
        self.issues: List[str] = []
        self.fixes: List[str] = []
    
    def validate_and_fix_file(self, filepath: Path, create_backup: bool = True) -> Dict:
        """
        Validate and auto-fix a playbook JSON file
        
        Args:
            filepath: Path to the JSON file
            create_backup: Whether to create a backup before fixing
            
        Returns:
            Dictionary with validation results
        """
        logger.info(f"🔍 Validating {filepath.name}...")
        
        # Load JSON
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse JSON: {e}")
            return {'success': False, 'error': str(e)}
        
        # Reset counters
        self.issues = []
        self.fixes = []
        
        # Validate and fix rules
        if 'rules' in data:
            for i, rule in enumerate(data['rules']):
                self._validate_and_fix_rule(rule, i)
        
        # Save if fixes were made
        if self.fixes:
            if create_backup:
                backup_path = filepath.with_suffix('.json.bak')
                filepath.rename(backup_path)
                logger.info(f"📦 Backup created: {backup_path.name}")
            
            # Write fixed data
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Fixed {len(self.fixes)} issues in {filepath.name}")
            for fix in self.fixes:
                logger.info(f"   • {fix}")
        else:
            logger.info(f"✅ No issues found in {filepath.name}")
        
        return {
            'success': True,
            'issues_found': len(self.issues),
            'fixes_applied': len(self.fixes),
            'issues': self.issues,
            'fixes': self.fixes
        }
    
    def _validate_and_fix_rule(self, rule: dict, index: int) -> None:
        """Validate and fix a single rule"""
        rule_id = rule.get('rule_id', f'rule_{index}')
        
        # Fix evidence_count
        if 'evidence_count' in rule:
            ec = rule['evidence_count']
            if isinstance(ec, str):
                self.issues.append(f"Rule {rule_id}: evidence_count is string '{ec}'")
                try:
                    rule['evidence_count'] = int(ec)
                    self.fixes.append(f"Rule {rule_id}: Converted evidence_count to int")
                except ValueError:
                    rule['evidence_count'] = 1
                    self.fixes.append(f"Rule {rule_id}: Reset invalid evidence_count to 1")
            elif not isinstance(ec, int):
                self.issues.append(f"Rule {rule_id}: evidence_count is {type(ec).__name__}")
                rule['evidence_count'] = 1
                self.fixes.append(f"Rule {rule_id}: Reset evidence_count to 1")
        
        # Fix type
        if 'type' in rule:
            rule_type = rule['type']
            if rule_type not in self.VALID_TYPES:
                self.issues.append(f"Rule {rule_id}: Invalid type '{rule_type}'")
                rule['type'] = 'strategy'
                self.fixes.append(f"Rule {rule_id}: Changed type to 'strategy'")
        
        # Fix confidence
        if 'confidence' in rule:
            conf = rule['confidence']
            try:
                conf_float = float(conf)
                if conf_float < 0.0:
                    self.issues.append(f"Rule {rule_id}: confidence {conf_float} < 0.0")
                    rule['confidence'] = 0.0
                    self.fixes.append(f"Rule {rule_id}: Clamped confidence to 0.0")
                elif conf_float > 1.0:
                    self.issues.append(f"Rule {rule_id}: confidence {conf_float} > 1.0")
                    rule['confidence'] = 1.0
                    self.fixes.append(f"Rule {rule_id}: Clamped confidence to 1.0")
            except (ValueError, TypeError):
                self.issues.append(f"Rule {rule_id}: Invalid confidence '{conf}'")
                rule['confidence'] = 0.5
                self.fixes.append(f"Rule {rule_id}: Reset confidence to 0.5")
        
        # Fix memory_type
        if 'memory_type' in rule:
            mem_type = rule['memory_type']
            if mem_type and mem_type not in self.VALID_MEMORIES:
                self.issues.append(f"Rule {rule_id}: Invalid memory_type '{mem_type}'")
                rule['memory_type'] = 'detection'
                self.fixes.append(f"Rule {rule_id}: Changed memory_type to 'detection'")


def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate and fix playbook JSON files')
    parser.add_argument('files', nargs='+', type=Path, help='JSON files to validate')
    parser.add_argument('--no-backup', action='store_true', help='Do not create backup files')
    
    args = parser.parse_args()
    
    validator = PlaybookValidator()
    total_issues = 0
    total_fixes = 0
    
    for filepath in args.files:
        if not filepath.exists():
            logger.error(f"❌ File not found: {filepath}")
            continue
        
        result = validator.validate_and_fix_file(filepath, create_backup=not args.no_backup)
        if result['success']:
            total_issues += result['issues_found']
            total_fixes += result['fixes_applied']
    
    print(f"\n{'='*60}")
    print(f"📊 Summary: Found {total_issues} issues, applied {total_fixes} fixes")
    print(f"{'='*60}")


if __name__ == '__main__':
    # Quick test mode if no args
    import sys
    if len(sys.argv) == 1:
        print("🔧 Running in test mode on default playbook files...")
        base_path = Path(__file__).parent.parent / 'data' / 'playbook'
        validator = PlaybookValidator()
        
        for filename in ['detection_memory.json', 'trust_memory.json']:
            filepath = base_path / filename
            if filepath.exists():
                validator.validate_and_fix_file(filepath)
    else:
        main()
