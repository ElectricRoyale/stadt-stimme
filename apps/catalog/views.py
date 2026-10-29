from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET

from apps.catalog.search import MAX_HITS, MIN_QUERY_LENGTH, search


@require_GET
def search_page(request: HttpRequest) -> HttpResponse:
    query = request.GET.get("q", "").strip()[:100]
    hits = search(query)
    return render(
        request,
        "catalog/search.html",
        {
            "query": query,
            "hits": hits,
            "too_short": 0 < len(query) < MIN_QUERY_LENGTH,
            "capped": len(hits) == MAX_HITS,
        },
    )
