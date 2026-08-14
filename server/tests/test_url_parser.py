from src.polymarket import parse_polymarket_url


def test_extract_slug_from_canonical_url():
    result = parse_polymarket_url(
        "https://polymarket.com/event/fed-decision-in-october?x=1#top"
    )
    assert result.slug == "fed-decision-in-october"


def test_extract_slug_from_localized_url():
    result = parse_polymarket_url(
        "https://polymarket.com/zh/event/world-cup-winner"
    )
    assert result.slug == "world-cup-winner"
    assert result.normalized_url == (
        "https://polymarket.com/event/world-cup-winner"
    )
