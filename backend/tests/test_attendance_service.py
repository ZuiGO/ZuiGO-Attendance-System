"""Unit tests for Attendance Verification mathematics and Anti-Proxy defense logic."""

import pytest
from app.services.attendance_service import (
    calculate_cosine_similarity,
    calculate_haversine_distance_meters,
)


def test_cosine_similarity_identical_vectors():
    """Identical vectors must return cosine similarity of 1.0."""
    vec = [0.12, 0.45, -0.67, 0.89, -0.23]
    similarity = calculate_cosine_similarity(vec, vec)
    assert pytest.approx(similarity, abs=1e-5) == 1.0


def test_cosine_similarity_orthogonal_vectors():
    """Orthogonal vectors must return cosine similarity of 0.0."""
    vec_a = [1.0, 0.0, 0.0]
    vec_b = [0.0, 1.0, 0.0]
    similarity = calculate_cosine_similarity(vec_a, vec_b)
    assert pytest.approx(similarity, abs=1e-5) == 0.0


def test_cosine_similarity_slight_variation():
    """Slight facial expression variations (e.g. smile/blink) should yield high similarity (> 0.90)."""
    baseline = [0.2, 0.5, 0.8, -0.3, 0.1]
    live_scan = [0.21, 0.49, 0.81, -0.29, 0.11]  # Micro variations
    similarity = calculate_cosine_similarity(baseline, live_scan)
    assert similarity > 0.99


def test_cosine_similarity_different_person():
    """Different person embeddings must yield low similarity (< 0.50)."""
    person_a = [0.8, -0.5, 0.2, 0.7, -0.1]
    person_b = [-0.7, 0.6, -0.3, -0.5, 0.8]
    similarity = calculate_cosine_similarity(person_a, person_b)
    assert similarity < 0.0  # Strongly dissimilar


def test_haversine_distance_zero():
    """Same coordinates should return 0 meters."""
    dist = calculate_haversine_distance_meters(28.5355, 77.3910, 28.5355, 77.3910)
    assert pytest.approx(dist, abs=0.1) == 0.0


def test_haversine_distance_known_points():
    """Calculates distance between two known points (e.g. ~111km per latitude degree)."""
    # 0.001 degree of latitude is roughly 111.19 meters
    dist = calculate_haversine_distance_meters(28.5355, 77.3910, 28.5365, 77.3910)
    assert 110.0 <= dist <= 112.0
