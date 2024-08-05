# -*- coding: utf-8 -*-

class NotEquivalenceError(Exception):
    def __init__(self):
        messages = 'Symbolic reasoning: NOT EQUIVALENT.'
        super(NotEquivalenceError, self).__init__(messages)


class NotSupportedError(Exception):
    def __init__(self, messages: str):
        super(NotSupportedError, self).__init__(f"Not supported feature: {messages}")


class UnknownError(Exception):
    def __init__(self):
        messages = 'Symbolic reasoning: UNKNOWN.'
        super(UnknownError, self).__init__(messages)


class SyntaxError(Exception):
    def __init__(self, messages: str):
        messages = f'{self.__class__.__name__}: {messages}'
        super(SyntaxError, self).__init__(messages)


class CorrelatedQueryError(NotSupportedError):
    def __init__(self, messages: str):
        messages = f'{self.__class__.__name__} {messages}'
        super(CorrelatedQueryError, self).__init__(messages)


class ParserSyntaxError(SyntaxError):
    def __init__(self, messages: str):
        messages = f'{self.__class__.__name__}: cannot parse `{messages}`'
        super(SyntaxError, self).__init__(messages)


class UnknownDatabaseError(SyntaxError):
    def __init__(self, messages: str):
        messages = f'{self.__class__.__name__}: unknown database `{messages}`'
        super(UnknownDatabaseError, self).__init__(messages)


class UnknownColumnError(SyntaxError):
    def __init__(self, messages: str):
        messages = f'{self.__class__.__name__}: unknown column `{messages}`'
        super(UnknownColumnError, self).__init__(messages)
