import os
from pathlib import Path

from dotenv import load_dotenv

for env_path in (Path(__file__).resolve().parents[1] / ".env", Path(__file__).resolve().parents[2] / ".env"):
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=False)

from openai import OpenAI
import httpx

api_key = os.environ.get('DASHSCOPE_API_KEY') or os.environ.get('SILICONFLOW_API_KEY')
base_url = os.environ.get('LLM_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
model_name = os.environ.get('LLM_MODEL', 'Qwen/Qwen2.5-7B-Instruct')
if 'MiniMax' in model_name:
    model_name = 'Qwen/Qwen2.5-7B-Instruct'

print(f'Using Model: {model_name}, URL: {base_url}, API Key: {api_key[:5]}...')

try:
    client = OpenAI(api_key=api_key, base_url=base_url, http_client=httpx.Client(verify=False, timeout=60.0))
    resp = client.chat.completions.create(
        model=model_name, 
        messages=[{'role': 'user', 'content': 'hello'}],
        timeout=10.0
    )
    print('SUCCESS:', resp.choices[0].message.content)
except Exception as e:
    import traceback
    traceback.print_exc()
