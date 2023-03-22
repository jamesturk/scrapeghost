class ScrapeghostError(Exception):
    pass


class TooManyTokens(ScrapeghostError):
    pass


class MaxCostExceeded(ScrapeghostError):
    pass


class PreprocessorError(ScrapeghostError):
    pass


class BadStop(ScrapeghostError):
    pass


class InvalidJSON(ScrapeghostError):
    pass


class PostprocessingError(ScrapeghostError):
    pass
