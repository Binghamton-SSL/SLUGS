from django.http import HttpResponse
from .render import Render


class RenderPDF(Render):

    params: dict = None
    template: str = None
    email: bool = False
    to: str = None


class RenderPDFMixin(RenderPDF):
    def get(self, request, *args, **kwargs):
        if True:
            self.added_context["request"] = request
            return Render.render(self.template_name, self.get_context_data())
        else:
            return HttpResponse("Email")
