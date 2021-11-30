from mp_api.routes.materials.hint_scheme import MaterialsHintScheme


def test_materials_hint_scheme():
    scheme = MaterialsHintScheme()
    assert scheme.generate_hints({"criteria": {"nelements": 3}}) == {
        "hint": {"nelements": 1}
    }
