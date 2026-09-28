"""Unit tests for generated Protocol Buffer stubs."""
import pytest

from warden_shared.proto.v1 import (
    laya_pb2,
    laya_pb2_grpc,
    retrieval_pb2,
    retrieval_pb2_grpc,
)


def test_retrieval_proto_stubs():
    assert hasattr(retrieval_pb2_grpc, "RetrievalServiceStub")
    assert hasattr(retrieval_pb2_grpc, "RetrievalServiceServicer")

    req = retrieval_pb2.RetrieveRequest(
        query_text="What is the bereavement leave policy?",
        caller_role="Employee",
        top_k_candidates=30,
        final_rerank_limit=5,
        enable_reranker=True,
    )
    assert req.query_text == "What is the bereavement leave policy?"
    assert req.caller_role == "Employee"
    assert req.top_k_candidates == 30
    assert req.final_rerank_limit == 5
    assert req.enable_reranker is True

    passage = retrieval_pb2.Passage(
        doc_id="DOC-HR-LEAVE-2026",
        chunk_index=2,
        content="Bereavement Leave: Employees are eligible for up to 5 days...",
        source_url="file:///data/policies/pto.md",
        role_tags=["Employee", "Manager"],
        rrf_score=0.0328,
        calibrated_score=0.9421,
    )
    resp = retrieval_pb2.RetrieveResponse(
        query_text="What is the bereavement leave policy?",
        caller_role_applied="Employee",
        passages=[passage],
        reranker_applied=True,
        fallback_active=False,
        execution_time_ms=47.9,
        raw_candidates_count=30,
        pruned_candidates_count=9,
    )
    assert len(resp.passages) == 1
    assert resp.passages[0].doc_id == "DOC-HR-LEAVE-2026"
    assert resp.pruned_candidates_count == 9

def test_index_batch_proto_stubs():
    point = retrieval_pb2.PointData(
        point_id="e81d7f3e-2b58-5d32-9f37-123456789abc",
        doc_id="DOC-HR-LEAVE-2026",
        chunk_index=0,
        content="Policy text chunk",
        dense_vector=[0.1, 0.2, 0.3],
        role_tags=["Employee"],
        redacted=True,
        source_url="file:///data/pto.md",
        token_count=512,
    )
    batch_req = retrieval_pb2.IndexBatchRequest(
        points=[point],
        wait=False,
    )
    assert len(batch_req.points) == 1
    assert batch_req.wait is False

    batch_resp = retrieval_pb2.IndexBatchResponse(
        status="UPSERTED",
        points_count=1,
        execution_time_ms=3.8,
    )
    assert batch_resp.status == "UPSERTED"
    assert batch_resp.points_count == 1

def test_laya_proto_stubs():
    assert hasattr(laya_pb2_grpc, "LayaInferenceServiceStub")
    assert hasattr(laya_pb2_grpc, "LayaInferenceServiceServicer")

    candidate = laya_pb2.CandidateItem(
        candidate_id="cand-001",
        text="Bereavement leave passage text",
    )
    rerank_req = laya_pb2.RerankRequest(
        query="Bereavement leave",
        candidates=[candidate],
        primitive="noul",
    )
    assert rerank_req.primitive == "noul"
    assert len(rerank_req.candidates) == 1

    ranked = laya_pb2.RankedCandidate(
        candidate_id="cand-001",
        probability_true=0.9421,
        rank=1,
    )
    rerank_resp = laya_pb2.RerankResponse(
        query="Bereavement leave",
        ranked_results=[ranked],
        inference_latency_ms=42.5,
    )
    assert len(rerank_resp.ranked_results) == 1
    assert rerank_resp.ranked_results[0].probability_true == pytest.approx(0.9421)

def test_laya_route_proto_stubs():
    route_req = laya_pb2.RouteRequest(
        query="Draft a legal contract",
        choices=["HR_POLICY_QUESTION", "OUT_OF_SCOPE_REQUEST"],
    )
    assert len(route_req.choices) == 2

    route_resp = laya_pb2.RouteResponse(
        query="Draft a legal contract",
        selected_choice="OUT_OF_SCOPE_REQUEST",
        confidence_distribution={"OUT_OF_SCOPE_REQUEST": 0.95, "HR_POLICY_QUESTION": 0.05},
        inference_latency_ms=24.1,
    )
    assert route_resp.selected_choice == "OUT_OF_SCOPE_REQUEST"
    assert route_resp.confidence_distribution["OUT_OF_SCOPE_REQUEST"] == pytest.approx(0.95)

def test_proto_binary_serialization():
    req = retrieval_pb2.RetrieveRequest(
        query_text="Serialization check",
        caller_role="HR-Admin",
        top_k_candidates=10,
    )
    serialized = req.SerializeToString()
    assert isinstance(serialized, bytes)

    deserialized = retrieval_pb2.RetrieveRequest()
    deserialized.ParseFromString(serialized)
    assert deserialized.query_text == "Serialization check"
    assert deserialized.caller_role == "HR-Admin"
    assert deserialized.top_k_candidates == 10
