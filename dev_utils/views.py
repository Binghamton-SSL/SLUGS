from django.views.generic.base import TemplateView
from django.contrib import messages


# Create your views here.
def merge_dicts(x, y):
    """
    Given two dicts, merge them into a new dict as a shallow copy.
    """
    z = x.copy()
    z.update(y)
    return z


class MultipleFormView(TemplateView):
    """
    View mixin that handles multiple forms / formsets.
    After the successful data is inserted ``self.process_forms`` is called.
    """

    form_classes = {}
    form_instances = {}

    def get_context_data(self, **kwargs):
        context = super(MultipleFormView, self).get_context_data(**kwargs)
        forms_initialized = {"forms": {}}
        for name, obj in self.form_classes.items():
            if "kwargs" not in obj:
                obj["kwargs"] = {}
            if "instance" in obj:
                forms_initialized["forms"][name] = obj["form"](
                    obj["args"] if "args" in obj else None,
                    prefix=name,
                    instance=obj["instance"],
                    **obj["kwargs"],
                )
            else:
                forms_initialized["forms"][name] = obj["form"](
                    obj["args"] if "args" in obj else None, prefix=name, **obj["kwargs"]
                )

        return merge_dicts(context, forms_initialized)

    def post(self, request, **kwargs):
        forms_initialized = {"forms": {}}
        for name, obj in self.form_classes.items():
            if "kwargs" not in obj:
                obj["kwargs"] = {}
            if "args" in obj:
                forms_initialized["forms"][name] = obj["form"](
                    obj["args"],
                    prefix=name,
                    data=request.POST,
                    instance=obj["instance"] if "instance" in obj else None,
                    **obj["kwargs"],
                )
            else:
                if "instance" in obj:
                    forms_initialized["forms"][name] = obj["form"](
                        prefix=name,
                        data=request.POST,
                        instance=obj["instance"],
                        **obj["kwargs"],
                    )
                else:
                    forms_initialized["forms"][name] = obj["form"](
                        prefix=name,
                        data=request.POST,
                        **obj["kwargs"],
                    )
        valid = True
        for form_class in forms_initialized.values():
            if valid is False:
                break
            if type(form_class) is dict:
                valid = all([form_class[form].is_valid() for form in form_class])
            else:
                valid = form_class.is_valid()
        if valid:
            return self.process_forms(forms_initialized)
        else:
            context = merge_dicts(self.get_context_data(), forms_initialized)
            context = self.post_valid_reject(context)
            messages.add_message(
                self.request,
                messages.ERROR,
                "Something is wrong. Make sure you're filling out the form properly.",
            )
            return self.render_to_response(context)

    def process_forms(self, form_instances):
        raise NotImplementedError

    def post_valid_reject(context):
        raise NotImplementedError
