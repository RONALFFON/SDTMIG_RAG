# SDTMIG_RAG

## 后端 API 集成测试
- 测试位置：`tests/test_query_api.py`
- 运行命令：

```bash
python -m unittest discover -s tests -v
```

- 说明：
  - 该测试使用 Flask `test_client` 和 stub，不依赖真实 Milvus 与真实 LLM 外部调用。
  - 主要覆盖 `/api/vector/query` 的参数校验、降级成功分支、异常失败分支。

