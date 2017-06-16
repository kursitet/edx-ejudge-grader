import logging

logger = logging.getLogger('edx-ejudge-grader')


class GraderException(Exception, BaseException):
    def __init__(self, message=None):
        self.msg = "Unknow error. Please inform your supervisor and try again later."
        logger.error(message)


class ValidationError(Exception):
    def __init__(self, field):
        Exception.__init__(self)
        self.field = field
        self.msg = "Unvalid field in grader_payload:" + str(field)
        logger.warning(self.msg)


class EmptyPayload(Exception):
    def __init__(self, field):
        Exception.__init__(self)
        self.field = field
        self.msg = "Unvalid field in grader_payload:Empty " + str(field)
        logger.warning(self.msg)


class SyntaxErrorPayload(Exception):
    def __init__(self, field):
        Exception.__init__(self)
        self.field = field
        self.msg = "Syntax error in grader_payload. Check quotes, brackets, commas."
        logger.warning(self.msg)


class ProhibitedOperatorsError(Exception):
    def __init__(self, command):
        Exception.__init__(self)
        self.field = command
        self.msg = "You are using the forbidden by the conditions of the task command: " + str(command)
        logger.warning(self.msg)


class StudentResponseCompilationError(Exception):
    def __init__(self, message=None):
        self.msg = "Compilation Error. Fix your program and try again."
        logger.warning(self.msg)