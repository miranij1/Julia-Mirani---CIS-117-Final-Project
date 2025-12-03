from django.shortcuts import render
from django.db import transaction
from collections import Counter
from urllib.request import urlopen
from urllib.error import URLError, HTTPError

from .models import Book, WordFrequency


STOPWORDS = {
    # pronouns
    "i", "you", "he", "she", "it", "we", "they",
    "me", "him", "her", "us", "them",
    "my", "your", "yours", "his", "its", "our", "ours", "their", "theirs",

    # articles / determiners
    "a", "an", "the", "this", "that", "these", "those",

    # coordinating conjunctions
    "and", "or", "but", "so", "yet", "for", "nor",

    # subordinating conjunctions
    "because", "although", "since", "while", "as", "if", "when", "though", "which",

    # prepositions
    "in", "on", "at", "by", "to", "from", "of", "off", "out",
    "over", "under", "up", "down", "with", "without", "into",
    "about", "before", "after", "between", "through", "during",

    # auxiliary verbs
    "is", "am", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did",
    "can", "could", "shall", "should", "will", "would",
    "may", "might", "must",

    # adverbs / fillers
    "very", "just", "then", "there", "here", "again", "like",

    # quantifiers
    "all", "any", "some", "no", "not",

    # common numbers
    "one", "two", "three",
}


def clean_text_to_words(text: str) -> list[str]:
    text = text.lower()

    chars_to_replace = ",.;:!?\"'()[]{}-_*/\\\n\r\t"
    for ch in chars_to_replace:
        text = text.replace(ch, " ")

    words = text.split()

    filtered = [
        w for w in words
        if w.isalpha() and w not in STOPWORDS and len(w) > 1
    ]
    return filtered


def fetch_gutenberg_text(url: str) -> str:
    """
    Given a Project Gutenberg URL, download and return the text.
    Raises an exception if something goes wrong.
    """
    try:
        response = urlopen(url)
        raw_bytes = response.read()
        # Most Gutenberg texts are UTF-8
        return raw_bytes.decode("utf-8", errors="ignore")
    except (HTTPError, URLError) as e:
        raise RuntimeError(f"Error fetching URL: {e}")


def extract_title_from_gutenberg(text: str) -> str:
    """
    Try to find a line that starts with 'Title:' in the Gutenberg header.
    If not found, return a generic title.
    """
    for line in text.splitlines():
        if line.lower().startswith("title:"):
            # Take everything after "Title:"
            return line.split(":", 1)[1].strip()
    return "Unknown Title"


def compute_top_words(text: str, limit: int = 10) -> list[tuple[str, int]]:
    words = clean_text_to_words(text)
    counts = Counter(words)

    return counts.most_common(limit)


def book_search_view(request):
    """
    Main view for:
    - Searching by book title in the local database
    - Loading/updating a book by its Project Gutenberg URL
    """
    context = {
        "title_query": "",
        "url_query": "",
        "book": None,
        "word_frequencies": None,
        "message": "",
        "error": "",
    }

    if request.method == "POST":
        # Which button did they click?
        if "search_title" in request.POST:
            # Search by title in local database
            title = request.POST.get("title", "").strip()
            context["title_query"] = title

            if not title:
                context["error"] = "Please enter a book title."
            else:
                try:
                    book = Book.objects.get(title__iexact=title)
                    word_freqs = book.word_frequencies.all()[:10]
                    if not word_freqs:
                        context["message"] = (
                            "Book found in database, but no word frequencies stored."
                        )
                    context["book"] = book
                    context["word_frequencies"] = word_freqs
                except Book.DoesNotExist:
                    context["message"] = (
                        "Book not found in local database. "
                        "If this is a Project Gutenberg book, paste its text URL below to add it."
                    )


        elif "load_url" in request.POST:
            #Load from a Project Gutenberg URL and update database
            url = request.POST.get("url", "").strip()
            context["url_query"] = url
            if not url:
                context["error"] = "Please enter a Project Gutenberg text URL."
            else:
                try:
                    full_text = fetch_gutenberg_text(url)
                    title = extract_title_from_gutenberg(full_text)

                    top_words = compute_top_words(full_text, limit=10)

                    # Save to database atomically
                    with transaction.atomic():
                        book, created = Book.objects.get_or_create(
                            title=title,
                            defaults={"gutenberg_url": url},
                        )
                        if not created:
                            book.gutenberg_url = url
                            book.save()

                        # Clear old frequencies, then insert new ones
                        WordFrequency.objects.filter(book=book).delete()

                        for word, freq in top_words:
                            WordFrequency.objects.create(
                                book=book,
                                word=word,
                                frequency=freq,
                            )

                    context["book"] = book
                    context["word_frequencies"] = (
                        WordFrequency.objects.filter(book=book)[:10]
                    )
                    context["message"] = (
                        f"Loaded '{book.title}' from Project Gutenberg and updated the database."
                    )

                except RuntimeError as e:
                    context["error"] = "Book was not found. Please check the URL and try again."
                except Exception as e:
                    context["error"] = "Book was not found. Please check the Project Gutenberg URL is correct."

            

    return render(request, "books/book_search.html", context)

