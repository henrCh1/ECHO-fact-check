"""AgentA: Fact-Checker Generator - Multi-Agent Collaboration Version

Splits the verification workflow into three specialized Agents:
1. Planner: Extract claims, select rules, generate search queries
2. Investigator: Execute searches, collect evidence
3. Judge: Synthesize information, make final judgment
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from google import genai
from google.genai import types
import json
from datetime import datetime
from typing import List, Dict, Any

from schemas.verdict import Verdict, Evidence, ProcessTrace
from utils.playbook_manager import PlaybookManager
from prompts.generator_prompt import PLANNER_PROMPT, INVESTIGATOR_PROMPT, JUDGE_PROMPT, GENERATOR_PROMPT
from config.settings import Settings


class GeneratorAgent:
    """AgentA: Fact-Checker Generator - Multi-Agent Collaboration Version"""
    
    def __init__(self, playbook_manager: PlaybookManager = None):
        # LLM for Planner and Judge
        self.llm = ChatGoogleGenerativeAI(
            model=Settings.GEMINI_MODEL,
            # temperature=Settings.TEMPERATURE,  # Commented out to use model's default
            max_output_tokens=Settings.MAX_TOKENS,
            google_api_key=Settings.GOOGLE_API_KEY
        )
        self.playbook_manager = playbook_manager if playbook_manager else PlaybookManager()
        
        # Official genai client for Investigator with Google Search
        self.genai_client = genai.Client(api_key=Settings.GOOGLE_API_KEY)
        self.grounding_tool = types.Tool(google_search=types.GoogleSearch())
    
    def execute(self, claim_text: str) -> Verdict:
        """Execute fact-checking (Multi-Agent Collaboration Version)"""
        
        print(f"\n{'='*60}")
        print("🚀 AgentA Starting Multi-Agent Collaboration Verification")
        print(f"{'='*60}\n")
        
        try:
            # ========================================
            # Phase 1: Planner - Plan Verification Strategy
            # ========================================
            print("📋 [1/3] Planner is analyzing...")
            planner_output = self._run_planner(claim_text)
            print(f"   ✓ Extracted {len(planner_output.get('extracted_claims', []))} claims")
            print(f"   ✓ Selected {len(planner_output.get('selected_rules', []))} rules")
            print(f"   ✓ Generated {len(planner_output.get('search_queries', []))} search queries")
            
            # ========================================
            # Phase 2: Investigator - Collect Evidence
            # ========================================
            print("\n🔍 [2/3] Investigator is searching for evidence...")
            investigator_output = self._run_investigator(planner_output.get('search_queries', []))
            print(f"   ✓ Collected {len(investigator_output.get('evidence_items', []))} evidence items")
            
            # ========================================
            # Phase 3: Judge - Synthesize and Judge
            # ========================================
            print("\n⚖️ [3/3] Judge is making judgment...")
            verdict = self._run_judge(claim_text, planner_output, investigator_output)
            
            print(f"\n{'='*60}")
            print("✅ AgentA Verification Complete")
            print(f"{'='*60}")
            print(verdict.to_display())
            
            return verdict
            
        except Exception as e:
            print(f"\n❌ Multi-Agent collaboration failed: {e}")
            print("📌 Falling back to single-Agent mode...")
            return self._fallback_execute(claim_text)
    
    def _run_planner(self, claim_text: str) -> Dict[str, Any]:
        """Phase 1: Planner - Analyze claims, select rules, generate search queries"""
        
        # Load only brief rule summary to reduce token usage
        rules_summary = self.playbook_manager.get_rules_brief_summary()
        
        prompt = PLANNER_PROMPT.format(
            rules_summary=rules_summary,
            input=claim_text
        )
        
        response = self.llm.invoke(prompt)
        content = response.content
        
        # Parse JSON
        try:
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
            else:
                json_str = content.strip()
            
            planner_output = json.loads(json_str)
            return planner_output
            
        except json.JSONDecodeError as e:
            print(f"   ⚠️ Planner JSON parsing failed: {e}")
            # Return basic output
            return {
                "extracted_claims": [claim_text],
                "selected_rules": [],
                "search_queries": [claim_text],
                "analysis_notes": f"JSON parsing failed, using original input as query"
            }
    
    def _run_investigator(self, search_queries: List[str]) -> Dict[str, Any]:
        """Phase 2: Investigator - Use official genai client with Google Search"""
        
        evidence_items = []
        raw_responses = []
        
        for query in search_queries[:3]:  # Execute at most 3 queries
            try:
                # Use official genai client with google_search tool
                search_prompt = INVESTIGATOR_PROMPT.format(search_query=query)
                
                config = types.GenerateContentConfig(
                    tools=[self.grounding_tool]
                )
                
                response = self.genai_client.models.generate_content(
                    model=Settings.GEMINI_MODEL,
                    contents=search_prompt,
                    config=config
                )
                
                # Store raw response for debugging
                raw_responses.append({
                    "query": query,
                    "text": response.text,
                    "has_grounding": hasattr(response.candidates[0], 'grounding_metadata') if response.candidates else False
                })
                
                # Parse search results
                evidence = self._parse_search_response(response, query)
                evidence_items.extend(evidence)
                
            except Exception as e:
                print(f"   ⚠️ Search query '{query[:30]}...' failed: {e}")
                continue
        
        return {
            "evidence_items": evidence_items,
            "raw_search_responses": raw_responses,
            "queries_executed": len(search_queries[:3])
        }
    
    def _parse_search_response(self, response, query: str) -> List[Dict]:
        """Parse official genai SDK response, extract grounding metadata"""
        
        evidence_items = []
        
        try:
            if not response.candidates:
                return evidence_items
            
            candidate = response.candidates[0]
            
            # Extract main text response
            if response.text:
                evidence_items.append({
                    "source": "Google Search - AI Summary",
                    "content": response.text[:500] if len(response.text) > 500 else response.text,
                    "credibility": "high",
                    "query": query
                })
            
            # Extract grounding metadata (official structure)
            if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                grounding = candidate.grounding_metadata
                
                # Extract web search queries used
                if hasattr(grounding, 'web_search_queries') and grounding.web_search_queries:
                    queries_used = ", ".join(grounding.web_search_queries)
                    print(f"   ℹ️ Web search queries: {queries_used}")
                
                # Extract grounding chunks (web sources)
                if hasattr(grounding, 'grounding_chunks') and grounding.grounding_chunks:
                    for chunk in grounding.grounding_chunks[:5]:  # Take at most 5 sources
                        if hasattr(chunk, 'web') and chunk.web:
                            evidence_items.append({
                                "source": chunk.web.uri if hasattr(chunk.web, 'uri') else "Unknown",
                                "content": chunk.web.title if hasattr(chunk.web, 'title') else "",
                                "credibility": "high",
                                "query": query
                            })
                
                # Extract grounding supports (text segments with citations)
                if hasattr(grounding, 'grounding_supports') and grounding.grounding_supports:
                    for support in grounding.grounding_supports[:3]:  # Take at most 3 supports
                        if hasattr(support, 'segment') and support.segment:
                            segment_text = support.segment.text if hasattr(support.segment, 'text') else ""
                            if segment_text:
                                # Get citation indices
                                chunk_indices = support.grounding_chunk_indices if hasattr(support, 'grounding_chunk_indices') else []
                                evidence_items.append({
                                    "source": f"Cited Segment (chunks: {chunk_indices})",
                                    "content": segment_text[:300],
                                    "credibility": "high",
                                    "query": query
                                })
                         
        except Exception as e:
            print(f"   ⚠️ Failed to parse search response: {e}")
        
        return evidence_items
    
    def _run_judge(self, original_input: str, planner_output: Dict, investigator_output: Dict) -> Verdict:
        """Phase 3: Judge - Synthesize all information and make final judgment"""
        
        # Build evidence summary
        evidence_items = investigator_output.get("evidence_items", [])
        evidence_summary = ""
        for i, item in enumerate(evidence_items, 1):
            evidence_summary += f"\n{i}. [{item.get('credibility', 'medium')}] {item.get('source', 'Unknown')}\n"
            evidence_summary += f"   Content: {item.get('content', 'N/A')[:200]}...\n"
        
        if not evidence_summary:
            evidence_summary = "No relevant evidence found"
        
        # Load full details of selected rules (FIX: Judge now can actually use rules!)
        selected_rule_ids = planner_output.get("selected_rules", [])
        selected_rules_detail = self.playbook_manager.get_rules_by_ids(selected_rule_ids)
        
        prompt = JUDGE_PROMPT.format(
            original_input=original_input,
            extracted_claims=json.dumps(planner_output.get("extracted_claims", []), ensure_ascii=False),
            selected_rules=selected_rules_detail,  # Now passing full rule details, not just IDs
            evidence_summary=evidence_summary
        )
        
        response = self.llm.invoke(prompt)
        content = response.content
        
        # Parse JSON
        try:
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
            else:
                json_str = content.strip()
            
            verdict_data = json.loads(json_str)
            
            # Ensure case_id exists
            if not verdict_data.get("case_id"):
                verdict_data["case_id"] = f"case_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Create ProcessTrace
            process_trace = ProcessTrace(
                planner_output=planner_output,
                investigator_output=investigator_output,
                judge_reasoning=verdict_data.get("reasoning", "")
            )
            
            # Add process_trace to verdict_data
            verdict_data["process_trace"] = process_trace
            
            # Create Verdict object
            verdict = Verdict(**verdict_data)
            return verdict
            
        except json.JSONDecodeError as e:
            print(f"   ⚠️ Judge JSON parsing failed: {e}")
            print(f"   Raw output: {content[:500]}...")
            
            # Create default Verdict
            process_trace = ProcessTrace(
                planner_output=planner_output,
                investigator_output=investigator_output,
                judge_reasoning=f"JSON parsing failed: {str(e)}"
            )
            
            return Verdict(
                case_id=f"case_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                claim=original_input,
                verdict="Unverifiable",
                confidence=0.0,
                reasoning=f"Judge output parsing failed: {str(e)}",
                evidence=[],
                used_rules=[],
                rule_match_quality="none",
                process_trace=process_trace
            )
    
    def _fallback_execute(self, claim_text: str) -> Verdict:
        """Fallback to original single-Agent mode"""
        
        # Also use brief summary in fallback mode to reduce token usage
        rules_summary = self.playbook_manager.get_rules_brief_summary()
        
        prompt_text = GENERATOR_PROMPT.format(
            rules_summary=rules_summary,
            input=claim_text
        )
        
        print("AgentA (Single-Agent Mode) is analyzing...")
        response = self.llm.invoke(prompt_text)
        
        try:
            content = response.content
            
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
            else:
                json_str = content.strip()
            
            verdict_data = json.loads(json_str)
            
            if not verdict_data.get("case_id"):
                verdict_data["case_id"] = f"case_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            verdict = Verdict(**verdict_data)
            
            print(f"\n{'='*60}")
            print("AgentA (Single-Agent Mode) Verification Complete")
            print(f"{'='*60}")
            print(verdict.to_display())
            
            return verdict
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing failed: {e}")
            
            return Verdict(
                case_id=f"case_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                claim=claim_text,
                verdict="Unverifiable",
                confidence=0.0,
                reasoning=f"Parsing failed: {str(e)}",
                evidence=[],
                used_rules=[],
                rule_match_quality="none"
            )
        except Exception as e:
            print(f"Other error: {e}")
            raise
