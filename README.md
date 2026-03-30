
# AliyunAI_SearchEngine
本项目是基于阿里云Qwen-Max大模型API封装的智能搜索引擎工具，支持自定义搜索配置、多维度结果解析与鲁棒异常处理。通过简洁的Python接口实现高质量网络搜索，适用于问答系统、研究辅助、数据挖掘等场景。

## 功能特性
- 集成阿里云大模型（默认 qwen-max）与实时搜索能力
- 自动提取搜索结果中的引用来源（标题、URL、摘要）
- 支持自定义搜索范围（时间、行业、结果数量等）
- 简洁的API接口，返回结构化结果（答案+引用+用量统计）

## 安装依赖
```bash
pip install requests
```

## API Key设置
### 获取方式
阿里云 DashScope API Key 需通过[阿里云控制台](https://dashscope.console.aliyun.com/)开通"智能搜索"服务后获取

### 两种配置方式
1. **环境变量配置（推荐）**  
   ```bash
   export DASHSCOPE_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"  # Linux/Mac
   set DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx      # Windows
   ```

2. **代码中直接传入**  
   ```python
   from aliyun_search import AliyunAISearchEngine
   engine = AliyunAISearchEngine(api_key="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
   ```

### 验证配置
```python
engine = AliyunAISearchEngine()
print(engine.api_key)  # 应输出配置的API Key
```

## 使用方法
### 基本搜索
```python
from aliyun_search import AliyunAISearchEngine

engine = AliyunAISearchEngine()
result = engine.search("什么是人工智能？")
print(result["answer"])
print("引用来源:", result["citations"])
```

### 高级搜索配置
```python
result = engine.search_with_custom_settings(
    query="2024年诺贝尔物理学奖",
    time_range="1y",   # 时间范围: 1d/1w/1m/1y/none
    industry="科学",   # 可选行业限定
    top_k=10           # 结果数量（1-10），大于5时自动启用高精度搜索
)
```

### 自定义搜索参数
```python
search_config = {
    "search_context_size": "high",  # low/medium/high
    "search_time_range": "1w",      # 可选
    "search_industry": "金融"       # 可选
}
result = engine.search("最新股票市场动态", search_config)
```

## API文档
### AliyunAISearchEngine(api_key=None)
**参数**  
- `api_key` (str, optional): DashScope API Key，若未提供则从环境变量 `DASHSCOPE_API_KEY` 读取

### search(query, search_config=None)
执行一次搜索问答  
**参数**  
- `query` (str): 用户问题  
- `search_config` (dict, optional): 搜索配置，可覆盖默认值  
  - `search_context_size` (str): "low", "medium", "high"，控制搜索上下文规模  
  - `search_time_range` (str): 时间范围，如 "1d", "1w", "1m", "1y", "none"  
  - `search_industry` (str): 行业限定，如 "金融", "法律", "医疗", "互联网"  

**返回值**  
```json
{
  "query": "原始问题",
  "answer": "模型生成的回答（包含引用编号）",
  "citations": [
    {"title": "标题", "url": "链接", "snippet": "摘要"}
  ],
  "usage": {"total_tokens": 1234, "prompt_tokens": 500, "completion_tokens": 734},
  "error": "发生错误时的错误信息（仅当失败时存在）"
}
```

### search_with_custom_settings(query, time_range="1w", industry=None, top_k=10)
便捷方法，自动构建搜索配置  
**参数**  
- `query` (str): 用户问题  
- `time_range` (str): 时间范围（默认 "1w"）  
- `industry` (str, optional): 行业限定  
- `top_k` (int): 返回结果数量（1-10），>5时自动设置`search_context_size="high"`  

**返回值**：同 `search()` 方法

## 示例输出
```json
{
  "query": "洛克王国是什么",
  "answer": "洛克王国是腾讯旗下的一款儿童在线游戏...[1]...游戏玩法...[2]...",
  "citations": [
    {"title": "洛克王国官方网站", "url": "https://roco.qq.com/", "snippet": "..."},
    {"title": "百度百科：洛克王国", "url": "https://baike.baidu.com/...", "snippet": "..."}
  ],
  "usage": {"total_tokens": 1234, "prompt_tokens": 500, "completion_tokens": 734}
}
```

## 注意事项
1. **API Key安全**：建议通过环境变量配置，避免在代码中硬编码密钥
2. **服务开通**：需在阿里云控制台开通"智能搜索"服务并获取有效API Key
3. **接口兼容性**：使用兼容模式API端点 `https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions`，与OpenAI接口格式兼容
4. **模型选择**：默认使用`qwen-max`，可在`search`方法中修改`model`参数切换其他模型（如`qwen-plus`、`qwen-turbo`）
5. **超时设置**：默认超时60秒，可根据网络情况在初始化时调整`timeout`参数
