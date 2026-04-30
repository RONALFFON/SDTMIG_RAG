"""
向量检索器模块
基于向量数据库实现智能问答和内容检索
"""


import logging
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# LangChain imports
from langchain_core.documents import Document


# 本地模块
try:
    # 包模式启动（python -m）
    from .vector_db_manager import VectorDatabaseManager
except Exception:
    # 脚本模式启动（python server.py）
    from vector_db_manager import VectorDatabaseManager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """检索结果数据类"""
    content: str
    score: float
    metadata: Dict[str, Any]
    source: str
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "content": self.content,
            "score": self.score,
            "metadata": self.metadata,
            "source": self.source
        }


@dataclass
class AnswerResult:
    """问答结果数据类"""
    answer: str
    confidence: float
    question_type: str
    source_documents: List[Document]
    scores: List[float]
    degraded: bool = False
    warning: str = ""
    error_code: str = ""


class VectorRetriever:
    """向量检索器"""
    
    def __init__(self, 
                 db_manager: VectorDatabaseManager,
                 similarity_threshold: float = 0.5, # 适当调整阈值
                 max_results: int = 10):
        """
        初始化向量检索器
        
        Args:
            db_manager: 向量数据库管理器
            similarity_threshold: 相似度阈值
            max_results: 最大返回结果数
        """
        self.db_manager = db_manager
        self.similarity_threshold = similarity_threshold
        self.max_results = max_results
    
    def search_similar_content(self,
                             query: str,
                             collection_name: str,
                             k: int = None,
                             filter_expression: str = None,
                             include_scores: bool = True) -> List[Tuple[Document, float]]:
        """
        搜索相似内容
        
        Args:
            query: 查询文本
            collection_name: Milvus 集合名称
            k: 返回结果数量
            filter_expression: Milvus 过滤表达式
            include_scores: 是否包含相似度分数
            
        Returns:
            检索结果列表 (文档, 分数)
        """
        if k is None:
            k = self.max_results
        
        try:
            # 执行向量搜索
            search_results = self.db_manager.search(query=query, k=k, collection_name=collection_name)
            
            # 过滤低相似度结果
            results = []
            for doc, score in search_results:
                if score >= self.similarity_threshold:
                    results.append((doc, score))
            
            logger.info(f"在集合 '{collection_name}' 中检索查询: '{query}', 返回 {len(results)} 个高质量结果")
            return results
            
        except Exception as e:
            logger.error(f"在集合 '{collection_name}' 中检索失败: {e}")
            return []
    
    def answer_question(self, 
                        question: str, 
                        collection_name: str, 
                        k: int = 5) -> AnswerResult:
        """
        回答问题
        
        Args:
            question: 问题文本
            collection_name: Milvus 集合名称
            k: 上下文文档数量
            
        Returns:
            回答结果
        """
        try:
            # 1. 分类问题
            question_type = QuestionClassifier.classify_question(question)
            
            # 2. 检索相关文档
            relevant_docs_with_scores = self.search_similar_content(
                query=question,
                collection_name=collection_name,
                k=k
            )
            
            # 3. 构建上下文 (即使为空也构建空上下文)
            context_parts = []
            source_documents = []
            scores = []
            
            if relevant_docs_with_scores:
                for i, (doc, score) in enumerate(relevant_docs_with_scores):
                    context_parts.append(f"参考资料{i+1}: {doc.page_content}")
                    source_documents.append(doc)
                    scores.append(score)
            
            context = "\n\n".join(context_parts)
            
            # 4. 生成回答 (使用 LLM)
            llm_result = self._generate_answer_with_llm(question, context)
            
            # 5. 计算置信度
            confidence = self._calculate_confidence(scores)
            
            return AnswerResult(
                answer=llm_result["answer"],
                confidence=confidence,
                question_type=question_type,
                source_documents=source_documents,
                scores=scores,
                degraded=llm_result["degraded"],
                warning=llm_result["warning"],
                error_code=llm_result["error_code"]
            )
            
        except Exception as e:
            logger.error(f"回答问题失败: {e}")
            return AnswerResult(
                answer=f"处理问题时出现错误: {str(e)}",
                confidence=0.0,
                question_type="错误",
                source_documents=[],
                scores=[]
            )
    
    def _generate_answer_with_llm(self, question: str, context: str) -> Dict[str, Any]:
        """使用 LLM 生成回答"""
        try:
            from openai import OpenAI
            import httpx
            import os
            
            # 使用与 query_system.py 相同的配置
            api_key = os.environ.get("DASHSCOPE_API_KEY", "") or os.environ.get("DASHSCOPE_", "")
            base_url = os.environ.get("LLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
            model_name = os.environ.get("LLM_MODEL", "qwen-plus")
            skip_verify = os.environ.get("LLM_INSECURE_SKIP_VERIFY", "true").lower() == "true"

            # WSL/企业代理环境下证书链可能不完整，允许通过环境变量跳过 TLS 校验
            if skip_verify:
                client = OpenAI(
                    api_key=api_key,
                    base_url=base_url,
                    http_client=httpx.Client(verify=False, timeout=60.0),
                )
            else:
                client = OpenAI(api_key=api_key, base_url=base_url)
            
            system_prompt = (
                "你是一个智能助手。请基于提供的【参考资料】回答用户的问题。\n"
                "如果参考资料为空或与问题无关，请忽略参考资料，利用你的通用知识进行回答，"
                "并在回答开头说明：'知识库中未找到相关内容，以下是基于通用知识的回答：'。\n"
                "回答要简洁、准确、有条理。"
            )
            
            user_prompt = f"问题：{question}\n\n"
            if context:
                user_prompt += f"【参考资料】：\n{context}"
            else:
                user_prompt += "【参考资料】：(无)"
                
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7
            )
            
            return {
                "answer": response.choices[0].message.content,
                "degraded": False,
                "warning": "",
                "error_code": ""
            }
            
        except Exception as e:
            logger.error(f"LLM 生成失败: {e}")
            error_msg = str(e)
            error_code = self._classify_llm_error(error_msg)
            fallback_answer = self._build_fallback_answer(question, context)
            return {
                "answer": fallback_answer,
                "degraded": True,
                "warning": "LLM 服务暂时不可用，已返回降级回答",
                "error_code": error_code
            }

    def _classify_llm_error(self, error_msg: str) -> str:
        """对 LLM 异常做粗粒度分类，便于 API 和前端展示"""
        msg = (error_msg or "").lower()
        if any(k in msg for k in ["401", "unauthorized", "api key", "invalid key"]):
            return "llm_auth_error"
        if any(k in msg for k in ["timeout", "timed out", "connection", "dns", "ssl", "certificate"]):
            return "llm_network_error"
        if any(k in msg for k in ["model", "not found", "invalid model"]):
            return "llm_model_error"
        return "llm_unknown_error"

    def _build_fallback_answer(self, question: str, context: str) -> str:
        """LLM 异常时的降级回答策略：优先用检索上下文，次选通用提示"""
        if context and context.strip():
            excerpt = context[:500]
            return (
                "知识库中已检索到相关内容，但大模型服务暂时不可用。"
                "以下是基于检索片段的降级摘要：\n\n"
                f"{excerpt}"
            )

        return (
            "知识库中未找到可用内容，且大模型服务暂时不可用。"
            "请稍后重试，或先上传更相关的文档后再提问。"
        )
    
    def _calculate_confidence(self, scores: List[float]) -> float:
        """
        计算回答置信度
        
        Args:
            scores: 相似度分数列表
            
        Returns:
            置信度分数 (0-1)
        """
        if not scores:
            return 0.0
        
        # 基于最高相似度分数和结果数量计算置信度
        max_score = max(scores)
        avg_score = sum(scores) / len(scores)
        
        # 结果数量权重
        count_weight = min(len(scores) / 5.0, 1.0)
        
        # 综合置信度
        confidence = (max_score * 0.6 + avg_score * 0.4) * count_weight
        
        return min(confidence, 1.0)
    
    
    
    def get_statistics(self, collection_name: str) -> Dict[str, Any]:
        """
        获取检索统计信息
        
        Args:
            collection_name: Milvus 集合名称

        Returns:
            统计信息字典
        """
        db_info = self.db_manager.get_database_info()
        
        stats = {
            "database_info": db_info,
            "similarity_threshold": self.similarity_threshold,
            "max_results": self.max_results,
            "retriever_status": "active" if db_info.get("is_initialized") else "inactive"
        }
        
        return stats


class QuestionClassifier:
    @classmethod
    def classify_question(cls, question: str) -> str:
        return "通用查询"


def main():
    """测试函数"""
    # 初始化 Milvus 连接
    try:
        db_manager = VectorDatabaseManager(
            milvus_host="localhost",
            milvus_port="19530"
        )
        retriever = VectorRetriever(db_manager)
        collection_name = "agent_rag"
        print("向量系统初始化成功")
    except Exception as e:
        print(f"向量系统初始化失败: {e}")
        return

    # 准备测试数据
    info = db_manager.get_database_info()
    if not info.get("is_initialized"):
        print(f"集合 '{collection_name}' 不存在，正在创建并添加数据...")
        # 此处可以添加一个示例文件上传的逻辑
        # 例如: db_manager.process_file("path/to/your/data.csv", collection_name)
        print("请先手动上传数据以进行测试。")
        # return # 如果没有数据，可以选择退出

    # 测试问题回答
    test_questions = [
        "Milvus 是什么？",
        "如何将文本上传到向量数据库？",
        "RAG 工作流程的关键步骤是什么？"
    ]
    
    print("\n--- 测试问答功能 ---")
    for question in test_questions:
        print(f"\n问题: {question}")
        
        result = retriever.answer_question(question, collection_name=collection_name)
        print(f"回答: {result.answer}")
        print(f"置信度: {result.confidence:.2f}")
        print(f"问题类型: {result.question_type}")
        print(f"参考来源数: {len(result.source_documents)}")
    
    


if __name__ == "__main__":
    main()
