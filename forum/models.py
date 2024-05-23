from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from hitcount.models import HitCount
from django.contrib.contenttypes.fields import GenericRelation
from django.shortcuts import reverse
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

CustomUser = get_user_model()


class Post(models.Model):
    class Meta:
        verbose_name = "Post"
        verbose_name_plural = "Posts"
        db_table = "posts"

    post_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=256)
    slug = models.SlugField(max_length=256, unique=True, blank=True)
    text = models.TextField(max_length=40000)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)
    votes = models.IntegerField(default=0)
    hit_count_generic = GenericRelation(
        HitCount,
        object_id_field="object_pk",
        related_query_name="hit_count_generic_relation",
    )

    def save(self, *args, **kwargs):
        """
        Save the post and perform validation checks before saving. If the slug is not set, generate it from the title.
        """
        if not self.slug:
            self.slug = slugify(self.title)
        self.full_clean()
        super(Post, self).save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        self.text = "[deleted]"
        self.is_deleted = True
        self.save()
        return self

    def __str__(self):
        return self.title

    def get_url(self):
        return reverse("post_detail", kwargs={"slug": self.slug})

    def get_comments(self):
        """
        Get all comments for this post in descending order of creation
        :return:  QuerySet of Comment objects
        """
        return Comment.objects.filter(post=self).order_by("-created_at")

    def clean(self):
        cleaned_data = super().clean()
        if not self.title:
            raise ValidationError(_("Title field is required."), code="invalid")
        if len(self.title) > 256:
            raise ValidationError(_("Title cannot exceed 256 characters."), code="invalid")
        if not self.text:
            raise ValidationError(_("Text field is required."), code="invalid")
        if len(self.text) > 40000:
            raise ValidationError(_("Text cannot exceed 40000 characters."), code="invalid")
        return cleaned_data
