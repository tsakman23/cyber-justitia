"""
Test cases for forum-related forms.

Author: Ionut-Valeriu Facaeru
"""

import unittest
from django.test import TestCase
from forum.forms import CreatePostForm, CreateCommentForm


class ForumFormTests(TestCase):
    """
    Test case for forum-related forms.
    """

    def test_valid_post_creation(self):
        """
        TFF1: Test creating a post with valid data.
        """
        form_data = {
            'title': 'Valid Title',
            'text': 'This is a valid text with appropriate length.'
        }
        form = CreatePostForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_post_creation_with_empty_title(self):
        """
        TFF2: Test creating a post with an empty title.
        """
        form_data = {
            'title': '',
            'text': 'This is a valid text with appropriate length.'
        }
        form = CreatePostForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)
        self.assertEqual(form.errors['title'], ['Title field is required.'])

    def test_post_creation_with_empty_text(self):
        """
        TFF3: Test creating a post with empty text.
        """
        form_data = {
            'title': 'Valid Title',
            'text': ''
        }
        form = CreatePostForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('text', form.errors)
        self.assertEqual(form.errors['text'], ['Text field is required.'])

    def test_post_creation_with_title_exceeding_max_length(self):
        """
        TFF4: Test creating a post with a title exceeding the maximum length.
        """
        form_data = {
            'title': 'a' * 257,
            'text': 'This is a valid text with appropriate length.'
        }
        form = CreatePostForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)
        self.assertEqual(form.errors['title'], ['Title cannot exceed 256 characters.'])

    def test_post_creation_with_text_exceeding_max_length(self):
        """
        TFF5: Test creating a post with text exceeding the maximum length.
        """
        form_data = {
            'title': 'Valid Title',
            'text': 'a' * 40001
        }
        form = CreatePostForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('text', form.errors)
        self.assertEqual(form.errors['text'], ['Text cannot exceed 40000 characters.'])

    def test_valid_comment_creation(self):
        """
        TFF6: Test creating a comment with valid data.
        """
        form_data = {
            'comment': 'This is a valid comment with appropriate length.'
        }
        form = CreateCommentForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_comment_creation_with_empty_comment(self):
        """
        TFF7: Test creating a comment with an empty comment field.
        """
        form_data = {
            'comment': ''
        }
        form = CreateCommentForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('comment', form.errors)
        self.assertEqual(form.errors['comment'], ['Comment field is required.'])

    def test_comment_creation_with_comment_exceeding_max_length(self):
        """
        TFF8: Test creating a comment with text exceeding the maximum length.
        """
        form_data = {
            'comment': 'a' * 40001
        }
        form = CreateCommentForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('comment', form.errors)
        self.assertEqual(form.errors['comment'], ['Comment cannot exceed 40000 characters.'])


if __name__ == '__main__':
    unittest.main()