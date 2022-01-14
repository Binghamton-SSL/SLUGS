import ast
from django.contrib.auth.models import Group
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from PyPDF4 import PdfFileWriter, PdfFileReader
from jsignature.utils import draw_signature
import os
from datetime import datetime


def processAutoSignForm(paperworkForm, user):
    c = canvas.Canvas(f"signed_copy-{user.pk}.pdf")
    pages = ast.literal_eval(paperworkForm.form.auto_sign_layout)
    for page in pages:
        for element in page:
            if element["type"] == "Text":
                c.setFont("Times-Roman", element["font_size"])
                c.drawString(
                    element["x"] * inch, element["y"] * inch, eval(element["text"])
                )
            elif element["type"] == "Signature":
                sig_image = ImageReader(draw_signature(user.signature))
                (sig_width, sig_height) = sig_image.getSize()
                img_height = (element["width"] / (sig_width / sig_height)) * inch
                c.drawImage(
                    sig_image,
                    element["x"] * inch,
                    ((element["y"] * inch) - img_height),
                    width=element["width"] * inch,
                    height=img_height,
                    mask="auto",
                )
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

    with open(
        f"{paperworkForm.form}-{user.last_name}_{user.first_name}-signed.pdf", "wb+"
    ) as outputStream:
        output_file.write(outputStream)
        paperworkForm.pdf.save(
            f'{paperworkForm.form}-{user.last_name}_{user.first_name}_{datetime.now().strftime("%H:%M:%S")}-signed.pdf',
            outputStream,
        )
        paperworkForm.uploaded = datetime.now()
        paperworkForm.save()

    os.remove(f"signed_copy-{user.pk}.pdf")
    os.remove(f"{paperworkForm.form}-{user.last_name}_{user.first_name}-signed.pdf")


def auto_place_group_user(user):
    if user.paperworkform_set.filter(processed=False, form__required_for_payroll=True):
        if user.groups.filter(name="Awaiting Paperwork").count() == 0:
            Group.objects.get(name="Awaiting Paperwork").user_set.add(user)
    elif user.paperworkform_set.filter(processed=False, form__required_for_payroll=True, form__required_for_employment=True).count() == 0:
        if user.groups.filter(name="Awaiting Paperwork").count():
            Group.objects.get(name="Awaiting Paperwork").user_set.remove(user)

    if user.paperworkform_set.filter(processed=False, form__required_for_employment=True):
        if user.groups.filter(name="Cannot Work").count() == 0:
            Group.objects.get(name="Cannot Work").user_set.add(user)
            Group.objects.get(name="Awaiting Paperwork").user_set.add(user)
    else:
        if user.groups.filter(name="Cannot Work").count():
            Group.objects.get(name="Cannot Work").user_set.remove(user)
