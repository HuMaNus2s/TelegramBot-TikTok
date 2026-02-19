import hashlib
import time
import os
def hash_ext(filename: str, hash_length: int = 12) -> str:
    """
    ### return
     
    **hash+ext:** filename.txt -> eqwe3d2xcfv4.txt
    """
    if not filename:
        return f"{int(time.time())}{os.path.splitext(filename)[1]}"
    
    base, ext = os.path.splitext(filename)
    salt = f"{time.perf_counter():.7f}"
    digest = hashlib.sha256((base + salt).encode()).hexdigest()[:hash_length]
    return f"{digest}{ext}"