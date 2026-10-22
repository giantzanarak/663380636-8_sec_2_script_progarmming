"""Creates data/dummy_report.pdf, the attachment used by Tasks 2 and 4."""
import os

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "dummy_report.pdf")

os.makedirs(os.path.dirname(PATH), exist_ok=True)
c = canvas.Canvas(PATH, pagesize=A4)
width, height = A4
c.setFont("Helvetica-Bold", 18)
c.drawString(2.5 * cm, height - 3 * cm, "Daily Report")
c.setFont("Helvetica", 12)
for i, line in enumerate([
    "This is a dummy report attached by the Email & SMS automator.",
    "Week 12 - LabX BASIC: Automating Communications (Email & SMS)",
]):
    c.drawString(2.5 * cm, height - 4.2 * cm - i * 0.7 * cm, line)
c.save()
print(f"Created {PATH}")
