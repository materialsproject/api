from maggma.api.resource import HintScheme


class TasksHintScheme(HintScheme):
    """
    Hint scheme for the tasks endpoint.
    """

    def generate_hints(self, query):

        hints = {"hint": {}}

        if query["criteria"] == {}:
            hints["hint"]["_id"] = 1

        return hints
