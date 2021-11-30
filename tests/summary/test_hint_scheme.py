from mp_api.routes.summary.hint_scheme import SummaryHintScheme


def test_summary_hint_scheme():
    scheme = SummaryHintScheme()
    assert scheme.generate_hints({"criteria": {"nelements": 3}}) == {
        "hint": {"nelements": 1}
    }
    assert scheme.generate_hints({"criteria": {"has_props": "dos"}}) == {
        "hint": {"has_props": 1}
    }
