"""
Project Gutenberg Word Explorer
A Django web application that grabs books from Project Gutenberg, analyzes word frequency, and stores results in a local database.
Users can serch for books by title or load new books with a URL.
Author: Julia Mirani
Date: 12/04/2025
Course: CIS 117
"""

from django.shortcuts import render
from django.db import transaction
from collections import Counter
from urllib.request import urlopen
from urllib.error import URLError, HTTPError

from .models import Book, WordFrequency

# Set of common words to explude from frequency counter
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
    "now", "how", "where", "why", "who", "what",  # ADDED THESE
    
    # common verbs (ADD THIS SECTION)
    "go", "went", "come", "came", "said", "took", "get", "got",
    "make", "made", "see", "saw", "know", "take", "give", "gave",

    # quantifiers
    "all", "any", "some", "no", "not",
    "away",  # ADDED THIS

    # common numbers
    "one", "two", "three",
}


def clean_text_to_words(text: str) -> list[str]:
    """
    Process raw text into a list of cleaned, meaningful words.
    This function converts text to lowercase, removes punctuation, filters out stopwards, and returns only alphabetic words longer than one character.
    Args: 
        text (str): The raw text to process.
    Returns: 
        list[str]: A list of cleaned words.
    """
    #Convert all text to lowercase for consistent processing
    text = text.lower()

    #Define characters to replace with spaces
    chars_to_replace = ",.;:!?\"'()[]{}-_*/\\\n\r\t"
    for ch in chars_to_replace:
        text = text.replace(ch, " ")

    #Split text into words
    words = text.split()

    filtered = [
        w for w in words
        if w.isalpha() and w not in STOPWORDS and len(w) > 1
    ]
    return filtered


def fetch_gutenberg_text(url: str) -> str:
    """
    Download the full text of a book from Project Gutenberg
    Args:
        url (str): The URL of the Project Gutenberg text file.
    Returns:
        str: The full text of the book.
    Raises:
        RuntimeError: If there is an error fetching the URL.
    """
    try:
        #Open the URL and read the content
        response = urlopen(url)
        raw_bytes = response.read()
        #Decode bytes to string
        # Most Gutenberg texts are UTF-8
        return raw_bytes.decode("utf-8", errors="ignore")
    except (HTTPError, URLError) as e:
        #Raise a more descriptive error is download fails 
        raise RuntimeError(f"Error fetching URL: {e}")


def extract_title_from_gutenberg(text: str) -> str:
    """
    Extract the title of a Project Gutenberg book from its full text.Extract the book titel from Project Gutenberg text.
    Args:
        text (str): The full text of the book.
    Returns:
        str: The extracted title, or "Unknown Title" if not found.
    """
    #Search through the beginning of the text line by line
    for line in text.splitlines():
        if line.lower().startswith("title:"):
            # Take everything after "Title:"
            return line.split(":", 1)[1].strip()
    #Return default title if no "Title:" feils is found
    return "Unknown Title"


def compute_top_words(text: str, limit: int = 10) -> list[tuple[str, int]]:
    """
    Analyze the text to compute the most common words, excluding stopwords.
    Args: 
        text (str): The full text to analyze.
        limit (int): The number of top words to return (default: 10).
    Returns:
        list[tuple[str, int]]: A list of tuples containing the top words and their frequencies.
    """
    words = clean_text_to_words(text)
    counts = Counter(words)

    return counts.most_common(limit)


def book_search_view(request):
    """
    Main view function for the Project Gutenberg Word Explorer.

    This View handles two main operations:
    1. Searching for a book by title in the local database
    2. Loadinhg a new book from Project Gutenberg URL and storing it in the database

    Args: 
        requestL Django HttpRequest object containing user input
    Returns: 
        HttpResponse: Rendered HTML page with search results or error messages.
    """

    #Initialize context dictionary with default values
    context = {
        "title_query": "",
        "url_query": "",
        "book": None,
        "word_frequencies": None,
        "message": "",
        "error": "",
    }

    #Only process if the form was submitted via POST
    if request.method == "POST":
        #Handle search by title in local database
        if "search_title" in request.POST:
            #Get the titel from the form and remove extra whitespace
            title = request.POST.get("title", "").strip()
            context["title_query"] = title

            if not title:
                context["error"] = "Please enter a book title."
            else:
                try:
                    #Search for a book in database (case-insensitive exact match)
                    book = Book.objects.get(title__iexact=title)
                    #Get the top 10 word frequencies for the book
                    word_freqs = book.word_frequencies.all()[:10]
                    if not word_freqs:
                        context["message"] = (
                            "Book found in database, but no word frequencies stored."
                        )
                    context["book"] = book
                    context["word_frequencies"] = word_freqs
                except Book.DoesNotExist:
                    #Book not found in database
                    context["message"] = (
                        "Book not found in local database. "
                        "If this is a Project Gutenberg book, paste its text URL below to add it."
                    )

        #Handle loading a new book from Project Gutenberg URL
        elif "load_url" in request.POST:
            #Get the URL from the form and remove extra whitespace
            url = request.POST.get("url", "").strip()
            context["url_query"] = url
            if not url:
                context["error"] = "Please enter a Project Gutenberg text URL."
            else:
                try:
                    #Download the book text from Project Gutenberg
                    full_text = fetch_gutenberg_text(url)
                    #Extract the title from the Gutenberg metadata
                    title = extract_title_from_gutenberg(full_text)
                    #Analyze the text and get top 10 most frequent words
                    top_words = compute_top_words(full_text, limit=10)

                    # Save book and word frequencies to database
                    #Use atomic transaction to ensure data consistency 
                    with transaction.atomic():
                        book, created = Book.objects.get_or_create(
                            title=title,
                            defaults={"gutenberg_url": url},
                        )
                        #Update URL if book already exists
                        if not created:
                            book.gutenberg_url = url
                            book.save()

                        # Clear old frequencies, then insert new ones
                        WordFrequency.objects.filter(book=book).delete()
                        
                        #Create new word frequency records 
                        for word, freq in top_words:
                            WordFrequency.objects.create(
                                book=book,
                                word=word,
                                frequency=freq,
                            )

                    #Update context with the book and its word frequencies 
                    context["book"] = book
                    context["word_frequencies"] = (
                        WordFrequency.objects.filter(book=book)[:10]
                    if created:
                        context["message"] = (
                            f"Loaded '{book.title}' from Project Gutenberg and added to the database."
                        )
                    else:
                        context["message"] = (
                            f"Updated '{book.title}' in the database with new word frequencies."
                        )

                except RuntimeError as e:
                    #Handle URL fetch errors
                    context["error"] = "Book was not found. Please check the URL and try again."
                except Exception as e:
                    #Handle any other unexpected errors
                    context["error"] = "Book was not found. Please check the Project Gutenberg URL is correct."

            
    #Render the template with the context data
    return render(request, "books/book_search.html", context)

