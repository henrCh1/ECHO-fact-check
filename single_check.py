"""单条信息核查工具 - Single Claim Verification Tool

使用现有的事实核查系统核查单条信息,无需运行完整的benchmark测试。
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

from agents.generator import GeneratorAgent
from utils.playbook_manager import PlaybookManager

# 加载环境变量
load_dotenv()


class SingleClaimChecker:
    """单条信息核查器"""
    
    def __init__(self):
        """初始化核查器"""
        # 使用现有的PlaybookManager和GeneratorAgent
        self.playbook_manager = PlaybookManager()
        self.generator = GeneratorAgent(playbook_manager=self.playbook_manager)
        
        # 创建输出目录
        self.output_dir = Path("data/single_checks")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def check_claim(self, claim_text: str, save_result: bool = True) -> dict:
        """
        核查单条信息
        
        Args:
            claim_text: 待核查的信息文本
            save_result: 是否保存结果到文件
            
        Returns:
            包含核查结果的字典
        """
        print(f"\n{'='*80}")
        print("单条信息核查系统")
        print(f"{'='*80}\n")
        print(f"待核查信息: {claim_text}\n")
        
        # 显示当前规则库状态
        playbook = self.playbook_manager.load_playbook()
        active_rules = playbook.get_active_rules()
        print(f"当前规则库: {playbook.version}, {len(active_rules)} 条活跃规则\n")
        
        # 执行核查
        print(f"{'='*80}")
        print("开始核查...")
        print(f"{'='*80}\n")
        
        verdict = self.generator.execute(claim_text)
        
        # 准备返回结果
        result = {
            'timestamp': datetime.now().isoformat(),
            'claim': claim_text,
            'verdict': verdict.verdict,
            'confidence': verdict.confidence,
            'reasoning': verdict.reasoning,
            'evidence_count': len(verdict.evidence),
            'used_rules': verdict.used_rules,
            'rule_match_quality': verdict.rule_match_quality,
            'playbook_version': playbook.version
        }
        
        # 保存结果
        if save_result:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            result_file = self.output_dir / f"check_{timestamp}.json"
            
            # 保存完整的verdict对象
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(verdict.model_dump(), f, ensure_ascii=False, indent=2, default=str)
            
            print(f"\n{'='*80}")
            print(f"✅ 核查结果已保存: {result_file}")
            print(f"{'='*80}\n")
        
        # 显示核查摘要
        self._print_summary(result)
        
        return result
    
    def _print_summary(self, result: dict):
        """打印核查结果摘要"""
        print(f"\n{'='*80}")
        print("核查结果摘要")
        print(f"{'='*80}\n")
        print(f"📋 待核查信息: {result['claim']}\n")
        print(f"⚖️  判定结果: {result['verdict']}")
        print(f"📊 置信度: {result['confidence']:.2%}\n")
        print(f"💡 推理过程:")
        print(f"   {result['reasoning']}\n")
        print(f"📚 使用的规则: {len(result['used_rules'])} 条")
        if result['used_rules']:
            for rule_id in result['used_rules']:
                print(f"   - {rule_id}")
        print(f"\n🔍 证据数量: {result['evidence_count']} 条")
        print(f"📖 规则库版本: {result['playbook_version']}")
        print(f"\n{'='*80}\n")


def main():
    """主函数 - 命令行接口"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="单条信息核查工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 交互式输入
  python single_check.py
  
  # 直接指定待核查信息
  python single_check.py --claim "利欧股份2026年1月跨境诉讼胜诉"
  
  # 不保存结果
  python single_check.py --claim "某条信息" --no-save
        """
    )
    
    parser.add_argument(
        '--claim',
        type=str,
        help='待核查的信息文本'
    )
    
    parser.add_argument(
        '--no-save',
        action='store_true',
        help='不保存核查结果到文件'
    )
    
    args = parser.parse_args()
    
    # 获取待核查信息
    if args.claim:
        claim_text = args.claim
    else:
        # 交互式输入
        print("\n" + "="*80)
        print("单条信息核查系统")
        print("="*80 + "\n")
        claim_text = input("请输入待核查的信息: ").strip()
        
        if not claim_text:
            print("❌ 错误: 未输入待核查信息")
            return
    
    # 初始化核查器
    try:
        checker = SingleClaimChecker()
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        print("\n请检查:")
        print("  1. .env 文件中的 GOOGLE_API_KEY 是否配置正确")
        print("  2. 网络连接是否正常")
        print("  3. 规则库文件是否存在 (data/playbook/)")
        return
    
    # 执行核查
    try:
        result = checker.check_claim(
            claim_text=claim_text,
            save_result=not args.no_save
        )
        
        print("✅ 核查完成!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
    except Exception as e:
        print(f"\n❌ 核查过程中出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
