from maggma.api.resource import HintScheme


class SummaryHintScheme(HintScheme):
    """
    Hint scheme for the summary endpoint.
    """

    def generate_hints(self, query):

        if "nelements" in query["criteria"]:
            return {"hint": {"nelements": 1}}
        elif "has_props" in query["criteria"]:
            return {"hint": {"has_props": 1}}
        else:
            return {"hint": {}}
