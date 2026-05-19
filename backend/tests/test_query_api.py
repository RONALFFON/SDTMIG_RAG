import unittest
from dataclasses import dataclass
from io import BytesIO
from time import sleep

from flask import Flask

from backend.app import api_integration


@dataclass
class DummyAnswerResult:
    answer: str = "ok"
    confidence: float = 0.8
    question_type: str = "通用查询"
    source_documents: list = None
    scores: list = None
    degraded: bool = False
    warning: str = ""
    error_code: str = ""

    def __post_init__(self):
        if self.source_documents is None:
            self.source_documents = []
        if self.scores is None:
            self.scores = []


class DummyRetriever:
    def __init__(self, result=None, should_raise=False):
        self.result = result or DummyAnswerResult()
        self.should_raise = should_raise

    def answer_question(self, question, collection_name, k=5):
        if self.should_raise:
            raise RuntimeError("mock retriever failure")
        return self.result


class DummyVectorManager:
    def __init__(self, should_fail=False):
        self.should_fail = should_fail

    def process_file(self, file_path, collection_name, progress_callback=None):
        if progress_callback:
            progress_callback(10, "preparing", {"file_name": "test.txt"})
            progress_callback(35, "parsing", {"document_count": 1})
            progress_callback(65, "chunking", {"chunk_count": 2})
        if self.should_fail:
            raise RuntimeError("mock upload failure")
        return True

    def get_database_info(self, collection_name):
        return {
            "collection_name": collection_name,
            "document_count": 2
        }


def create_test_client(retriever):
    app = Flask(__name__)
    app.testing = True
    app.register_blueprint(api_integration.vector_bp)
    api_integration.vector_retriever = retriever
    return app.test_client()


def create_test_client_with_manager(manager):
    app = Flask(__name__)
    app.testing = True
    app.register_blueprint(api_integration.vector_bp)
    api_integration.vector_manager = manager
    return app.test_client()


class QueryApiTests(unittest.TestCase):
    def setUp(self):
        api_integration.upload_tasks.clear()

    def test_query_missing_params_returns_400(self):
        client = create_test_client(DummyRetriever())
        resp = client.post("/api/vector/query", json={})
        payload = resp.get_json()

        self.assertEqual(resp.status_code, 400)
        self.assertFalse(payload["success"])
        self.assertIn("question", payload["message"])

    def test_query_degraded_success(self):
        result = DummyAnswerResult(
            answer="降级回答",
            degraded=True,
            warning="LLM 服务暂时不可用，已返回降级回答",
            error_code="llm_network_error",
        )
        client = create_test_client(DummyRetriever(result=result))
        resp = client.post(
            "/api/vector/query",
            json={"question": "什么是RAG", "collection_name": "agent_rag"},
        )
        payload = resp.get_json()

        self.assertEqual(resp.status_code, 200)
        self.assertTrue(payload["success"])
        self.assertTrue(payload["degraded"])
        self.assertEqual(payload["answer"], "降级回答")
        self.assertEqual(payload["error_code"], "llm_network_error")

    def test_query_internal_error_returns_500(self):
        client = create_test_client(DummyRetriever(should_raise=True))
        resp = client.post(
            "/api/vector/query",
            json={"question": "测试", "collection_name": "agent_rag"},
        )
        payload = resp.get_json()

        self.assertEqual(resp.status_code, 500)
        self.assertFalse(payload["success"])
        self.assertIn("查询失败", payload["message"])

    def test_upload_file_returns_task_and_status(self):
        client = create_test_client_with_manager(DummyVectorManager())
        resp = client.post(
            "/api/vector/upload_file",
            data={
                "collection_name": "agent_rag",
                "file": (BytesIO(b"hello"), "test.txt")
            },
            content_type="multipart/form-data"
        )
        payload = resp.get_json()

        self.assertEqual(resp.status_code, 202)
        self.assertTrue(payload["success"])
        self.assertTrue(payload["accepted"])
        self.assertIn("task_id", payload)

        sleep(0.1)
        task_resp = client.get(f"/api/vector/upload_task/{payload['task_id']}")
        task_payload = task_resp.get_json()

        self.assertEqual(task_resp.status_code, 200)
        self.assertTrue(task_payload["success"])
        self.assertEqual(task_payload["task"]["status"], "completed")
        self.assertEqual(task_payload["task"]["database_info"]["document_count"], 2)


if __name__ == "__main__":
    unittest.main()
