class GraderException(Exception):
    def __init__(self):
        pass


class ValidationError(Exception):
    def __init__(self, field):
        Exception.__init__(self)
        self.field = field
        self.msg = "Unvalid field in grader_payload:"+str(field)


class EmptyPayload(Exception):
    def __init__(self, field):
        Exception.__init__(self)
        self.field = field
        self.msg = "Unvalid field in grader_payload:Empty "+str(field)

