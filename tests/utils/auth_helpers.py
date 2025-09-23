def extract_error(data: dict) -> str:
    
    """
    Universal API error parser.

    This function normalizes different error response formats
    into a plain string message. It is useful in tests to handle
    various response schemas consistently.

    :param data: API response body (typically JSON-decoded).
    :type data: dict
    :return: Extracted error message.
    :rtype: str
    """
    
    if not isinstance(data, dict):
        return str(data)

    if "message" in data:
        return str(data["message"])
    if "detail" in data:
        return str(data["detail"])
    if "error" in data:
        # якщо error = dict → виводимо message
        err = data["error"]
        if isinstance(err, dict) and "message" in err:
            return str(err["message"])
        return str(err)
    if "msg" in data:
        return str(data["msg"])

    return str(data)
