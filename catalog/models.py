from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.text import slugify
from hitcount.models import HitCountMixin, HitCount

class Category(models.Model):
    """Модель для категорий предметов коллекции"""
    name = models.CharField(max_length=100, verbose_name="Название")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="URL")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    
    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('category_detail', kwargs={'slug': self.slug})


class CollectibleItem(models.Model, HitCountMixin):
    """Модель для предметов коллекции (монет/марок)"""
    CONDITION_CHOICES = [
        ('UNC', 'Не бывшая в обращении (UNC)'),
        ('AU', 'Почти не бывшая в обращении (AU)'),
        ('XF', 'Отличное состояние (XF)'),
        ('VF', 'Очень хорошее состояние (VF)'),
        ('F', 'Хорошее состояние (F)'),
        ('VG', 'Удовлетворительное состояние (VG)'),
        ('G', 'Плохое состояние (G)'),
    ]
    
    name = models.CharField(max_length=200, verbose_name="Название")
    slug = models.SlugField(max_length=200, unique=True, verbose_name="URL")
    description = models.TextField(verbose_name="Описание")
    issue_date = models.DateField(blank=True, null=True, verbose_name="Дата выпуска")
    country = models.CharField(max_length=100, verbose_name="Страна")
    condition = models.CharField(max_length=3, choices=CONDITION_CHOICES, verbose_name="Состояние")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='items', verbose_name="Категория")
    image = models.ImageField(upload_to='items/', blank=True, null=True, verbose_name="Изображение")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    
    class Meta:
        verbose_name = "Предмет коллекции"
        verbose_name_plural = "Предметы коллекции"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('item_detail', kwargs={'slug': self.slug})


class Comment(models.Model):
    """Модель для комментариев к предметам коллекции"""
    item = models.ForeignKey(CollectibleItem, on_delete=models.CASCADE, related_name='comments', verbose_name="Предмет")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments', verbose_name="Пользователь")
    text = models.TextField(verbose_name="Текст комментария")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    
    class Meta:
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.user.username} - {self.item.name}'


class Vote(models.Model):
    """Модель для голосования пользователей"""
    item = models.ForeignKey(CollectibleItem, on_delete=models.CASCADE, related_name='votes', verbose_name="Предмет")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='votes', verbose_name="Пользователь")
    value = models.BooleanField(default=True, verbose_name="Значение (лайк/дизлайк)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата голосования")
    
    class Meta:
        verbose_name = "Голос"
        verbose_name_plural = "Голоса"
        unique_together = ['item', 'user']
    
    def __str__(self):
        vote_type = "Лайк" if self.value else "Дизлайк"
        return f'{self.user.username} - {vote_type} - {self.item.name}'


class UserCollection(models.Model):
    """Модель для хранения предметов в личной коллекции пользователя"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='collections', verbose_name="Пользователь")
    item = models.ForeignKey(CollectibleItem, on_delete=models.CASCADE, related_name='in_collections', verbose_name="Предмет")
    notes = models.TextField(blank=True, null=True, verbose_name="Заметки")
    added_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")
    
    class Meta:
        verbose_name = "Предмет в коллекции пользователя"
        verbose_name_plural = "Предметы в коллекциях пользователей"
        unique_together = ['user', 'item']
    
    def __str__(self):
        return f'{self.user.username} - {self.item.name}'


class VisitCount(models.Model):
    """Модель для счетчика посещений"""
    date = models.DateField(auto_now_add=True, unique=True, verbose_name="Дата")
    count = models.PositiveIntegerField(default=0, verbose_name="Количество посещений")
    
    class Meta:
        verbose_name = "Статистика посещений"
        verbose_name_plural = "Статистика посещений"
        ordering = ['-date']
    
    def __str__(self):
        return f'{self.date} - {self.count} посещений'


class Poll(models.Model):
    """Модель для опросов на сайте"""
    question = models.CharField(max_length=200, verbose_name="Вопрос")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    
    class Meta:
        verbose_name = "Опрос"
        verbose_name_plural = "Опросы"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.question


class PollOption(models.Model):
    """Модель для вариантов ответа в опросе"""
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='options', verbose_name="Опрос")
    text = models.CharField(max_length=200, verbose_name="Текст варианта")
    
    class Meta:
        verbose_name = "Вариант ответа"
        verbose_name_plural = "Варианты ответов"
    
    def __str__(self):
        return self.text


class PollVote(models.Model):
    """Модель для голосов в опросе"""
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='votes', verbose_name="Опрос")
    option = models.ForeignKey(PollOption, on_delete=models.CASCADE, related_name='votes', verbose_name="Вариант")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='poll_votes', verbose_name="Пользователь")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата голосования")
    
    class Meta:
        verbose_name = "Голос в опросе"
        verbose_name_plural = "Голоса в опросе"
        unique_together = ['poll', 'user']
    
    def __str__(self):
        return f'{self.user.username} - {self.option.text}'