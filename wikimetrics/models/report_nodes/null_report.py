from report import ReportLeaf


class NullReport(ReportLeaf):
    """
    Report that returns an empty result.
    """
    def run(self):
        return {}
