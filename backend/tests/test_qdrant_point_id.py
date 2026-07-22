import uuid

from app.services.qdrant_service import build_point_id


def test_build_point_id_is_deterministic():
    id_1 = build_point_id("Documents/hr/leave_policy.txt", 1, 3)
    id_2 = build_point_id("Documents/hr/leave_policy.txt", 1, 3)

    assert id_1 == id_2


def test_build_point_id_differs_for_different_chunks():
    id_a = build_point_id("Documents/hr/leave_policy.txt", 1, 0)
    id_b = build_point_id("Documents/hr/leave_policy.txt", 1, 1)
    id_c = build_point_id("Documents/hr/other_policy.txt", 1, 0)

    assert id_a != id_b
    assert id_a != id_c
    assert id_b != id_c


def test_build_point_id_is_a_valid_uuid_string():
    point_id = build_point_id("Documents/hr/leave_policy.txt", 1, 0)
    parsed = uuid.UUID(point_id)

    assert str(parsed) == point_id


def test_reindexing_same_document_produces_same_ids():
    first_pass = [build_point_id("Documents/it/vpn_setup_guide.txt", 1, i) for i in range(5)]
    second_pass = [build_point_id("Documents/it/vpn_setup_guide.txt", 1, i) for i in range(5)]

    assert first_pass == second_pass
