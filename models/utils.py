
def single_row(results, message=None):
    """
    Returns a single row from the results.
    Raises an error if there is 0 or >1 rows.
    @param results: queryset.
    @param message: (Optional) Message to include in the exception
                    if there are 0 or >1 results.
    """
    if len(results) != 1:
        if message is None:
            raise Exception('Require 1 row, found %i.' % len(results))
        else:
            raise Exception('%s\nRequire 1 row, found %i' %
                            (message, len(results)))
    return results[0]


def single_row_or_none(results):
    """
    Returns a single row from the results, or None if there are 0 results.
    Raises an exception if there are >1 results.
    """
    if len(results) > 1:
        raise Exception('Require 1 row, found %d' % len(results))
    elif len(results) == 0:
        return None
    return results[0]


def list_to_choices(list):
    """
    Takes a list and returns a list of 2-tuples, useful for the 'choices'
    form field attribute.
    """
    result = []
    for item in list:
        result.append((item, item))
    return result
