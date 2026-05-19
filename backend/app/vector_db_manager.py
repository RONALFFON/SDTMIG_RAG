"""
向量数据库管理模块
基于LangChain和Milvus实现文档切分、向量化存储和检索功能
- 1.
MinIO (对象存储服务) : Milvus 使用 MinIO 来存储数据。它提供了一个网页管理界面。

- 登录页面 : http://localhost:9001
- 账号 (Access Key) : minioadmin
- 密码 (Secret Key) : minioadmin
- 2.
Milvus (向量数据库) : 在我们当前的配置中，Milvus 本身 没有 提供一个用于登录的网页界面。您可以通过代码（例如使用 pymilvus 库）连接到 Milvus 服务来进行操作。

- 连接地址 : localhost:19530
"""

import os
import json
import logging
import re
from difflib import SequenceMatcher
from typing import Callable, List, Dict, Any, Optional, Tuple

# LangChain and Milvus imports
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings, DashScopeEmbeddings
from langchain_community.embeddings.fake import FakeEmbeddings
from langchain_milvus import Milvus
from langchain_core.documents import Document
from langchain_community.document_loaders import (
    TextLoader, 
    CSVLoader, 
    PyPDFLoader, 
    Docx2txtLoader,
    UnstructuredExcelLoader
)
from pymilvus import utility, connections, Collection, FieldSchema, CollectionSchema, DataType

from .config import load_environment

load_environment()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ProgressCallback = Optional[Callable[[int, str, Dict[str, Any]], None]]

class VectorDatabaseManager:
    """向量数据库管理器 (Milvus后端)"""
    
    def __init__(self, 
                 milvus_host: str = None,
                 milvus_port: int = None,
                 collection_name: str = None,
                 embedding_model: str = None,
                 dashscope_api_key: str = None,
                 chunk_size: int = 500,
                 chunk_overlap: int = 50):
        """
        初始化向量数据库管理器
        
        Args:
            milvus_host: Milvus 服务主机
            milvus_port: Milvus 服务端口
            collection_name: Milvus 集合名称
            embedding_model: DashScope嵌入模型名称
            dashscope_api_key: DashScope API密钥
            chunk_size: 文档切分块大小
            chunk_overlap: 文档切分重叠大小
        """
        self.milvus_host = milvus_host or os.getenv("MILVUS_HOST", "127.0.0.1")
        # Ensure port is a string as pymilvus might expect it, or handle int gracefully
        self.milvus_port = str(milvus_port or os.getenv("MILVUS_PORT", "19530"))
        self.collection_name = collection_name or os.getenv("COLLECTION_NAME", "agent_rag")
        self.embedding_model = embedding_model or os.getenv("EMBEDDING_MODEL", "text-embedding-v1")
        self.dashscope_api_key = dashscope_api_key or os.getenv("DASHSCOPE_API_KEY", "")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # 初始化嵌入模型
        self._init_embeddings()
        
        # 初始化文档切分器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]
        )
        
        # 连接到Milvus
        self._connect_to_milvus()
        
        # 向量数据库实例
        self.vectorstore = None
        # Milvus 不可用时的内存兜底存储
        self._fallback_documents: Dict[str, List[Document]] = {}
        # 最近一次写入状态，便于 API 层判断“是否真正入 Milvus”
        self._last_write_backend = "none"
        self._last_write_error = ""
        self._last_write_collection = self.collection_name
        self._last_write_count = 0
        # 延迟加载：不要在 __init__ 中调用 _load_existing_db，避免启动时连接未就绪或报错
        # self._load_existing_db() 

    def _init_embeddings(self):
        """初始化嵌入模型"""
        try:
            # 确保 API Key 存在
            if not self.dashscope_api_key:
                 logger.warning("未提供 DashScope API Key，将尝试从环境变量获取")
                 self.dashscope_api_key = os.environ.get("DASHSCOPE_API_KEY", "")

            self.embeddings = DashScopeEmbeddings(
                model=self.embedding_model,
                dashscope_api_key=self.dashscope_api_key
            )
            # 简单测试 embedding 是否工作
            try:
                self.embeddings.embed_query("test")
                logger.info(f"成功加载并验证 DashScope嵌入模型: {self.embedding_model}")
            except Exception as e:
                 logger.error(f"DashScope 模型验证失败: {e}")
                 raise e

        except Exception as e:
            logger.error(f"加载DashScope模型失败: {e}")
            # 直接使用 FakeEmbeddings，避免在受限网络下加载 HuggingFace 模型导致启动阻塞
            logger.warning("启用 FakeEmbeddings 作为兜底嵌入模型")
            self.embeddings = FakeEmbeddings(size=768)

    def _connect_to_milvus(self):
        """连接到Milvus服务"""
        try:
            logger.info(f"Connecting to Milvus: host={self.milvus_host}, port={self.milvus_port}")
            connections.connect("default", host=self.milvus_host, port=self.milvus_port)
            logger.info(f"成功连接到Milvus: {self.milvus_host}:{self.milvus_port}")
        except Exception as e:
            logger.error(f"连接Milvus失败: {e}")
            raise

    def _ensure_milvus_connection(self):
        """在执行读写前确保默认连接可用"""
        try:
            # 直接重连是幂等的，可避免连接被回收导致的 ConnectionNotExistException
            connections.connect("default", host=self.milvus_host, port=self.milvus_port)
        except Exception as e:
            logger.error(f"Milvus重连失败: {e}")
            raise

    def _load_existing_db(self):
        """加载已存在的Milvus集合"""
        try:
            if utility.has_collection(self.collection_name):
                try:
                    self.vectorstore = Milvus(
                        embedding_function=self.embeddings,
                        collection_name=self.collection_name,
                        connection_args={"host": self.milvus_host, "port": self.milvus_port, "alias": "default"}
                    )
                    logger.info(f"成功加载现有Milvus集合: {self.collection_name}")
                except Exception as e:
                    logger.error(f"加载现有集合失败: {e}")
                    # 不再自动删除，防止误删数据。
                    # 如果 Schema 不兼容，将在写入时处理。
                    self.vectorstore = None
            else:
                logger.info(f"未找到集合 {self.collection_name}，将在添加文档时创建")
        except Exception as e:
            logger.error(f"加载Milvus集合失败: {e}")

    def load_document(self, file_path: str) -> List[Document]:
        """根据文件类型加载文档"""
        # ... (代码与之前版本相同)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        file_extension = Path(file_path).suffix.lower()
        
        try:
            if file_extension == '.txt':
                loader = TextLoader(file_path, encoding='utf-8')
            elif file_extension == '.csv':
                loader = CSVLoader(file_path, encoding='utf-8')
            elif file_extension == '.pdf':
                loader = PyPDFLoader(file_path)
            elif file_extension in ['.docx', '.doc']:
                loader = Docx2txtLoader(file_path)
            elif file_extension in ['.xlsx', '.xls']:
                loader = UnstructuredExcelLoader(file_path)
            else:
                loader = TextLoader(file_path, encoding='utf-8')
                logger.warning(f"未识别的文件类型 {file_extension}, 使用文本加载器")
            
            documents = loader.load()
            logger.info(f"成功加载文档: {file_path}, 共 {len(documents)} 个文档块")
            return documents
            
        except Exception as e:
            logger.error(f"加载文档失败 {file_path}: {e}")
            return []

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """切分文档"""
        # ... (代码与之前版本相同)
        try:
            split_docs = self.text_splitter.split_documents(documents)
            logger.info(f"文档切分完成: {len(documents)} -> {len(split_docs)} 个块")
            return split_docs
        except Exception as e:
            logger.error(f"文档切分失败: {e}")
            return documents

    def add_documents_to_db(self, documents: List[Document], collection_name: str = None) -> str:
        """
        将文档添加到Milvus数据库
        
        Args:
            documents: 文档列表
            collection_name: 集合名称（可选，覆盖默认）
        """
        if not documents:
            logger.warning("没有文档需要添加")
            return "skipped"
        
        target_collection = collection_name or self.collection_name
        self._last_write_collection = target_collection
        self._last_write_count = len(documents)
        self._last_write_error = ""
        
        try:
            self._ensure_milvus_connection()
            # 为规避连接别名丢失导致的 add_documents 报错，
            # 统一通过 from_documents 执行写入（集合存在时会追加，drop_old=False）
            self.vectorstore = Milvus.from_documents(
                documents=documents,
                embedding=self.embeddings,
                collection_name=target_collection,
                connection_args={"host": self.milvus_host, "port": self.milvus_port, "alias": "default"},
                drop_old=False
            )
            self.collection_name = target_collection
            logger.info(f"成功写入集合 '{target_collection}'，文档数: {len(documents)}")
            self._last_write_backend = "milvus"
            return "milvus"
            
        except Exception as e:
            # 捕获 Schema 不兼容错误并尝试自动修复（重建）
            msg = str(e)
            if "non-exist field" in msg or "inconsistent with defined schema" in msg:
                 logger.warning(f"检测到 Schema 不兼容 ({e})，尝试重建集合...")
                 try:
                     if utility.has_collection(target_collection):
                         utility.drop_collection(target_collection)
                     
                     self.vectorstore = Milvus.from_documents(
                        documents=documents,
                        embedding=self.embeddings,
                        collection_name=target_collection,
                        connection_args={"host": self.milvus_host, "port": self.milvus_port, "alias": "default"},
                        drop_old=True
                     )
                     self.collection_name = target_collection
                     logger.info(f"集合 '{target_collection}' 已重建并写入数据")
                     self._last_write_backend = "milvus"
                     self._last_write_error = ""
                     return "milvus"
                 except Exception as re:
                     logger.error(f"重建集合失败: {re}")
                     # langchain_milvus 在部分环境会抛 ConnectionNotExistException，回退到 pymilvus 直写
                     pym_ok = self._add_documents_via_pymilvus(target_collection, documents)
                     if pym_ok:
                         self._last_write_backend = "milvus_pymilvus"
                         self._last_write_error = ""
                         return "milvus_pymilvus"
                     self._last_write_backend = "fallback"
                     self._last_write_error = str(re)
                     self._fallback_add_documents(target_collection, documents)
                     logger.warning(f"重建失败后回退到内存知识库写入，集合: {target_collection}, 文档数: {len(documents)}")
                     return "fallback"
            else:
                logger.error(f"添加文档到Milvus失败: {e}")
                pym_ok = self._add_documents_via_pymilvus(target_collection, documents)
                if pym_ok:
                    self._last_write_backend = "milvus_pymilvus"
                    self._last_write_error = ""
                    return "milvus_pymilvus"
                self._last_write_backend = "fallback"
                self._last_write_error = str(e)
                self._fallback_add_documents(target_collection, documents)
                return "fallback"

    def process_file(
        self,
        file_path: str,
        collection_name: str = None,
        progress_callback: ProgressCallback = None
    ) -> bool:
        """
        处理单个文件：加载、切分、存储
        
        Args:
            file_path: 文件路径
            collection_name: 集合名称
            
        Returns:
            处理是否成功
        """
        def report(progress: int, stage: str, **extra):
            if progress_callback:
                progress_callback(progress, stage, extra)

        try:
            logger.info(f"开始处理文件: {file_path}")
            report(10, "preparing", file_name=os.path.basename(file_path))
            documents = self.load_document(file_path)
            if not documents:
                report(100, "failed", error="文档加载失败或内容为空")
                return False

            report(35, "parsing", document_count=len(documents))
            split_docs = self.split_documents(documents)
            report(65, "chunking", chunk_count=len(split_docs))
            storage_mode = self.add_documents_to_db(split_docs, collection_name)

            report(100, "completed", chunk_count=len(split_docs), storage_mode=storage_mode)
            logger.info(f"文件处理完成: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"处理文件失败 {file_path}: {e}")
            report(100, "failed", error=str(e))
            return False

    def process_csv_data(self, csv_path: str,
                         text_columns: List[str] = None,
                         metadata_columns: List[str] = None) -> bool:
        """
        处理CSV数据文件
        
        Args:
            csv_path: CSV文件路径
            text_columns: 需要向量化的文本列名列表
            
        Returns:
            处理是否成功
        """
        try:
            import pandas as pd
            df = pd.read_csv(csv_path, encoding='utf-8')
            logger.info(f"读取CSV文件: {csv_path}, 共 {len(df)} 行数据")
            if text_columns is None or not text_columns:
                object_cols = [c for c in df.columns if df[c].dtype == 'object']
                text_columns = [c for c in object_cols if not str(c).startswith('Unnamed')]

            if metadata_columns is None:
                metadata_columns = [c for c in df.columns if c not in text_columns]

            documents = []
            for idx, row in df.iterrows():
                content_parts = []
                metadata = {"source": csv_path, "row_index": idx}
                
                for col in text_columns:
                    if pd.notna(row[col]):
                        text = str(row[col]).strip()
                        if text:
                            content_parts.append(f"{col}: {text}")

                for col in metadata_columns:
                    val = row.get(col)
                    if pd.notna(val):
                        metadata[str(col)] = str(val)
                
                if content_parts:
                    content = "\n".join(content_parts)
                    doc = Document(page_content=content, metadata=metadata)
                    documents.append(doc)
            
            logger.info(f"构建了 {len(documents)} 个文档")
            split_docs = self.split_documents(documents)
            self.add_documents_to_db(split_docs)
            
            return True
            
        except Exception as e:
            logger.error(f"处理CSV数据失败: {e}")
            return False

    def get_embedding(self, texts: List[str]) -> List[List[float]]:
        """使用嵌入模型为一组文本生成嵌入向量"""
        try:
            return self.embeddings.embed_documents(texts)
        except Exception as e:
            logger.error(f"生成嵌入向量失败: {e}")
            return []

    def search(self, query: str, k: int = 5, filter_dict: Dict = None, collection_name: Optional[str] = None) -> List[Tuple[Document, float]]:
        """
        相似性搜索
        
        Args:
            query: 查询文本
            k: 返回结果数量
            filter_dict: Milvus目前不支持直接的元数据过滤，此参数保留但暂不使用
            collection_name: 指定要搜索的集合名称（可选）
        
        Returns:
            (文档, 相似度分数) 列表
        """
        target_collection = collection_name or self.collection_name

        if self.vectorstore is None or (target_collection and self.collection_name != target_collection):
            try:
                self._ensure_milvus_connection()
                if target_collection and utility.has_collection(target_collection):
                    self.vectorstore = Milvus(
                        embedding_function=self.embeddings,
                        collection_name=target_collection,
                        connection_args={"host": self.milvus_host, "port": self.milvus_port, "alias": "default"}
                    )
                    self.collection_name = target_collection
                    logger.info(f"加载集合用于搜索: {target_collection}")
                else:
                    logger.warning("向量数据库未初始化，尝试内存知识库检索")
                    return self._fallback_search(query, target_collection, k)
            except Exception as e:
                logger.error(f"加载Milvus集合失败: {e}")
                pym_results = self._search_via_pymilvus(query, target_collection, k)
                if pym_results:
                    return pym_results
                return self._fallback_search(query, target_collection, k)
        
        try:
            if filter_dict:
                logger.warning("Milvus集成当前不支持直接的元数据过滤，该过滤器将被忽略。")
            
            results = self.vectorstore.similarity_search_with_score(query=query, k=k)
            logger.info(f"搜索查询: '{query}', 返回 {len(results)} 个结果")
            return results
            
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            pym_results = self._search_via_pymilvus(query, target_collection, k)
            if pym_results:
                return pym_results
            return self._fallback_search(query, target_collection, k)

    def get_database_info(self, collection_name: str = None) -> Dict[str, Any]:
        """
        获取数据库信息
        """
        target_collection = collection_name or self.collection_name
        
        fallback_count = len(self._fallback_documents.get(target_collection, []))
        info = {
            "milvus_host": self.milvus_host,
            "milvus_port": self.milvus_port,
            "collection_name": target_collection,
            "is_initialized": self.vectorstore is not None,
            "fallback_document_count": fallback_count,
            "last_write_backend": self._last_write_backend,
            "last_write_error": self._last_write_error
        }
        
        try:
            self._ensure_milvus_connection()
            # 如果 vectorstore 未初始化，尝试临时连接检查
            if utility.has_collection(target_collection):
                # 使用 Collection 对象获取统计信息
                col = Collection(target_collection)
                # 刷新以确保获取最新数据量（刚插入的数据可能还在内存中）
                col.flush()
                info["document_count"] = col.num_entities
                
                # 如果 self.vectorstore 为空但集合存在，尝试初始化它（如果还没做过）
                if self.vectorstore is None:
                     try:
                        self.vectorstore = Milvus(
                            embedding_function=self.embeddings,
                            collection_name=target_collection,
                            connection_args={"host": self.milvus_host, "port": self.milvus_port, "alias": "default"}
                        )
                        info["is_initialized"] = True
                     except:
                        pass # 忽略加载错误，只返回统计
            else:
                info["document_count"] = 0
        except Exception as e:
            logger.error(f"获取Milvus集合信息失败: {e}")
            info["error"] = str(e)
            info["document_count"] = 0

        # 用稳定规则给前端/调用方表达真实存储状态
        if info.get("document_count", 0) > 0:
            info["storage_mode"] = "milvus"
        elif info.get("fallback_document_count", 0) > 0:
            info["storage_mode"] = "fallback_memory"
        else:
            info["storage_mode"] = "empty"
        info["is_initialized"] = info["storage_mode"] != "empty"
        
        return info

    def _add_documents_via_pymilvus(self, collection_name: str, documents: List[Document]) -> bool:
        """绕过 langchain_milvus 的直连写入，避免 ConnectionNotExistException。"""
        if not documents:
            return False
        try:
            self._ensure_milvus_connection()
            texts = [(doc.page_content or "")[:65535] for doc in documents]
            metadatas = [dict(doc.metadata or {}) for doc in documents]
            vectors = self.embeddings.embed_documents(texts)
            if not vectors:
                return False
            dim = len(vectors[0])

            # 如果已有集合 schema 与直连写入字段不兼容，则重建。
            recreate = False
            if utility.has_collection(collection_name):
                existing = Collection(collection_name)
                field_names = {f.name for f in existing.schema.fields}
                if not {"content", "metadata", "embedding"}.issubset(field_names):
                    recreate = True
                else:
                    try:
                        emb_field = next(f for f in existing.schema.fields if f.name == "embedding")
                        old_dim = int((emb_field.params or {}).get("dim", dim))
                        if old_dim != dim:
                            recreate = True
                    except Exception:
                        recreate = True
                if recreate:
                    logger.warning(f"检测到集合 '{collection_name}' schema 不兼容，执行重建以恢复 Milvus 写入。")
                    utility.drop_collection(collection_name)

            if not utility.has_collection(collection_name):
                schema = CollectionSchema(
                    fields=[
                        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                        FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
                        FieldSchema(name="metadata", dtype=DataType.JSON),
                        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim),
                    ],
                    description="RAG documents",
                )
                Collection(name=collection_name, schema=schema)

            col = Collection(collection_name)
            existing_indexes = {idx.field_name for idx in col.indexes}
            if "embedding" not in existing_indexes:
                col.create_index(
                    field_name="embedding",
                    index_params={"index_type": "AUTOINDEX", "metric_type": "COSINE", "params": {}},
                )

            col.insert([texts, metadatas, vectors])
            col.flush()
            col.load()
            logger.info(f"通过 pymilvus 写入集合成功: {collection_name}, 文档数: {len(texts)}")
            return True
        except Exception as e:
            logger.error(f"pymilvus 直写失败: {e}")
            return False

    def _search_via_pymilvus(self, query: str, collection_name: str, k: int) -> List[Tuple[Document, float]]:
        """绕过 langchain_milvus 的直连检索。"""
        try:
            self._ensure_milvus_connection()
            if not utility.has_collection(collection_name):
                return []
            col = Collection(collection_name)
            col.load()
            qvec = self.embeddings.embed_query(query)
            results = col.search(
                data=[qvec],
                anns_field="embedding",
                param={"metric_type": "COSINE", "params": {}},
                limit=k,
                output_fields=["content", "metadata"],
            )
            parsed: List[Tuple[Document, float]] = []
            for hit in results[0]:
                entity = hit.entity
                content = entity.get("content") if entity else ""
                metadata = entity.get("metadata") if entity else {}
                parsed.append((Document(page_content=content or "", metadata=metadata or {}), float(hit.score)))
            if parsed:
                logger.info(f"通过 pymilvus 直连检索成功，返回 {len(parsed)} 条")
            return parsed
        except Exception as e:
            logger.error(f"pymilvus 直连检索失败: {e}")
            return []

    def clear_database(self, collection_name: str = None):
        """清空Milvus集合与内存兜底数据"""
        target_collection = collection_name or self.collection_name
        try:
            self._ensure_milvus_connection()
            if utility.has_collection(target_collection):
                utility.drop_collection(target_collection)
                logger.info(f"Milvus集合 '{target_collection}' 已被删除")
        except Exception as e:
            logger.error(f"清空Milvus集合失败: {e}")
        finally:
            self._fallback_documents.pop(target_collection, None)
            if target_collection == self.collection_name:
                self.vectorstore = None

    def _fallback_add_documents(self, collection_name: str, documents: List[Document]):
        """将文档写入内存兜底知识库"""
        bucket = self._fallback_documents.setdefault(collection_name, [])
        bucket.extend(documents)

    def _fallback_search(self, query: str, collection_name: str, k: int) -> List[Tuple[Document, float]]:
        """兜底检索：兼容中英文，尽量在无向量库时返回可用上下文"""
        docs = self._fallback_documents.get(collection_name, [])
        if not docs:
            return []

        query_terms = self._tokenize_for_fallback(query)
        query_text = (query or "").lower()
        scored: List[Tuple[Document, float]] = []
        for doc in docs:
            content = (doc.page_content or "")
            content_text = content.lower()
            terms = self._tokenize_for_fallback(content_text)
            if not terms or not content_text.strip():
                continue

            # 词项重叠 + 子串命中 + 序列相似度，组合成兜底分值
            overlap = len(query_terms & terms) / max(len(query_terms), 1)
            contains = 1.0 if query_text and query_text in content_text else 0.0
            ratio = SequenceMatcher(None, query_text[:128], content_text[:4096]).ratio()
            score = max(overlap, contains, 0.65 * overlap + 0.35 * ratio)

            # 给检索链路打标，便于上层调整阈值策略
            metadata = dict(doc.metadata or {})
            metadata["_retrieval_mode"] = "fallback"
            marked_doc = Document(page_content=doc.page_content, metadata=metadata)
            scored.append((marked_doc, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:k]

    def _tokenize_for_fallback(self, text: str) -> set:
        text = (text or "").lower()
        words = set(re.findall(r"[a-z0-9]+", text))
        cjk_chars = set(re.findall(r"[\u4e00-\u9fff]", text))
        cjk_bigrams = {
            text[i:i + 2]
            for i in range(len(text) - 1)
            if re.match(r"[\u4e00-\u9fff]", text[i]) and re.match(r"[\u4e00-\u9fff]", text[i + 1])
        }
        return words | cjk_chars | cjk_bigrams

def main():
    """测试函数"""
    # 确保Milvus服务正在运行
    try:
        connections.connect("default", host=os.getenv("MILVUS_HOST", "127.0.0.1"), port=os.getenv("MILVUS_PORT", "19530"))
        utility.get_collection_stats("agent_rag")
        connections.disconnect("default")
    except Exception as e:
        logger.error("无法连接到Milvus服务，请确保您已通过 docker-compose up -d 启动了Milvus。")
        logger.error(f"错误: {e}")
        return

    # 创建向量数据库管理器
    db_manager = VectorDatabaseManager()
    
    # 清空现有数据
    print("清空现有数据库...")
    db_manager.clear_database()

    # 处理学科数据CSV文件
    csv_path = "../data.csv"
    if os.path.exists(csv_path):
        print("处理CSV数据...")
        success = db_manager.process_csv_data(csv_path)
        if success:
            print("CSV数据处理成功！")
            
            # 测试搜索
            print("\n测试搜索功能:")
            results = db_manager.search("示例查询", k=3)
            for i, (doc, score) in enumerate(results):
                print(f"\n结果 {i+1} (相似度: {score:.4f}):")
                print(f"内容: {doc.page_content[:200]}...")
                print(f"元数据: {doc.metadata}")
        else:
            print("CSV数据处理失败！")
    else:
        print(f"未找到数据文件: {csv_path}")
    
    # 显示数据库信息
    print("\n数据库信息:")
    info = db_manager.get_database_info()
    print(json.dumps(info, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
