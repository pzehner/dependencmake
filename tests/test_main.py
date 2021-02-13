from dependen6make.__main__ import get_parser


class TestGetParser:
    def test_get(self):
        """Get a parser."""
        parser = get_parser()
        assert parser is not None
