# 📂 main.py - Versión Tkinter
import argparse
import logging
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from core.organizer import FileOrganizer
from core.duplicates import DuplicateFinder
from core.reporter import ReportGenerator
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import json
import sys

class FileFlowApp:
    def __init__(self, root):
        self.root = root
        self.config = self.load_config()
        self.setup_ui()
        self.setup_logging()
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('fileflow.log'),
                logging.StreamHandler()
            ]
        )
    
    def load_config(self):
        try:
            with open('config/settings.json') as f:
                return json.load(f)
        except FileNotFoundError:
            logging.warning("Config no encontrada, usando valores por defecto")
            return {
                "categories": {
                    "Imágenes": [".jpg", ".png", ".jpeg"],
                    "Documentos": [".pdf", ".docx", ".xlsx"],
                    "Audios": [".mp3", ".wav"]
                },
                "report_path": "reportes"
            }
    
    def setup_ui(self):
        self.root.title("FileFlow Automator")
        self.root.geometry("800x600")
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Controles
        ttk.Label(main_frame, text="Carpeta a organizar:").grid(row=0, column=0, sticky=tk.W)
        self.folder_path = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.folder_path, width=50).grid(row=0, column=1)
        ttk.Button(main_frame, text="Examinar", command=self.browse_folder).grid(row=0, column=2)
        
        self.check_duplicates = tk.BooleanVar()
        ttk.Checkbutton(main_frame, text="Buscar duplicados", variable=self.check_duplicates).grid(row=1, column=1, sticky=tk.W)
        
        self.check_report = tk.BooleanVar(value=True)
        ttk.Checkbutton(main_frame, text="Generar reporte Excel", variable=self.check_report).grid(row=2, column=1, sticky=tk.W)
        
        # Consola de salida
        self.output_console = scrolledtext.ScrolledText(main_frame, height=20, width=90)
        self.output_console.grid(row=3, column=0, columnspan=3, pady=10)
        
        # Botones de acción
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=4, column=0, columnspan=3, pady=10)
        
        ttk.Button(btn_frame, text="Ejecutar", command=self.run_organizer).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Modo Monitor", command=self.start_monitor).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Salir", command=self.root.quit).pack(side=tk.RIGHT, padx=5)
    
    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path.set(folder)
            self.log(f"Carpeta seleccionada: {folder}")
    
    def log(self, message):
        self.output_console.insert(tk.END, message + "\n")
        self.output_console.see(tk.END)
        logging.info(message)
    
    def run_organizer(self):
        folder = self.folder_path.get()
        if not folder:
            messagebox.showerror("Error", "Selecciona una carpeta primero")
            return
        
        try:
            organizer = FileOrganizer(self.config)
            duplicate_finder = DuplicateFinder()
            reporter = ReportGenerator(self.config["report_path"])
            actions = []
            
            for file in Path(folder).glob("*"):
                if file.is_file():
                    action = organizer.process_file(str(file))
                    actions.append(action)
                    self.log(f"Procesado: {file.name} -> {action['destino']}")
            
            if self.check_duplicates.get():
                duplicates = duplicate_finder.find(folder)
                dup_count = len(duplicates)
                self.log(f"Archivos duplicados encontrados: {dup_count}")
                messagebox.showinfo("Duplicados", f"Se encontraron {dup_count} archivos duplicados")
            
            if self.check_report.get():
                report_path = reporter.generate(actions)
                self.log(f"Reporte generado: {report_path}")
                messagebox.showinfo("Éxito", f"Reporte guardado en:\n{report_path}")
                
        except Exception as e:
            self.log(f"ERROR: {str(e)}")
            messagebox.showerror("Error", str(e))
    
    def start_monitor(self):
        folder = self.folder_path.get()
        if not folder:
            messagebox.showerror("Error", "Selecciona una carpeta primero")
            return
        
        self.log(f"Iniciando monitorización de: {folder}")
        organizer = FileOrganizer(self.config)
        event_handler = FileHandler(organizer)
        observer = Observer()
        observer.schedule(event_handler, folder, recursive=True)
        observer.start()
        
        # Guardar referencia para poder detenerlo
        self.monitor_observer = observer
        self.monitor_btn = ttk.Button(self.root, text="Detener Monitor", command=lambda: self.stop_monitor(observer))
        self.monitor_btn.pack()
    
    def stop_monitor(self, observer):
        observer.stop()
        observer.join()
        self.log("Monitorización detenida")
        self.monitor_btn.destroy()

class FileHandler(FileSystemEventHandler):
    def __init__(self, organizer):
        self.organizer = organizer
    
    def on_modified(self, event):
        if not event.is_directory:
            try:
                self.organizer.process_file(event.src_path)
                logging.info(f"Archivo procesado automáticamente: {event.src_path}")
            except Exception as e:
                logging.error(f"Error al procesar {event.src_path}: {str(e)}")

def cli_mode(config, folder_path, check_duplicates, generate_report):
    organizer = FileOrganizer(config)
    duplicate_finder = DuplicateFinder()
    reporter = ReportGenerator(config["report_path"])
    
    actions = []
    for file in Path(folder_path).glob("*"):
        if file.is_file():
            action = organizer.process_file(str(file))
            actions.append(action)
            logging.info(f"Procesado: {file.name} -> {action['destino']}")

    if check_duplicates:
        duplicates = duplicate_finder.find(folder_path)
        logging.info(f"Duplicados encontrados: {len(duplicates)}")

    if generate_report:
        reporter.generate(actions)
        logging.info(f"Reporte generado en {config['report_path']}")

def monitor_mode(config, folder_path):
    organizer = FileOrganizer(config)
    event_handler = FileHandler(organizer)
    observer = Observer()
    observer.schedule(event_handler, folder_path, recursive=True)
    
    logging.info(f"👀 Monitoreando {folder_path}... (Presiona Ctrl+C para detener)")
    observer.start()
    try:
        while True:
            pass
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FileFlow Automator")
    parser.add_argument("folder", nargs="?", help="Carpeta a organizar")
    parser.add_argument("--monitor", action="store_true", help="Modo monitorización")
    parser.add_argument("--duplicates", action="store_true", help="Buscar duplicados")
    parser.add_argument("--report", action="store_true", help="Generar reporte Excel")
    
    args = parser.parse_args()

    if args.folder or args.monitor or args.duplicates or args.report:
        config = load_config()
        if args.monitor:
            if not args.folder:
                logging.error("Debes especificar una carpeta con --monitor")
                sys.exit(1)
            monitor_mode(config, args.folder)
        elif args.folder:
            cli_mode(config, args.folder, args.duplicates, args.report)
    else:
        root = tk.Tk()
        app = FileFlowApp(root)
        root.mainloop()