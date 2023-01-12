class Perference():
    def __init__(self, bedroom_from=None, bedroom_to=None, bathroom_from=None, bathroom_to=None, aggregated_type=None, max_posted_days=None):
        self.bedroom_from = bedroom_from
        self.bedroom_to = bedroom_to
        self.bathroom_from = bathroom_from
        self.bathroom_to = bathroom_to
        self.aggregated_type = aggregated_type
        self.max_posted_days = max_posted_days