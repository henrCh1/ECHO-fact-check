from langchain_core.tools import tool
from typing import List, Dict
import os
import json

# 尝试导入搜索库
try:
    from serpapi import GoogleSearch
    SERPAPI_AVAILABLE = True
except ImportError:
    SERPAPI_AVAILABLE = False

try:
    from googleapiclient.discovery import build
    GOOGLE_SEARCH_AVAILABLE = True
except ImportError:
    GOOGLE_SEARCH_AVAILABLE = False

@tool
def search_web(query: str, num_results: int = 5) -> str:
    """
    网络搜索工具：用于事实核查
    
    Args:
        query: 搜索查询词
        num_results: 返回结果数量
    
    Returns:
        搜索结果的JSON字符串，包含title, link, snippet
    """
    
    # 尝试使用SerpAPI
    if SERPAPI_AVAILABLE and os.getenv("SERPAPI_KEY"):
        try:
            params = {
                "q": query,
                "api_key": os.getenv("SERPAPI_KEY"),
                "num": num_results,
                "engine": "google"
            }
            search = GoogleSearch(params)
            results = search.get_dict()
            
            organic_results = results.get("organic_results", [])
            formatted_results = [
                {
                    "title": r.get("title", ""),
                    "link": r.get("link", ""),
                    "snippet": r.get("snippet", "")
                }
                for r in organic_results[:num_results]
            ]
            return json.dumps(formatted_results, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"SerpAPI搜索失败: {e}")
    
    # 尝试使用Google Custom Search
    if GOOGLE_SEARCH_AVAILABLE and os.getenv("GOOGLE_SEARCH_API_KEY") and os.getenv("GOOGLE_CSE_ID"):
        try:
            service = build("customsearch", "v1", developerKey=os.getenv("GOOGLE_SEARCH_API_KEY"))
            result = service.cse().list(
                q=query,
                cx=os.getenv("GOOGLE_CSE_ID"),
                num=num_results
            ).execute()
            
            items = result.get("items", [])
            formatted_results = [
                {
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", "")
                }
                for item in items
            ]
            return json.dumps(formatted_results, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Google Search失败: {e}")
    
    # 模拟搜索（demo用）
    print(f"[模拟搜索] 查询: {query}")
    mock_results = [
        {
            "title": f"权威来源关于{query}的报道",
            "link": "https://example.com/news/article1",
            "snippet": f"根据官方消息，关于'{query}'的最新信息显示..."
        },
        {
            "title": f"{query} - 官方声明",
            "link": "https://official.gov/statement",
            "snippet": f"官方机构就'{query}'发布了正式声明，澄清相关情况..."
        },
        {
            "title": f"专家分析：{query}的真相",
            "link": "https://expert-analysis.com/truth",
            "snippet": f"专业分析师对'{query}'进行了深入调查，发现..."
        }
    ]
    return json.dumps(mock_results[:num_results], ensure_ascii=False, indent=2)


# 为LangChain Agent准备工具列表
search_tools = [search_web]
