from django import forms
from django.contrib.auth.models import User
from .models import Advertisement
from .models import Comment
from .models import Message
from .models import Report
from .models import Share


class AdvertisementForm(forms.ModelForm):
    class Meta:
        model = Advertisement
        fields = ['image', 'title', 'slug', 'description', 'price', 'category', 'city', 'is_featured', 'status']

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Add a comment...'})
        }


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['receiver', 'ad', 'subject', 'body']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Write your message...'})
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['receiver'].queryset = User.objects.exclude(id=user.id)
        self.fields['ad'].required = False


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['report_type', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Please provide details about why you are reporting this advertisement...'})
        }


class ShareForm(forms.Form):
    share_method = forms.ChoiceField(
        choices=Share.SHARE_METHODS,
        widget=forms.HiddenInput()
    )


class OrderForm(forms.Form):
    PAYMENT_CHOICES = [
        ('credit_card', 'Credit Card'),
        ('paypal', 'PayPal'),
        ('bank_transfer', 'Bank Transfer'),
        ('cod', 'Cash on Delivery'),
    ]

    buyer_name = forms.CharField(max_length=200, label='Full Name')
    buyer_email = forms.EmailField(label='Email Address')
    payment_method = forms.ChoiceField(choices=PAYMENT_CHOICES, label='Payment Method')
    quantity = forms.IntegerField(min_value=1, initial=1, label='Quantity')
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3}), label='Additional Notes (optional)')

