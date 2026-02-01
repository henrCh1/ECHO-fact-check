"""Evaluation Metrics Calculator"""

from typing import Dict, List
from dataclasses import dataclass

@dataclass
class ConfusionMatrix:
    """Confusion Matrix"""
    TP: int = 0  # True Positive
    FN: int = 0  # False Negative
    Miss_T: int = 0  # Miss True (Actual True, Predicted Unverifiable)
    TN: int = 0  # True Negative
    FP: int = 0  # False Positive
    Miss_F: int = 0  # Miss False (Actual False, Predicted Unverifiable)
    
    @property
    def total(self) -> int:
        return self.TP + self.FN + self.Miss_T + self.TN + self.FP + self.Miss_F

@dataclass
class Metrics:
    """All Evaluation Metrics"""
    # Basic confusion matrix
    confusion_matrix: ConfusionMatrix
    
    # Core performance metrics
    global_accuracy: float
    coverage_rate: float
    accuracy_on_answered: float
    abstention_rate: float
    
    # Detailed classification metrics
    precision_true: float
    precision_false: float
    recall_true: float
    recall_false: float
    
    # Balanced metrics
    f1_true: float
    f1_false: float
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'confusion_matrix': {
                'TP': self.confusion_matrix.TP,
                'FN': self.confusion_matrix.FN,
                'Miss_T': self.confusion_matrix.Miss_T,
                'TN': self.confusion_matrix.TN,
                'FP': self.confusion_matrix.FP,
                'Miss_F': self.confusion_matrix.Miss_F,
                'Total': self.confusion_matrix.total
            },
            'core_metrics': {
                'global_accuracy': self.global_accuracy,
                'coverage_rate': self.coverage_rate,
                'accuracy_on_answered': self.accuracy_on_answered,
                'abstention_rate': self.abstention_rate
            },
            'classification_metrics': {
                'precision_true': self.precision_true,
                'precision_false': self.precision_false,
                'recall_true': self.recall_true,
                'recall_false': self.recall_false
            },
            'balanced_metrics': {
                'f1_true': self.f1_true,
                'f1_false': self.f1_false
            }
        }


class MetricsCalculator:
    """Evaluation Metrics Calculator"""
    
    @staticmethod
    def calculate_confusion_matrix(predictions: List[Dict]) -> ConfusionMatrix:
        """
        Calculate confusion matrix
        predictions: [{'ground_truth': 'True'/'False', 'prediction': 'True'/'False'/'Unverifiable'}, ...]
        """
        cm = ConfusionMatrix()
        
        for pred in predictions:
            gt = pred['ground_truth']
            pred_value = pred['prediction']
            
            if gt == 'True':
                if pred_value == 'True':
                    cm.TP += 1
                elif pred_value == 'False':
                    cm.FN += 1
                elif pred_value == 'Unverifiable':
                    cm.Miss_T += 1
            
            elif gt == 'False':
                if pred_value == 'False':
                    cm.TN += 1
                elif pred_value == 'True':
                    cm.FP += 1
                elif pred_value == 'Unverifiable':
                    cm.Miss_F += 1
        
        return cm
    
    @staticmethod
    def calculate_metrics(cm: ConfusionMatrix) -> Metrics:
        """Calculate all metrics from confusion matrix"""
        
        total = cm.total
        if total == 0:
            raise ValueError("Total samples is 0, cannot calculate metrics")
        
        # 1. Core performance metrics
        global_accuracy = (cm.TP + cm.TN) / total
        
        answered = cm.TP + cm.FP + cm.TN + cm.FN
        coverage_rate = answered / total if total > 0 else 0.0
        
        accuracy_on_answered = (cm.TP + cm.TN) / answered if answered > 0 else 0.0
        
        abstention_rate = (cm.Miss_T + cm.Miss_F) / total
        
        # 2. Detailed classification metrics
        # Precision - True
        precision_true = cm.TP / (cm.TP + cm.FP) if (cm.TP + cm.FP) > 0 else 0.0
        
        # Precision - False
        precision_false = cm.TN / (cm.TN + cm.FN) if (cm.TN + cm.FN) > 0 else 0.0
        
        # Recall - True
        recall_true = cm.TP / (cm.TP + cm.FN + cm.Miss_T) if (cm.TP + cm.FN + cm.Miss_T) > 0 else 0.0
        
        # Recall - False
        recall_false = cm.TN / (cm.TN + cm.FP + cm.Miss_F) if (cm.TN + cm.FP + cm.Miss_F) > 0 else 0.0
        
        # 3. Balanced metrics
        # F1 Score - True
        if precision_true + recall_true > 0:
            f1_true = 2 * (precision_true * recall_true) / (precision_true + recall_true)
        else:
            f1_true = 0.0
        
        # F1 Score - False
        if precision_false + recall_false > 0:
            f1_false = 2 * (precision_false * recall_false) / (precision_false + recall_false)
        else:
            f1_false = 0.0
        
        return Metrics(
            confusion_matrix=cm,
            global_accuracy=global_accuracy,
            coverage_rate=coverage_rate,
            accuracy_on_answered=accuracy_on_answered,
            abstention_rate=abstention_rate,
            precision_true=precision_true,
            precision_false=precision_false,
            recall_true=recall_true,
            recall_false=recall_false,
            f1_true=f1_true,
            f1_false=f1_false
        )
    
    @staticmethod
    def print_metrics(metrics: Metrics) -> None:
        """Format and print metrics"""
        cm = metrics.confusion_matrix
        
        print("\n" + "="*80)
        print("📊 Evaluation Metrics Report")
        print("="*80)
        
        # Confusion matrix
        print("\n0️⃣  Confusion Matrix:")
        print(f"   TP (True Positive):   {cm.TP:4d}  (Actual True, Predicted True)")
        print(f"   FN (False Negative):  {cm.FN:4d}  (Actual True, Predicted False)")
        print(f"   Miss_T:               {cm.Miss_T:4d}  (Actual True, Predicted Unverifiable)")
        print(f"   TN (True Negative):   {cm.TN:4d}  (Actual False, Predicted False)")
        print(f"   FP (False Positive):  {cm.FP:4d}  (Actual False, Predicted True)")
        print(f"   Miss_F:               {cm.Miss_F:4d}  (Actual False, Predicted Unverifiable)")
        print(f"   Total:                {cm.total:4d}")
        
        # Core performance metrics
        print("\n1️⃣  Core Performance Metrics:")
        print(f"   Global Accuracy:                     {metrics.global_accuracy:.2%}")
        print(f"   Coverage Rate:                       {metrics.coverage_rate:.2%}")
        print(f"   Accuracy on Answered:                {metrics.accuracy_on_answered:.2%}")
        print(f"   Abstention Rate:                     {metrics.abstention_rate:.2%}")
        
        # Detailed classification metrics
        print("\n2️⃣  Classification Metrics:")
        print(f"   Precision (True):                    {metrics.precision_true:.2%}")
        print(f"   Precision (False):                   {metrics.precision_false:.2%}")
        print(f"   Recall (True):                       {metrics.recall_true:.2%}")
        print(f"   Recall (False):                      {metrics.recall_false:.2%}")
        
        # Balanced metrics
        print("\n3️⃣  Balanced Metrics:")
        print(f"   F1 Score (True):                     {metrics.f1_true:.2%}")
        print(f"   F1 Score (False):                    {metrics.f1_false:.2%}")
        
        print("\n" + "="*80)