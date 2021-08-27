from django.core.mail import EmailMessage
from django.template.loader import get_template


def send_generic_email(
    title,
    subject,
    request,
    included_text="",
    included_html="",
    to=[],
    cc=[],
    bcc=[],
    attachments=[],
):
    template = get_template("utils/components/generic_email.html")
    email_template = template.render(locals())
    email = EmailMessage(
        subject=subject,
        body=email_template,
        from_email="bssl.slugs@binghamtonsa.org",
        to=to,
        cc=cc,
        bcc=bcc,
        reply_to=["bssl@binghamtonsa.org"],
    )
    email.content_subtype = "html"
    for attachment in attachments:
        email.attach_file(attachment)
    email.send()
