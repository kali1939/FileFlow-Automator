# 📂 core/organizer.py
import shutil
from pathlib import Path
import logging
from datetime import datetime

class FileOrganizer:
    def __init__(self, config):
        self.config = config
        self.ensure_folders()

    def ensure_folders(self):
        """Crea las carpetas de categorías si no existen"""
        for category in self.config["categories"].keys():
            Path(category).mkdir(exist_ok=True)
        Path("Otros").mkdir(exist_ok=True)

    def process_file(self, file_path):
        """Procesa un archivo individual"""
        file = Path(file_path)
        if not file.is_file():
            raise ValueError(f"{file_path} no es un archivo válido")

        dest_folder = self.classify_file(file)
        dest_path = Path(dest_folder) / file.name

        # Manejamos colisiones de nombres
        counter = 1
        while dest_path.exists():
            stem = file.stem
            suffix = file.suffix
            dest_path = Path(dest_folder) / f"{stem}_{counter}{suffix}"
            counter += 1

        shutil.move(str(file), str(dest_path))
        
        action = {
            "archivo": file.name,
            "origen": str(file.parent),
            "destino": str(dest_path.parent),
            "fecha": datetime.now().isoformat(),
            "accion": "movido"
        }
        
        logging.info(f"Organizado: {file.name} -> {dest_folder}")
        return action

    def classify_file(self, file):
        """Clasifica el archivo según su extensión"""
        extension = file.suffix.lower()
        for category, extensions in self.config["categories"].items():
            if extension in extensions:
                return category
        return "Otros"