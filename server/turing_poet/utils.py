import hashlib

def hashc(content):
    return hashlib.sha1(hashlib.md5(content.encode()).digest()).hexdigest()[:8]
