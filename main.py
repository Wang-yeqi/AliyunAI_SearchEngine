import os
import requests
from typing import List, Dict, Any, Optional


class AliyunAISearchEngine:
    def __init__(self, api_key: Optional[str] = None):

        self.api_key = api_key or os.environ.get("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("请设置DASHSCOPE_API_KEY环境变量或传入api_key")

        self.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"

    def search(self, query: str, search_config: Dict[str, Any] = None) -> Dict[str, Any]:

        # 默认搜索配置
        web_search = {
            "search_context_size": "high",  # low/medium/high
        }
        if search_config:
            web_search.update(search_config)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "qwen-max",  # 可以换其他模型
            "messages": [
                {
                    "role": "system",
                    #"content": "你是一个智能搜索助手。请根据搜索结果回答问题，并在回答中用[编号]标注引用来源。"
                    "content": "你是一个智能搜索助手。请根据搜索结果回答问题，并尽可能多地引用不同的来源，每个引用使用[编号]标注。至少引用5个来源，如果搜索结果充足，引用数量越多越好。"
                },
                {
                    "role": "user",
                    "content": query
                }
            ],
            "web_search_options": web_search,
            "temperature": 0.3,
            "max_tokens": 2000
        }

        try:
            response = requests.post(self.base_url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            result = response.json()

            # 解析响应
            answer = result['choices'][0]['message']['content']

            # 提取引用（阿里云API返回的citation信息）
            citations = self._extract_citations(result)

            return {
                "query": query,
                "answer": answer,
                "citations": citations,
                "usage": result.get('usage', {})
            }

        except Exception as e:
            return {
                "query": query,
                "answer": f"搜索失败: {str(e)}",
                "citations": [],
                "error": str(e)
            }

    def _extract_citations(self, result: Dict) -> List[Dict]:
        """从API响应中提取引用信息"""
        citations = []
        # 阿里云API返回的引用在 message 的 annotations 或 web_search 结果中
        message = result.get('choices', [{}])[0].get('message', {})

        # 尝试获取搜索引用的原始数据
        if 'annotations' in message:
            for ann in message['annotations']:
                if 'web_search' in ann:
                    citations.append({
                        "title": ann.get('title', ''),
                        "url": ann.get('url', ''),
                        "snippet": ann.get('snippet', '')
                    })

        # 如果没有单独返回，从搜索结果中提取
        if not citations and 'web_search' in result:
            for item in result.get('web_search', []):
                citations.append({
                    "title": item.get('title', ''),
                    "url": item.get('url', ''),
                    "snippet": item.get('snippet', '')
                })

        return citations

    def search_with_custom_settings(self, query: str,
                                    time_range: str = "1w",  # 1d/1w/1m/1y/none
                                    industry: str = None,  # 金融/法律/医疗/互联网
                                    top_k: int = 10) -> Dict:
        """
        使用高级搜索配置
        :param time_range: 时间范围
        :param industry: 行业限定
        :param top_k: 返回结果数量（1-10）
        """
        search_config = {
            "search_context_size": "high" if top_k > 5 else "medium",
            "search_time_range": time_range,
        }
        if industry:
            search_config["search_industry"] = industry

        return self.search(query, search_config)


# 使用示例
def main():
    engine = AliyunAISearchEngine(api_key="sk-4ea60d3ea5d44edd961bdf3ac6e28ca9")

    # 使用高级配置，top_k=10 自动启用 high 搜索
    result = engine.search_with_custom_settings(
        query="洛克王国是什么",
        top_k=10,
        time_range="1y"
    )

    print(f"问题: {result['query']}")
    print(f"回答: {result['answer']}")
    print(f"引用数: {len(result['citations'])}")
    if result.get('usage'):
        print(f"Token消耗: {result['usage']}")


if __name__ == "__main__":
    main()
