# 📂 core/duplicates.py
import hashlib
from pathlib import Path
from collections import defaultdict

class DuplicateFinder:
    def find(self, directory):
        """Encuentra archivos duplicados por contenido (hash MD5)"""
        hashes = defaultdict(list)
        
        for file_path in Path(directory).rglob("*"):
            if file_path.is_file():
                try:
                    file_hash = self._hash_file(file_path)
                    hashes[file_hash].append(str(file_path))
                except (IOError, PermissionError):
                    continue

        return [files for files in hashes.values() if len(files) > 1]

    def _hash_file(self, file_path, block_size=65536):
        """Genera hash MD5 para un archivo"""
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            for block in iter(lambda: f.read(block_size), b''):
                hasher.update(block)
        return hasher.hexdigest()