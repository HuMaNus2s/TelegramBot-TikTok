async def is_zip(buffer):
    """
    Checks if buffer is a ZIP archive using magic bytes.
    Works with bytes and io.BytesIO.
    """
    if isinstance(buffer, bytes):
        header = buffer[:4]
    elif hasattr(buffer, 'getvalue'):
        header = buffer.getvalue()[:4]
    elif hasattr(buffer, 'read'):
        pos = buffer.tell()
        header = buffer.read(4)
        buffer.seek(pos)
    else:
        raise TypeError(f"Unsupported buffer type: {type(buffer)}")

    return header == b'PK\x03\x04'