import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.setFont("Helvetica", 10)
        self.drawRightString(A4[0]-30, 35, f"Page {self._pageNumber} of {page_count}")

buf = io.BytesIO()
doc = SimpleDocTemplate(buf)
elements = [Paragraph("Hello World", getSampleStyleSheet()['Normal']), Spacer(1, 800), Paragraph("Page 2", getSampleStyleSheet()['Normal'])]
doc.build(elements, canvasmaker=NumberedCanvas)
with open('test_canvas.pdf', 'wb') as f:
    f.write(buf.getvalue())
print("OK")
