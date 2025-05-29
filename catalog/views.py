from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from django.db.models import Count, Sum, Case, When, IntegerField
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from hitcount.views import HitCountDetailView

from .models import (
    Category, CollectibleItem, Comment, Vote, UserCollection,
    Poll, PollOption, PollVote
)
from .forms import CommentForm, VoteForm, PollVoteForm


class IndexView(ListView):
    """Главная страница с последними добавленными предметами"""
    model = CollectibleItem
    template_name = 'catalog/index.html'
    context_object_name = 'items'
    paginate_by = 12
    
    def get_queryset(self):
        return CollectibleItem.objects.all().order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.annotate(
            item_count=Count('items')
        ).order_by('-item_count')[:5]
        
        # Добавляем активный опрос
        context['poll'] = Poll.objects.filter(is_active=True).first()
        if context['poll'] and self.request.user.is_authenticated:
            # Проверяем, голосовал ли пользователь в этом опросе
            context['user_voted'] = PollVote.objects.filter(
                poll=context['poll'], 
                user=self.request.user
            ).exists()
            
            # Если пользователь голосовал, добавляем результаты
            if context['user_voted']:
                # Подсчитываем количество голосов для каждого варианта
                options = context['poll'].options.annotate(
                    vote_count=Count('votes')
                ).order_by('-vote_count')
                
                # Считаем общее количество голосов
                total_votes = sum(option.vote_count for option in options)
                
                # Добавляем процент для каждого варианта
                for option in options:
                    option.percentage = round(option.vote_count / total_votes * 100) if total_votes > 0 else 0
                
                context['poll_options'] = options
                context['total_votes'] = total_votes
            else:
                context['poll_form'] = PollVoteForm(poll=context['poll'])
                
        return context


class CategoryListView(ListView):
    """Список категорий"""
    model = Category
    template_name = 'catalog/category_list.html'
    context_object_name = 'categories'
    
    def get_queryset(self):
        return Category.objects.annotate(item_count=Count('items'))


class CategoryDetailView(DetailView):
    """Детальная страница категории с предметами"""
    model = Category
    template_name = 'catalog/category_detail.html'
    context_object_name = 'category'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.items.all()
        return context


class ItemDetailView(HitCountDetailView):
    """Детальная страница предмета коллекции"""
    model = CollectibleItem
    template_name = 'catalog/item_detail.html'
    context_object_name = 'item'
    count_hit = True
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Добавляем форму комментария
        context['comment_form'] = CommentForm()
        
        # Проверяем, добавлен ли предмет в коллекцию пользователя
        if self.request.user.is_authenticated:
            context['in_collection'] = UserCollection.objects.filter(
                user=self.request.user, 
                item=self.object
            ).exists()
            
            # Проверяем, голосовал ли пользователь за этот предмет
            try:
                vote = Vote.objects.get(user=self.request.user, item=self.object)
                context['user_vote'] = vote.value
            except Vote.DoesNotExist:
                context['user_vote'] = None
        
        # Подсчитываем количество лайков и дизлайков
        context['likes'] = self.object.votes.filter(value=True).count()
        context['dislikes'] = self.object.votes.filter(value=False).count()
        
        return context


@login_required
def add_comment(request, slug):
    """Добавление комментария к предмету"""
    item = get_object_or_404(CollectibleItem, slug=slug)
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.item = item
            comment.user = request.user
            comment.save()
            messages.success(request, 'Комментарий успешно добавлен!')
    
    return redirect('item_detail', slug=slug)


@login_required
def vote_item(request, slug):
    """Голосование за предмет коллекции"""
    item = get_object_or_404(CollectibleItem, slug=slug)
    
    if request.method == 'POST':
        value = request.POST.get('value') == 'true'
        
        # Проверяем, голосовал ли пользователь ранее
        vote, created = Vote.objects.get_or_create(
            user=request.user,
            item=item,
            defaults={'value': value}
        )
        
        # Если пользователь уже голосовал, обновляем его выбор
        if not created:
            vote.value = value
            vote.save()
        
        # Возвращаем новое количество лайков и дизлайков
        likes = item.votes.filter(value=True).count()
        dislikes = item.votes.filter(value=False).count()
        
        return JsonResponse({
            'success': True,
            'likes': likes,
            'dislikes': dislikes
        })
    
    return JsonResponse({'success': False})


@login_required
def toggle_collection(request, slug):
    """Добавление/удаление предмета в/из коллекции пользователя"""
    item = get_object_or_404(CollectibleItem, slug=slug)
    
    # Проверяем, есть ли уже предмет в коллекции
    collection_item = UserCollection.objects.filter(user=request.user, item=item)
    
    if collection_item.exists():
        # Если предмет уже в коллекции, удаляем его
        collection_item.delete()
        messages.success(request, 'Предмет удален из вашей коллекции')
        in_collection = False
    else:
        # Если предмета нет в коллекции, добавляем его
        UserCollection.objects.create(user=request.user, item=item)
        messages.success(request, 'Предмет добавлен в вашу коллекцию')
        in_collection = True
    
    if request.is_ajax():
        return JsonResponse({
            'success': True,
            'in_collection': in_collection
        })
    
    return redirect('item_detail', slug=slug)


@login_required
def user_collection(request):
    """Просмотр личной коллекции пользователя"""
    collection_items = UserCollection.objects.filter(user=request.user).select_related('item')
    
    return render(request, 'catalog/user_collection.html', {
        'collection_items': collection_items
    })


@login_required
def vote_poll(request, poll_id):
    """Голосование в опросе"""
    poll = get_object_or_404(Poll, id=poll_id, is_active=True)
    
    # Проверяем, голосовал ли пользователь в этом опросе
    if PollVote.objects.filter(poll=poll, user=request.user).exists():
        messages.error(request, 'Вы уже голосовали в этом опросе')
        return redirect('index')
    
    if request.method == 'POST':
        form = PollVoteForm(poll=poll, data=request.POST)
        if form.is_valid():
            option_id = form.cleaned_data['option']
            option = get_object_or_404(PollOption, id=option_id, poll=poll)
            
            # Создаем голос
            PollVote.objects.create(
                poll=poll,
                option=option,
                user=request.user
            )
            
            messages.success(request, 'Ваш голос учтен!')
            return redirect('index')
    
    return redirect('index')