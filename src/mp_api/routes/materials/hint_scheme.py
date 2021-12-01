from maggma.api.resource import HintScheme


class MaterialsHintScheme(HintScheme):
    """
    Hint scheme for the materials endpoint.
    """

    def generate_hints(self, query):

        if "nelements" in query["criteria"]:
            return {"hint": {"nelements": 1}}
        else:
            return {"hint": {}}
