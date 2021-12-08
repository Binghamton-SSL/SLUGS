import ast
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from PyPDF4 import PdfFileWriter, PdfFileReader
from jsignature.utils import draw_signature
import os
from datetime import datetime



def processAutoSignForm(paperworkForm, user):
    c = canvas.Canvas(f"signed_copy-{user.pk}.pdf")
    pages = ast.literal_eval(paperworkForm.form.auto_sign_layout)
    for page in pages:
        for element in page:
            if element['type'] == 'Text':
                c.setFont("Times-Roman", element['font_size'])
                c.drawString(element['x']*inch, element['y']*inch, eval(element['text']))
            elif element['type'] == 'Signature':
                c.drawImage(draw_signature(user.signature, as_file=True), element['x']*inch, element['y']*inch, width=element['width']*inch, height=(element['width']/2.5)*inch, mask='auto')
        c.showPage()
    c.save()

    signed_file = PdfFileReader(open(f"signed_copy-{user.pk}.pdf", "rb"))
    input_file = PdfFileReader(open(paperworkForm.form.form_pdf.path, "rb"))
    output_file = PdfFileWriter()
    page_count = input_file.getNumPages()

    for page_number in range(page_count):
        input_page = input_file.getPage(page_number)
        input_page.mergePage(signed_file.getPage(page_number))
        output_file.addPage(input_page)

    with open(f'{paperworkForm.form}-{user.last_name}_{user.first_name}-signed.pdf', "wb+") as outputStream:
        output_file.write(outputStream)
        paperworkForm.pdf.save(f'{paperworkForm.form}-{user.last_name}_{user.first_name}-signed.pdf', outputStream)

    os.remove(f"signed_copy-{user.pk}.pdf")
    os.remove(f'{paperworkForm.form}-{user.last_name}_{user.first_name}-signed.pdf')
