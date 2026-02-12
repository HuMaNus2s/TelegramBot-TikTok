import io

def is_zip(buffer: bytes) -> bool:
    """
    Checks if buffer is a ZIP archive using magic bytes.
    Only supports bytes (as used in process_buffer).
    """
    if not isinstance(buffer, bytes):
        raise TypeError(f"Expected bytes, received {type(buffer)}")
    
    return buffer[:4] == b'PK\x03\x04'