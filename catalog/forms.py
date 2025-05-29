from django import forms
from .models import Comment, Vote, PollOption

class CommentForm(forms.ModelForm):
    """Форма для добавления комментария"""
    
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'placeholder': 'Напишите ваш комментарий...'
            }),
        }


class VoteForm(forms.ModelForm):
    """Форма для голосования за предмет коллекции"""
    
    class Meta:
        model = Vote
        fields = ['value']


class PollVoteForm(forms.Form):
    """Форма для голосования в опросе"""
    option = forms.ChoiceField(
        widget=forms.RadioSelect(attrs={'class': 'poll-option'}),
        label='Выберите вариант ответа'
    )
    
    def __init__(self, poll=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if poll:
            self.fields['option'].choices = [(option.id, option.text) for option in poll.options.all()]