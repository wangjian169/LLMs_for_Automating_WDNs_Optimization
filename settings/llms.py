import os

V3 = "deepseek-chat"
R1 = "deepseek-reasoner"

config_list = [
    {
        "model": V3,
        "base_url": "https://api.deepseek.com/v1",
        "api_key": os.environ.get("OPENAI_API_KEY"),
        "max_tokens": 2048,
    }
]

llm_config = {
    "seed": 10,
    "temperature": 0,
    "config_list": config_list,
    "timeout": 600,
    "cache_seed": None
}