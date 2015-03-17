import pprint


def pp(data, ro=False):

    """Format for pretty print."""
    if not ro:
        pprint.pprint(data, indent=4, width=10)
    return pprint.pformat(data, indent=4, width=10)
