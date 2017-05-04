class GraderException(Exception, BaseException):
    def __init__(self):
        self.msg = "Unknow error. Please try again latter."


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


class SyntaxErrorPayload(Exception):
    def __init__(self, field):
        Exception.__init__(self)
        self.field = field
        self.msg = "Syntax error in grader_payload. Check quotes, brackets, commas."