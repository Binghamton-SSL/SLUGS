from django.shortcuts import render

# Create your views here.
def index(request):
    if not request.user.is_authenticated:
        return redirect('%s?next=%s' % (reverse('auth:login'), request.path))
    return render(request, 'training/index.html', {})
