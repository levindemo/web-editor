def decode_bytes_recursively(obj):
    """
    递归地将一个对象（字典、列表）中的 bytes 解码为 utf-8 字符串。
    """
    if isinstance(obj, dict):
        return {k: decode_bytes_recursively(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [decode_bytes_recursively(elem) for elem in obj]
    elif isinstance(obj, bytes):
        return obj.decode('utf-8', errors='ignore') # errors='ignore' 可以避免解码失败
    else:
        return obj