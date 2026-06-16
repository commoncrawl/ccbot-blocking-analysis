import pytest

import quad_class


def test_quad_url():
    tests = [
        ('http://example.com', 'quad://example.com'),
        ('https://example.com', 'quad://example.com'),
        ('http://www.example.com', 'quad://example.com'),
        ('https://www.example.com', 'quad://example.com'),

        ('http://example.com/', 'quad://example.com/'),
        ('http://example.com/foo', 'quad://example.com/foo'),
        ('http://example.com/foo?bar', 'quad://example.com/foo?bar'),

    ]
    crashers = [
        ('', AttributeError),
        ('asdf', AttributeError),
        (None, AttributeError),
        (False, AttributeError),
        ('https:///foo', AttributeError)
    ]

    for t in tests:
        assert quad_class.make_quad_url(t[0]) == t[1], t[0]

    for c in crashers:
        with pytest.raises(c[1]):
            assert quad_class.make_quad_url(c[0])
