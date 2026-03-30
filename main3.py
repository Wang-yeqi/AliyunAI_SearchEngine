import os
import requests
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import re


class AliyunAISearchEngine:
    def __init__(self, api_key: Optional[str] = None):
        # 直接硬编码 API Key（请替换为你的实际 Key）
        self.api_key = api_key or os.environ.get("DASHSCOPE_API_KEY") or "sk-4ea60d3ea5d44edd961bdf3ac6e28ca9"
        if not self.api_key:
            raise ValueError("请设置DASHSCOPE_API_KEY环境变量或传入api_key")

        self.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"

    def _call_llm(self, messages: List[Dict], temperature: float = 0.3, max_tokens: int = 2000) -> Dict:
        """调用阿里云 LLM API 的通用方法"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "qwen-max",
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        try:
            response = requests.post(self.base_url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def fetch_webpage_text(self, url: str) -> str:
        """
        爬取网页并提取纯文本内容
        :param url: 目标网址
        :return: 提取的文本内容（如果失败返回空字符串）
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            # 自动检测编码
            if response.encoding is None:
                response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')

            # 移除脚本和样式标签
            for script in soup(["script", "style"]):
                script.decompose()

            # 获取文本并清理空白
            text = soup.get_text(separator='\n')
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)

            # 限制文本长度（避免超过模型上下文，这里限制约 3000 词）
            if len(text) > 12000:
                text = text[:12000] + "...(内容已截断)"
            return text
        except Exception as e:
            print(f"抓取网页失败: {e}")
            return ""

    def query_from_url(self, url: str, question: str) -> Dict[str, Any]:
        """
        针对指定 URL 的内容回答问题
        :param url: 网页地址
        :param question: 用户问题
        :return: 包含答案和出处的字典
        """
        # 1. 获取网页内容
        content = self.fetch_webpage_text(url)
        if not content:
            return {
                "query": question,
                "answer": "无法获取网页内容，请检查 URL 是否有效或网络连接。",
                "citations": [],
                "error": "fetch_failed"
            }

        # 2. 构建提示词，让模型基于内容回答
        system_prompt = (
            "你是一个智能助手。我会给你一段网页内容，请根据这段内容回答用户的问题。"
            "如果内容中没有相关答案，请直接回复'没有'。回答时要简洁、准确，"
            "并在末尾注明信息来源：原文出处为提供的 URL。"
        )
        user_prompt = f"网页内容如下：\n\n{content}\n\n用户问题：{question}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        # 3. 调用 LLM
        result = self._call_llm(messages)

        if "error" in result:
            return {
                "query": question,
                "answer": f"调用模型失败: {result['error']}",
                "citations": [],
                "error": result["error"]
            }

        answer = result['choices'][0]['message']['content']

        # 4. 检查是否包含“没有”字样（确保未找到时的规范输出）
        if "没有" not in answer and len(answer) > 0:
            # 有答案，添加来源
            answer = answer + f"\n\n（来源：{url}）"
        elif "没有" in answer:
            # 明确返回没有
            pass
        else:
            answer = "没有（未找到相关内容）"

        return {
            "query": question,
            "answer": answer,
            "citations": [{"url": url, "title": "目标网页", "snippet": content[:200]}],
            "usage": result.get('usage', {})
        }

    # 以下是原有的搜索方法（可选保留）
    def search(self, query: str, search_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """基于搜索引擎的通用搜索（保留原有功能）"""
        default_search = {"search_context_size": "high"}
        if search_config:
            default_search.update(search_config)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "qwen-max",
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个智能搜索助手。请根据搜索结果回答问题，并在回答中用[编号]标注引用来源。如果搜索结果中没有相关答案，请直接回答'没有'。"
                },
                {"role": "user", "content": query}
            ],
            "web_search_options": default_search,
            "temperature": 0.3,
            "max_tokens": 2000
        }
        try:
            response = requests.post(self.base_url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            result = response.json()
            answer = result['choices'][0]['message']['content']
            citations = self._extract_citations(result)

            if not citations and "没有" not in answer:
                answer = "没有（未找到相关答案）"

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
        """提取搜索引文（原有方法）"""
        citations = []
        message = result.get('choices', [{}])[0].get('message', {})
        if 'annotations' in message:
            for ann in message['annotations']:
                if 'web_search' in ann:
                    citations.append({
                        "title": ann.get('title', ''),
                        "url": ann.get('url', ''),
                        "snippet": ann.get('snippet', '')
                    })
        if not citations and 'web_search' in result:
            for item in result.get('web_search', []):
                citations.append({
                    "title": item.get('title', ''),
                    "url": item.get('url', ''),
                    "snippet": item.get('snippet', '')
                })
        return citations


# 使用示例
def main():
    # 创建实例（API Key 已在类中硬编码）
    engine = AliyunAISearchEngine()

    # 示例1：从指定网页内容回答问题
    url = "https://yunpan.plus/t/17963-1-1"
    question = "这篇文章的主要内容是什么？"
    result = engine.query_from_url(url, question)

    print(f"问题: {result['query']}")
    print(f"回答: {result['answer']}")
    print(f"引用: {result['citations']}")

    # 示例2：如果网页中没有答案，会返回“没有”
    # 假设问一个不存在的问题
    result2 = engine.query_from_url(url, "第二个项目名字是什么？")
    print(f"\n问题: {result2['query']}")
    print(f"回答: {result2['answer']}")


if __name__ == "__main__":
    main()