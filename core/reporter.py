# 📂 core/reporter.py
import pandas as pd
from pathlib import Path
from datetime import datetime

class ReportGenerator:
    def __init__(self, report_dir="reportes"):
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(exist_ok=True)

    def generate(self, actions):
        """Genera reporte en Excel"""
        df = pd.DataFrame(actions)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.report_dir / f"reporte_{timestamp}.xlsx"
        
        df.to_excel(report_path, index=False)
        return str(report_path)