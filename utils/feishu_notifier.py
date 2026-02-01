"""Feishu Webhook Notifier for Benchmark Progress Updates"""

import requests
import json
from datetime import datetime


class FeishuNotifier:
    """Send progress notifications to Feishu via webhook"""
    
    def __init__(self, webhook_url: str):
        """
        Initialize Feishu notifier
        
        Args:
            webhook_url: Feishu webhook URL
        """
        self.webhook_url = webhook_url
    
    def send_progress(self, current_case: int, total_cases: int, accuracy: str, 
                     rule_base_info: str, verdict: str, confidence: float, 
                     processing_time: str, full_terminal_output: str) -> None:
        """
        Send progress notification to Feishu
        
        Args:
            current_case: Current case number
            total_cases: Total number of cases
            accuracy: Cumulative accuracy percentage
            rule_base_info: Rule base information
            verdict: Latest verdict result
            confidence: Verdict confidence score
            processing_time: Total processing time
            full_terminal_output: Complete terminal output text
        """
        progress_percent = (current_case / total_cases) * 100
        
        # Build plain text message (no emoji)
        message = f"""Benchmark Progress Update [{current_case}/{total_cases}]
========================================

Progress: {progress_percent:.1f}%
Cumulative Accuracy: {accuracy}%
Latest Verdict: {verdict} (Confidence: {confidence})
Rule Base: {rule_base_info}
Processing Time: {processing_time}
Update Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

========================================
FULL TERMINAL OUTPUT
========================================

{full_terminal_output}

========================================
END OF OUTPUT
========================================
"""
        
        # Build payload following Feishu webhook format
        payload = {
            "msg_type": "text",
            "content": {
                "text": message
            }
        }
        
        try:
            response = requests.post(
                self.webhook_url,
                headers={"Content-Type": "application/json"},
                data=json.dumps(payload),
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"[OK] Progress sent to Feishu ({current_case}/{total_cases})")
            else:
                print(f"[WARNING] Feishu notification failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"[ERROR] Feishu notification exception: {str(e)}")
