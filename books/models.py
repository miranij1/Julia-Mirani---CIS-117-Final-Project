"""
Database Models for the Project Gutenberg App.

This module for the Project Gutenberg Django application defines the database models used to store book information and word frequency data.
- Book: Represents a book from Project Gutenberg
- WordFrequency: Stores individual word frequencies for each book

"""

from django.db import models

class Book(models.Model):
    """
    Represents a single book from Project Gutenberg.
    This model stores basic info about each boon including its title and the URL where it was fetched from Project Gutenberg.

    Attributes: 
        title (str): The title of the book.
        gutenberg_url (str): The URL of the book on Project Gutenberg.

    """

    #Book title - unique to avoid duplicates
    title = models.CharField(max_length=300, unique=True)
    #URL from Project Gutenberg where the book was fetched
    gutenberg_url = models.URLField(blank=True, null=True)

    def __str__(self):
        """
        String represents the book object
        Returns:
            str: The title of the book.
        """
        return self.title


class WordFrequency(models.Model):
    """
    Stores a word and its frequency for a given book.

    This model creates a relationship between books and their most frequent words.
    Each record represents one word and how many times it appearsin a particular book.

    Attributes:
        book (Book): Foreign key linking to the Book model.
        word (str): The word being tracked.
        frequency (int): The number of times the word appears in the book.
    """

    #Foreign key to the Book model
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="word_frequencies")
    #The word itself
    word = models.CharField(max_length=100)
    frequency = models.IntegerField()

    class Meta:
        """
        Metadata options for the WordFrequency model.
        - unique_together: Esnures each word is unique per book.
        - ordering: Default ordering by frequency in descending order.
        """

        #Prevent dubplicate word entries for the same book
        unique_together = ('book', 'word')
        #Default ordering by frequency (highest first)
        ordering = ['-frequency']

    def __str__(self):
        """
        String representation of the WordFrequency object.

        Returns:
            str: A formatted string showing the word, its frequency, and the associated book title.
        """
        return f"{self.word} ({self.frequency}) in {self.book.title}"

