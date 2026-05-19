"""
API集成模块
将向量数据库功能集成到Flask应用中
"""

import logging
import os
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict

from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename

from .config import UPLOAD_ROOT, load_environment

load_environment()

# 为了允许在未安装全部向量依赖的情况下启动后端，
# 将向量相关模块改为延迟导入（在需要时再导入）
VectorDatabaseManager = None
VectorRetriever = None
DocumentLoader = None

# 创建蓝图
vector_bp = Blueprint('vector', __name__, url_prefix='/api/vector')

# 全局变量存储向量系统实例
vector_manager: VectorDatabaseManager = None
vector_retriever: VectorRetriever = None
upload_tasks: Dict[str, Dict[str, Any]] = {}
upload_tasks_lock = threading.Lock()

# 临时上传目录
UPLOAD_FOLDER = str(UPLOAD_ROOT)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _cleanup_upload_tasks(max_age_seconds: int = 3600):
    """清理过期任务，避免内存无限增长"""
    now = time.time()
    with upload_tasks_lock:
        expired_task_ids = [
            task_id
            for task_id, task in upload_tasks.items()
            if now - task.get('updated_at', now) > max_age_seconds
        ]
        for task_id in expired_task_ids:
            upload_tasks.pop(task_id, None)


def _set_upload_task(task_id: str, **updates):
    """线程安全更新上传任务状态"""
    with upload_tasks_lock:
        task = upload_tasks.get(task_id, {})
        task.update(updates)
        task['updated_at'] = time.time()
        upload_tasks[task_id] = task


def _run_upload_task(task_id: str, file_path: str, filename: str, collection_name: str):
    """后台执行文档解析和入库"""
    global vector_manager

    def progress_callback(progress: int, stage: str, extra: Dict[str, Any]):
        _set_upload_task(
            task_id,
            status='processing',
            progress=progress,
            stage=stage,
            detail=extra or {}
        )

    try:
        _set_upload_task(
            task_id,
            status='processing',
            progress=5,
            stage='queued',
            detail={'file_name': filename}
        )

        success = vector_manager.process_file(
            file_path,
            collection_name,
            progress_callback=progress_callback
        )
        if success:
            db_info = vector_manager.get_database_info(collection_name)
            storage_mode = db_info.get('storage_mode', 'empty')
            if storage_mode == 'milvus':
                message = f'文件上传并处理成功（Milvus）: {filename}'
                warning = ''
            elif storage_mode == 'fallback_memory':
                message = f'文件已解析，但 Milvus 写入失败，当前仅内存检索可用: {filename}'
                warning = 'fallback_memory_only'
            else:
                message = f'文件处理完成，但未检测到可检索数据: {filename}'
                warning = 'no_index_data'
            _set_upload_task(
                task_id,
                status='completed',
                progress=100,
                stage='completed',
                message=message,
                warning=warning,
                database_info=db_info
            )
        else:
            _set_upload_task(
                task_id,
                status='failed',
                progress=100,
                stage='failed',
                message=f'文件处理失败: {filename}'
            )
    except Exception as e:
        logger.error(f"后台文档处理失败: {e}")
        _set_upload_task(
            task_id,
            status='failed',
            progress=100,
            stage='failed',
            message=str(e)
        )
    finally:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except OSError:
            logger.warning(f"无法删除临时文件: {file_path}")


def init_vector_system(
    milvus_host: str = None,
    milvus_port: str = None,
    embedding_model: str = None,
    dashscope_api_key: str = None
):
    """初始化向量系统（延迟导入向量模块）"""
    global vector_manager, vector_retriever, VectorDatabaseManager, VectorRetriever, DocumentLoader

    # 延迟导入可能依赖较多的向量模块，避免在未安装全部依赖时阻塞应用启动
    if VectorDatabaseManager is None or VectorRetriever is None:
        try:
            from .document_loader import DocumentLoader as _DocumentLoader
            from .vector_db_manager import VectorDatabaseManager as _VectorDatabaseManager
            from .vector_retriever import VectorRetriever as _VectorRetriever
        except Exception as e:
            logger.warning(f"无法导入向量模块，跳过初始化: {e}")
            return False

        VectorDatabaseManager = _VectorDatabaseManager
        VectorRetriever = _VectorRetriever
        DocumentLoader = _DocumentLoader

    try:
        vector_manager = VectorDatabaseManager(
            milvus_host=milvus_host,
            milvus_port=milvus_port,
            embedding_model=embedding_model,
            dashscope_api_key=dashscope_api_key
        )
        vector_retriever = VectorRetriever(vector_manager)
        logger.info(f"向量系统初始化成功，连接到 Milvus at {milvus_host}:{milvus_port}")
        return True
    except Exception as e:
        logger.error(f"向量系统初始化失败: {str(e)}")
        return False


@vector_bp.route('/upload_document', methods=['POST'])
def upload_document():
    """上传并处理文档"""
    global vector_manager
    
    if not vector_manager:
        return jsonify({
            'success': False,
            'message': '向量系统未初始化'
        }), 400
    
    try:
        data = request.get_json()
        if not data or 'file_path' not in data or 'collection_name' not in data:
            return jsonify({
                'success': False,
                'message': '请提供 file_path 和 collection_name 参数'
            }), 400
        
        file_path = data['file_path']
        collection_name = data['collection_name']
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'message': f'文件不存在: {file_path}'
            }), 400
        
        # 处理文档
        success = vector_manager.process_file(file_path, collection_name)
        
        if success:
            # 获取数据库信息
            db_info = vector_manager.get_database_info(collection_name)
            
            return jsonify({
                'success': True,
                'message': f'文档处理成功: {file_path}',
                'database_info': db_info
            })
        else:
            return jsonify({
                'success': False,
                'message': f'文档处理失败: {file_path}'
            }), 500
            
    except Exception as e:
        logger.error(f"文档上传API错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'文档处理失败: {str(e)}'
        }), 500


@vector_bp.route('/upload_file', methods=['POST'])
def upload_file():
    """上传文件流处理，并异步执行解析入库"""
    global vector_manager
    
    if not vector_manager:
        return jsonify({'success': False, 'message': '向量系统未初始化'}), 400

    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '未找到文件部分'}), 400
        
    file = request.files['file']
    collection_name = request.form.get('collection_name', 'agent_rag')
    
    if file.filename == '':
        return jsonify({'success': False, 'message': '未选择文件'}), 400
        
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)

        task_id = uuid.uuid4().hex
        _cleanup_upload_tasks()
        _set_upload_task(
            task_id,
            upload_task_id=task_id,
            status='queued',
            progress=0,
            stage='upload_received',
            message='文件上传成功，开始解析入库',
            collection_name=collection_name,
            file_name=filename,
            created_at=time.time()
        )

        worker = threading.Thread(
            target=_run_upload_task,
            args=(task_id, file_path, filename, collection_name),
            daemon=True
        )
        worker.start()

        return jsonify({
            'success': True,
            'accepted': True,
            'task_id': task_id,
            'message': '文件上传成功，后台正在解析入库',
            'status': 'queued',
            'progress': 0
        }), 202

    return jsonify({'success': False, 'message': '上传失败'}), 500


@vector_bp.route('/upload_task/<task_id>', methods=['GET'])
def get_upload_task(task_id: str):
    """查询上传入库任务进度"""
    _cleanup_upload_tasks()
    with upload_tasks_lock:
        task = upload_tasks.get(task_id)

    if not task:
        return jsonify({'success': False, 'message': '任务不存在或已过期'}), 404

    return jsonify({
        'success': True,
        'task': task
    })


@vector_bp.route('/query', methods=['POST'])
def query_documents():
    """查询文档"""
    global vector_retriever
    
    if not vector_retriever:
        return jsonify({
            'success': False,
            'message': '向量系统未初始化'
        }), 400
    
    try:
        data = request.get_json()
        if not data or 'question' not in data or 'collection_name' not in data:
            return jsonify({
                'success': False,
                'message': '请提供 question 和 collection_name 参数'
            }), 400
        
        question = data['question']
        collection_name = data['collection_name']
        k = data.get('k', 5)  # 返回结果数量
        
        # 执行查询
        result = vector_retriever.answer_question(question, k=k, collection_name=collection_name)

        degraded = getattr(result, 'degraded', False)
        warning = getattr(result, 'warning', '')
        error_code = getattr(result, 'error_code', '')

        response_payload = {
            'success': True,
            'question': question,
            'answer': result.answer,
            'confidence': result.confidence,
            'question_type': result.question_type,
            'sources': [
                {
                    'content': doc.page_content,
                    'metadata': doc.metadata,
                    'score': score
                }
                for doc, score in zip(result.source_documents, result.scores)
            ]
        }

        if degraded:
            response_payload['degraded'] = True
            if warning:
                response_payload['warning'] = warning
            if error_code:
                response_payload['error_code'] = error_code

        return jsonify(response_payload)
        
    except Exception as e:
        logger.error(f"查询API错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'查询失败: {str(e)}'
        }), 500


@vector_bp.route('/search', methods=['POST'])
def search_similar():
    """相似性搜索"""
    global vector_retriever
    
    if not vector_retriever:
        return jsonify({
            'success': False,
            'message': '向量系统未初始化'
        }), 400
    
    try:
        data = request.get_json()
        if not data or 'query' not in data or 'collection_name' not in data:
            return jsonify({
                'success': False,
                'message': '请提供 query 和 collection_name 参数'
            }), 400
        
        query = data['query']
        collection_name = data['collection_name']
        k = data.get('k', 5)
        
        # 执行相似性搜索
        results = vector_retriever.search_similar_content(query, k=k, collection_name=collection_name)
        
        return jsonify({
            'success': True,
            'query': query,
            'results': [
                {
                    'content': doc.page_content,
                    'metadata': doc.metadata,
                    'score': score
                }
                for doc, score in results
            ]
        })
        
    except Exception as e:
        logger.error(f"搜索API错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'搜索失败: {str(e)}'
        }), 500


@vector_bp.route('/collection_info', methods=['GET'])
def get_collection_info():
    """获取集合信息"""
    global vector_manager
    
    if not vector_manager:
        return jsonify({
            'success': False,
            'message': '向量系统未初始化'
        }), 400
    
    collection_name = request.args.get('collection_name')
    if not collection_name:
        return jsonify({
            'success': False,
            'message': '请提供 collection_name 参数'
        }), 400

    try:
        db_info = vector_manager.get_database_info(collection_name)
        return jsonify({
            'success': True,
            'database_info': db_info
        })
        
    except Exception as e:
        logger.error(f"数据库信息API错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取数据库信息失败: {str(e)}'
        }), 500


@vector_bp.route('/clear_collection', methods=['POST'])
def clear_collection():
    """清空集合"""
    global vector_manager
    
    if not vector_manager:
        return jsonify({
            'success': False,
            'message': '向量系统未初始化'
        }), 400
    
    data = request.get_json()
    if not data or 'collection_name' not in data:
        return jsonify({
            'success': False,
            'message': '请提供 collection_name 参数'
        }), 400

    collection_name = data['collection_name']

    try:
        vector_manager.clear_database(collection_name)
        return jsonify({
            'success': True,
            'message': f"集合 '{collection_name}' 已清空"
        })
        
    except Exception as e:
        logger.error(f"清空数据库API错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'清空数据库失败: {str(e)}'
        }), 500


# 错误处理
@vector_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'message': '接口不存在'
    }), 404


@vector_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'message': '服务器内部错误'
    }), 500


def register_vector_routes(app):
    """注册向量数据库路由到Flask应用"""
    app.register_blueprint(vector_bp)
    
    # 自动初始化向量系统
    with app.app_context():
        init_vector_system()
    
    logger.info("向量数据库API路由已注册")
