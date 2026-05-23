"""
Helper functions for converting moneyline odds to probabilties.
"""


def moneyline_to_prob(moneyline):
    """
    Convert an American moneyline to its implied proability
    
    Examples:
    moneyline_to_prob(-150) -> 0.6
    moneyline_to_prob(+135) -> 0.426
    """
    if moneyline is None:
        return None
    if moneyline < 0:
        return abs(moneyline) / (abs(moneyline) +100)
    else:
        return 100 / (moneyline + 100)
    
def strip_vig(prob_a, prob_b):
    """
    Normalize two implied probabilities so they sum to 1.0,
    removing the bookmaker's margin (vig).
    
    Returns a tuple: (fair_prob_a, fair_prob_b)
    
    Example
        strip_vig(0.60, 04.35) -> (0.580, 0.420)
    """
    if prob_a is None or prob_b is None:
        return (None, None)
    total = prob_a + prob_b
    return (prob_a / total, prob_b / total)