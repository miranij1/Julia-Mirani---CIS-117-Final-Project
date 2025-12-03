from django.db import models

class Book(models.Model):
    """
    Represents a single book from Project Gutenberg.
    We’ll store the title and (optionally) the URL.
    """
    title = models.CharField(max_length=300, unique=True)
    gutenberg_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.title


class WordFrequency(models.Model):
    """
    Stores a word and its frequency for a given book.
    """
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="word_frequencies")
    word = models.CharField(max_length=100)
    frequency = models.IntegerField()

    class Meta:
        unique_together = ('book', 'word')
        ordering = ['-frequency']

    def __str__(self):
        return f"{self.word} ({self.frequency}) in {self.book.title}"

