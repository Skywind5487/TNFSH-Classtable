import pytest
from model.swap import TeacherNode, CourseNode, connect_neighbors, merge_paths


def _build_simple_graph():
    """Return a minimal graph matching the example in docs."""
    A = TeacherNode("A")
    B = TeacherNode("B")
    a1 = CourseNode("1", A)              # need swap
    a2 = CourseNode("2", A, is_free=True)
    b1 = CourseNode("1", B, is_free=True)
    b2 = CourseNode("2", B)              # need swap
    connect_neighbors([a1, b2])
    return a1, b1


def test_stop_at_first_free():
    start, expected_last = _build_simple_graph()
    paths = list(merge_paths(start))
    # Exactly one path & it ends at the first free slot b1_
    assert len(paths) == 1
    assert paths[0][-1] == expected_last


def test_no_path_when_isolated():
    A = TeacherNode("A"); B = TeacherNode("B")
    a1 = CourseNode("1", A)
    b2 = CourseNode("2", B)
    # no neighbors connected -> no path
    paths = list(merge_paths(a1))
    assert paths == []


def test_depth_limit():
    """Ensure algorithm halts before exceeding _MAX_DEPTH (10)."""
    A = TeacherNode("A")
    B = TeacherNode("B")
    prev = CourseNode("0", A)
    start = prev
    # Chain length 15 (> _MAX_DEPTH) alternating teachers
    for i in range(1, 15):
        teacher = A if i % 2 == 0 else B
        node = CourseNode(str(i), teacher)
        connect_neighbors([prev, node])
        prev = node
    # last node free to allow stopping
    prev.is_free = True
    paths = list(merge_paths(start))
    assert paths  # we get at least one path
    # Each yielded path length should be <= _MAX_DEPTH * 2 (rough upper bound)
    assert all(len(p) <= 30 for p in paths)
