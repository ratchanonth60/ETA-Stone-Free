from .forms import SearchForm


def search_form(request):
    """
    Ensure that the search form is available site wide
    """
    return {"search_form": SearchForm(request.GET)}
