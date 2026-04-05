from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, FormView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import HttpResponse, FileResponse, HttpResponseForbidden
from django.core.exceptions import PermissionDenied
from django.views import View
from django.conf import settings
import os
import logging
from django.db import models
from .models import Advertisement, Category, Comment, Message, Report, Share, Order, Cart, CartItem
from .forms import AdvertisementForm, OrderForm
from django.http import JsonResponse, HttpResponseForbidden
from .forms import CommentForm
from .forms import MessageForm
from .forms import ReportForm
from .forms import ShareForm

logger = logging.getLogger('myapp.security')


def is_ad_available_to_user(user, ad):
    """Return True when user is allowed to access the advertisement details."""
    if user.is_staff or user.is_superuser:
        return True
    return ad.status == 'active'


class AdminOrOwnerMixin(UserPassesTestMixin):
    """Mixin to check if user is admin or owner of the advertisement"""
    def test_func(self):
        ad = self.get_object()
        # Allow if user is admin/staff or the owner
        return self.request.user.is_staff or self.request.user == ad.user
    
    def handle_no_permission(self):
        # Redirect to home if not authorized
        return redirect('advertisement-list')


class AdminOnlyMixin(UserPassesTestMixin):
    """Mixin to check if user is admin"""
    def test_func(self):
        user = self.request.user
        return user.is_staff or user.is_superuser
    
    def handle_no_permission(self):
        # Redirect to home if not authorized
        return redirect('advertisement-list')


class ApprovedOrStaffMixin(UserPassesTestMixin):
    """Allow access if user is staff or authenticated."""
    def test_func(self):
        user = self.request.user
        if not user.is_authenticated:
            return False
        if user.is_staff or user.is_superuser:
            return True
        # Allow all authenticated users since profile approval is removed
        return True
    
    def handle_no_permission(self):
        return redirect('advertisement-list')


class LandingPageView(TemplateView):
    template_name = 'myapp/landing.html'

    # The landing page is shown to all visitors (authenticated or not).
    # Users can still navigate to the advertisements list via the menu.


class AdvertisementListView(LoginRequiredMixin, ListView):
    model = Advertisement
    template_name = 'myapp/advertisement_list.html'
    context_object_name = 'advertisements'
    paginate_by = 10
    login_url = 'login'  # Redirect to login page if not authenticated
    
    def get_queryset(self):
        # Regular users only see active ads, admins see all statuses
        if self.request.user.is_staff or self.request.user.is_superuser:
            queryset = Advertisement.objects.all()
        else:
            queryset = Advertisement.objects.filter(status='active')

        category = self.request.GET.get('category')
        status = self.request.GET.get('status')

        if category:
            queryset = queryset.filter(category_id=category)
        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        return context


class AdvertisementDetailView(LoginRequiredMixin, DetailView):
    model = Advertisement
    template_name = 'myapp/advertisement_detail.html'
    context_object_name = 'advertisement'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    login_url = 'login'  # Redirect to login page if not authenticated
    
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)

        # Regular users cannot view non-active ads.
        if not (self.request.user.is_staff or self.request.user.is_superuser):
            if obj.status != 'active':
                raise PermissionDenied('You do not have permission to view this advertisement.')

        obj.views += 1
        obj.save()
        return obj


class ToggleLikeView(View):
    def post(self, request, slug):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'login_required'}, status=403)
        ad = get_object_or_404(Advertisement, slug=slug)
        if not is_ad_available_to_user(request.user, ad):
            return JsonResponse({'error': 'permission_denied'}, status=403)

        user = request.user
        if user in ad.likes.all():
            ad.likes.remove(user)
            liked = False
        else:
            ad.likes.add(user)
            liked = True
        return JsonResponse({'liked': liked, 'total_likes': ad.likes.count()})


class IncrementShareView(View):
    def post(self, request, slug):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'login_required'}, status=403)

        ad = get_object_or_404(Advertisement, slug=slug)
        if not is_ad_available_to_user(request.user, ad):
            return JsonResponse({'error': 'permission_denied'}, status=403)

        share_method = request.POST.get('share_method', 'link')

        # Create or get share record
        share, created = Share.objects.get_or_create(
            user=request.user,
            advertisement=ad,
            share_method=share_method,
            defaults={
                'ip_address': self.get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', '')
            }
        )

        return JsonResponse({
            'shares_count': ad.shares_count,
            'created': created
        })

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class ShareAnalyticsView(AdminOnlyMixin, TemplateView):
    template_name = 'myapp/share_analytics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Share statistics
        context['total_shares'] = Share.objects.count()
        context['unique_sharers'] = Share.objects.values('user').distinct().count()
        context['most_shared_ads'] = Advertisement.objects.annotate(
            share_count=models.Count('shares')
        ).order_by('-share_count')[:10]

        # Shares by method
        shares_by_method = Share.objects.values('share_method').annotate(
            count=models.Count('share_method')
        ).order_by('-count')
        
        # Calculate percentage for each method
        total_shares = context['total_shares']
        for method in shares_by_method:
            if total_shares > 0:
                method['percentage'] = round((method['count'] / total_shares) * 100, 1)
            else:
                method['percentage'] = 0
        
        context['shares_by_method'] = shares_by_method

        # Recent shares
        context['recent_shares'] = Share.objects.select_related('user', 'advertisement')[:20]

        # Shares over time (last 30 days)
        from django.utils import timezone
        from datetime import timedelta

        thirty_days_ago = timezone.now() - timedelta(days=30)
        context['shares_last_30_days'] = Share.objects.filter(
            shared_at__gte=thirty_days_ago
        ).count()

        return context


class UserShareHistoryView(LoginRequiredMixin, ListView):
    model = Share
    template_name = 'myapp/user_share_history.html'
    context_object_name = 'shares'
    paginate_by = 20

    def get_queryset(self):
        return Share.objects.filter(user=self.request.user).select_related('advertisement')


class UserProfileView(LoginRequiredMixin, TemplateView):
    """User profile page for viewing and editing user information"""
    template_name = 'myapp/user_profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get user statistics
        context['user'] = user
        context['total_ads'] = Advertisement.objects.filter(user=user).count()
        context['active_ads'] = Advertisement.objects.filter(user=user, status='active').count()
        context['total_views'] = Advertisement.objects.filter(user=user).aggregate(
            total=models.Sum('views')
        )['total'] or 0
        context['total_likes'] = Advertisement.objects.filter(user=user).aggregate(
            total=models.Count('likes')
        )['total'] or 0
        context['member_since'] = user.date_joined.strftime('%B %Y')
        
        return context


class UserRolesView(TemplateView):
    """Display user roles and permissions information"""
    template_name = 'myapp/user_roles.html'


class AddCommentView(View):
    def post(self, request, slug):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'login_required'}, status=403)
        ad = get_object_or_404(Advertisement, slug=slug)
        if not is_ad_available_to_user(request.user, ad):
            return JsonResponse({'error': 'permission_denied'}, status=403)
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.ad = ad

            # Handle parent comment for replies
            parent_id = request.POST.get('parent_id')
            if parent_id:
                try:
                    parent_comment = Comment.objects.get(id=parent_id, ad=ad)
                    comment.parent = parent_comment
                except Comment.DoesNotExist:
                    return JsonResponse({'error': 'Parent comment not found'}, status=400)

            comment.save()

            return JsonResponse({
                'ok': True,
                'comment_id': comment.id,
                'username': request.user.username,
                'text': comment.text,
                'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M'),
                'is_reply': comment.is_reply(),
                'parent_id': parent_id or None
            })
        return JsonResponse({'ok': False, 'errors': form.errors}, status=400)


class AdvertisementCreateView(LoginRequiredMixin, AdminOnlyMixin, CreateView):
    model = Advertisement
    template_name = 'myapp/advertisement_form.html'
    form_class = AdvertisementForm
    success_url = reverse_lazy('advertisement-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'user': self.request.user})
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class AdvertisementUpdateView(LoginRequiredMixin, AdminOnlyMixin, UpdateView):
    model = Advertisement
    template_name = 'myapp/advertisement_form.html'
    form_class = AdvertisementForm
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'user': self.request.user})
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('advertisement-detail', kwargs={'slug': self.object.slug})


class AdvertisementDeleteView(LoginRequiredMixin, AdminOnlyMixin, DeleteView):
    model = Advertisement
    template_name = 'myapp/advertisement_confirm_delete.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    success_url = reverse_lazy('advertisement-list')


class CategoryListView(LoginRequiredMixin, ListView):
    model = Category
    template_name = 'myapp/category_list.html'
    context_object_name = 'categories'
    login_url = 'login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for category in context['categories']:
            if self.request.user.is_staff or self.request.user.is_superuser:
                category.ad_count = category.advertisement_set.count()
            else:
                category.ad_count = category.advertisement_set.filter(status='active').count()
        return context


class DownloadAdvertisementImageView(View):
    """View to download advertisement image"""
    def get(self, request, slug):
        advertisement = get_object_or_404(Advertisement, slug=slug)
        if not is_ad_available_to_user(request.user, advertisement):
            return HttpResponseForbidden("You do not have permission to download this image.")

        if not advertisement.image:
            return HttpResponse("No image available", status=404)
        
        file_path = advertisement.image.path
        
        if not os.path.exists(file_path):
            return HttpResponse("Image file not found", status=404)
        
        # Get the filename
        filename = os.path.basename(file_path)
        
        # Open and serve the file
        with open(file_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response


class CustomLoginView(LoginView):
    """Custom login view"""
    template_name = 'myapp/login.html'
    form_class = AuthenticationForm
    # After login, send the user to the advertisement list to see products.
    success_url = reverse_lazy('advertisement-list')
    
    def get_success_url(self):
        return self.success_url
    
    def form_valid(self, form):
        """Log successful login"""
        response = super().form_valid(form)
        logger.info(f'Successful login for user: {self.request.user.username} from IP: {self.get_client_ip()}')
        return response
    
    def form_invalid(self, form):
        """Log failed login attempt"""
        logger.warning(f'Failed login attempt for username: {form.data.get("username")} from IP: {self.get_client_ip()}')
        return super().form_invalid(form)
    
    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip


class CustomLogoutView(LogoutView):
    """Custom logout view"""

    # Allow logout via GET as well as POST so the header link can log users out.
    # We override GET to mirror the POST behavior (logout + redirect).
    next_page = reverse_lazy('landing')
    http_method_names = ['get', 'post', 'options']

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)


class SignupView(CreateView):
    """User registration view - creates regular users only"""
    form_class = UserCreationForm
    template_name = 'myapp/signup.html'
    success_url = reverse_lazy('login')
    
    def form_valid(self, form):
        """Create regular user account"""
        # Check if terms were accepted
        if not self.request.POST.get('accept_terms'):
            from django.contrib import messages
            messages.error(self.request, 'You must accept the Terms & Conditions to create an account.')
            return self.form_invalid(form)
            
        user = form.save()
        # Ensure new users are never staff or superuser
        user.is_staff = False
        user.is_superuser = False
        user.save()
        
        logger.info(f'New regular user account created: {user.username} from IP: {self.get_client_ip()}')
        return super().form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        """Block or redirect signup attempts originating from the admin portal.

        We check the HTTP Referer and the `next` GET parameter for the
        admin portal token. If found, redirect to the advertisement list to
        avoid allowing signups coming from the admin area.
        """
        referer = request.META.get('HTTP_REFERER', '')
        next_param = request.GET.get('next', '')
        if 'admin-portal' in referer or 'admin-portal' in next_param:
            logger.warning(f'Blocked signup attempt from admin area from IP: {self.get_client_ip()}')
            return HttpResponse('Forbidden', status=403)
        return super().dispatch(request, *args, **kwargs)
    
    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip


# -------------------------  
# MESSAGING VIEWS
# -------------------------
class InboxView(LoginRequiredMixin, ListView):
    model = Message
    template_name = 'myapp/inbox.html'
    context_object_name = 'messages'
    paginate_by = 20

    def get_queryset(self):
        return Message.objects.filter(receiver=self.request.user).order_by('-created_at')


class SentMessagesView(LoginRequiredMixin, ListView):
    model = Message
    template_name = 'myapp/sent_messages.html'
    context_object_name = 'messages'
    paginate_by = 20

    def get_queryset(self):
        return Message.objects.filter(sender=self.request.user).order_by('-created_at')


class ComposeMessageView(LoginRequiredMixin, CreateView):
    model = Message
    form_class = MessageForm
    template_name = 'myapp/compose_message.html'
    success_url = reverse_lazy('inbox')

    def form_valid(self, form):
        form.instance.sender = self.request.user
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        receiver_id = self.request.GET.get('receiver')
        ad_id = self.request.GET.get('ad')
        if receiver_id:
            try:
                initial['receiver'] = User.objects.get(id=receiver_id)
            except User.DoesNotExist:
                pass
        if ad_id:
            try:
                initial['ad'] = Advertisement.objects.get(id=ad_id)
            except Advertisement.DoesNotExist:
                pass
        return initial


class MessageDetailView(LoginRequiredMixin, DetailView):
    model = Message
    template_name = 'myapp/message_detail.html'
    context_object_name = 'message'

    def get_queryset(self):
        # Only allow viewing messages sent to or from the user
        return Message.objects.filter(
            models.Q(sender=self.request.user) | models.Q(receiver=self.request.user)
        )

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        # Mark as read if the user is the receiver
        if obj.receiver == self.request.user and not obj.is_read:
            obj.is_read = True
            obj.save()
        return obj


# -------------------------
# REPORTING VIEWS
# -------------------------
class ReportAdvertisementView(LoginRequiredMixin, CreateView):
    model = Report
    form_class = ReportForm
    template_name = 'myapp/report_ad.html'

    def dispatch(self, request, *args, **kwargs):
        # Ensure advert exists before rendering
        self.ad = get_object_or_404(Advertisement, slug=kwargs.get('slug'))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['advertisement'] = self.ad
        return context

    def form_valid(self, form):
        form.instance.reporter = self.request.user
        form.instance.advertisement = self.ad
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('advertisement-detail', kwargs={'slug': self.ad.slug})


class ReportListView(AdminOnlyMixin, ListView):
    model = Report
    template_name = 'myapp/admin_reports.html'
    context_object_name = 'reports'
    paginate_by = 20

    def get_queryset(self):
        status = self.request.GET.get('status')
        report_type = self.request.GET.get('type')
        queryset = Report.objects.select_related('reporter', 'advertisement', 'advertisement__user')

        if status:
            queryset = queryset.filter(status=status)
        if report_type:
            queryset = queryset.filter(report_type=report_type)

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Report.STATUS_CHOICES
        context['report_type_choices'] = Report.REPORT_TYPES
        return context


class ReportDetailView(AdminOnlyMixin, DetailView):
    model = Report
    template_name = 'myapp/admin_report_detail.html'
    context_object_name = 'report'


class UpdateReportStatusView(AdminOnlyMixin, View):
    def post(self, request, pk):
        report = get_object_or_404(Report, pk=pk)
        new_status = request.POST.get('status')
        admin_notes = request.POST.get('admin_notes', '')

        if new_status in dict(Report.STATUS_CHOICES):
            report.status = new_status
            report.admin_notes = admin_notes
            report.save()

        return redirect('admin-report-detail', pk=pk)


class UserDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'myapp/user_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # User's advertisements
        context['user_ads'] = Advertisement.objects.filter(user=user).order_by('-created_at')
        context['active_ads_count'] = context['user_ads'].filter(status='active').count()
        context['sold_ads_count'] = context['user_ads'].filter(status='sold').count()
        context['total_views'] = context['user_ads'].aggregate(total=models.Sum('views'))['total'] or 0
        context['total_likes'] = context['user_ads'].aggregate(total=models.Sum('likes__id', distinct=True))['total'] or 0

        # User's activity
        context['user_messages'] = Message.objects.filter(
            models.Q(sender=user) | models.Q(receiver=user)
        ).order_by('-created_at')[:5]

        context['user_reports'] = Report.objects.filter(reporter=user).order_by('-created_at')[:5]
        context['user_shares'] = Share.objects.filter(user=user).select_related('advertisement').order_by('-shared_at')[:10]

        # Recent comments on user's ads
        context['recent_comments'] = Comment.objects.filter(
            ad__user=user
        ).select_related('user', 'ad').order_by('-created_at')[:10]

        return context


class AdminDashboardView(AdminOnlyMixin, TemplateView):
    template_name = 'myapp/admin_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Basic statistics
        context['total_ads'] = Advertisement.objects.count()
        context['active_ads'] = Advertisement.objects.filter(status='active').count()
        context['pending_ads'] = Advertisement.objects.filter(status='pending').count()
        context['sold_ads'] = Advertisement.objects.filter(status='sold').count()
        context['expired_ads'] = Advertisement.objects.filter(status='expired').count()

        context['total_users'] = User.objects.count()
        context['staff_users'] = User.objects.filter(is_staff=True).count()
        context['active_users'] = User.objects.filter(is_active=True).count()
        context['inactive_users'] = User.objects.filter(is_active=False).count()

        # Content moderation
        context['pending_reports'] = Report.objects.filter(status='pending').count()
        context['total_reports'] = Report.objects.count()
        context['resolved_reports'] = Report.objects.filter(status='resolved').count()
        context['dismissed_reports'] = Report.objects.filter(status='dismissed').count()

        # Social features statistics
        context['total_comments'] = Comment.objects.count()
        context['total_likes'] = Advertisement.objects.aggregate(total=models.Sum('likes__id', distinct=True))['total'] or 0
        context['total_shares'] = Share.objects.count()
        context['unique_sharers'] = Share.objects.values('user').distinct().count()

        # Recent activity
        context['recent_reports'] = Report.objects.select_related('reporter', 'advertisement')[:10]
        context['recent_ads'] = Advertisement.objects.select_related('user').order_by('-created_at')[:10]
        context['recent_users'] = User.objects.order_by('-date_joined')[:10]

        # Analytics data
        context['ads_by_status'] = Advertisement.objects.values('status').annotate(count=models.Count('status'))
        context['reports_by_type'] = Report.objects.values('report_type').annotate(count=models.Count('report_type'))
        context['shares_by_method'] = Share.objects.values('share_method').annotate(count=models.Count('share_method')).order_by('-count')

        return context


class AdminUserManagementView(AdminOnlyMixin, ListView):
    model = User
    template_name = 'myapp/admin_users.html'
    context_object_name = 'users'
    paginate_by = 20

    def get_queryset(self):
        queryset = User.objects.all().order_by('-date_joined')
        search = self.request.GET.get('search')
        status = self.request.GET.get('status')
        is_staff = self.request.GET.get('is_staff')

        if search:
            queryset = queryset.filter(
                models.Q(username__icontains=search) |
                models.Q(email__icontains=search) |
                models.Q(first_name__icontains=search) |
                models.Q(last_name__icontains=search)
            )
        if status:
            if status == 'active':
                queryset = queryset.filter(is_active=True)
            elif status == 'inactive':
                queryset = queryset.filter(is_active=False)
        if is_staff:
            if is_staff == 'staff':
                queryset = queryset.filter(is_staff=True)
            elif is_staff == 'user':
                queryset = queryset.filter(is_staff=False)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_users'] = User.objects.count()
        context['active_users'] = User.objects.filter(is_active=True).count()
        context['staff_users'] = User.objects.filter(is_staff=True).count()
        return context


class AdminAdvertisementManagementView(AdminOnlyMixin, ListView):
    model = Advertisement
    template_name = 'myapp/admin_ads.html'
    context_object_name = 'advertisements'
    paginate_by = 20

    def get_queryset(self):
        queryset = Advertisement.objects.select_related('user', 'category').order_by('-created_at')
        search = self.request.GET.get('search')
        status = self.request.GET.get('status')
        category = self.request.GET.get('category')

        if search:
            queryset = queryset.filter(
                models.Q(title__icontains=search) |
                models.Q(description__icontains=search) |
                models.Q(user__username__icontains=search)
            )
        if status:
            queryset = queryset.filter(status=status)
        if category:
            queryset = queryset.filter(category_id=category)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['status_choices'] = Advertisement.STATUS_CHOICES
        return context


class AdminUpdateAdStatusView(AdminOnlyMixin, View):
    def post(self, request, pk):
        ad = get_object_or_404(Advertisement, pk=pk)
        new_status = request.POST.get('status')
        
        if new_status in dict(Advertisement.STATUS_CHOICES):
            ad.status = new_status
            ad.save()
        
        return redirect('admin-ads')


class AdminToggleUserStatusView(AdminOnlyMixin, View):
    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        user.is_active = not user.is_active
        user.save()
        
        return redirect('admin-users')


class UserSignupsListView(AdminOnlyMixin, ListView):
    """Admin view to retrieve and display all user signups (registrations)"""
    model = User
    template_name = 'myapp/user_signups.html'
    context_object_name = 'users'
    paginate_by = 20

    def get_queryset(self):
        queryset = User.objects.all().order_by('-date_joined')
        search = self.request.GET.get('search')
        status = self.request.GET.get('status')

        if search:
            queryset = queryset.filter(
                models.Q(username__icontains=search) |
                models.Q(email__icontains=search) |
                models.Q(first_name__icontains=search) |
                models.Q(last_name__icontains=search)
            )
        if status:
            if status == 'active':
                queryset = queryset.filter(is_active=True)
            elif status == 'inactive':
                queryset = queryset.filter(is_active=False)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_signups'] = User.objects.count()
        context['recent_signups'] = User.objects.order_by('-date_joined')[:10]
        return context



class OrderFormView(LoginRequiredMixin, FormView):
    """Display order form and create Order record."""
    template_name = 'myapp/order_form.html'
    form_class = OrderForm
    login_url = 'login'

    def dispatch(self, request, *args, **kwargs):
        # Ensure advert exists before rendering
        self.ad = get_object_or_404(Advertisement, slug=kwargs.get('slug'))
        if not is_ad_available_to_user(request.user, self.ad):
            return HttpResponseForbidden('You cannot order from this advertisement.')
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.setdefault('initial', {})
        kwargs['initial'].update({
            'buyer_name': self.request.user.get_full_name() or self.request.user.username,
            'buyer_email': self.request.user.email,
        })
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['advertisement'] = self.ad
        context['action'] = 'order'
        return context

    def form_valid(self, form):
        order = Order.objects.create(
            user=self.request.user,
            advertisement=self.ad,
            quantity=form.cleaned_data['quantity'],
            status='pending'
        )
        return render(self.request, 'myapp/order_success.html', {
            'advertisement': self.ad,
            'order': order,
            'action': 'order'
        })


class BuyNowFormView(LoginRequiredMixin, FormView):
    """Display buy-now form and create completed Order."""
    template_name = 'myapp/order_form.html'
    form_class = OrderForm
    login_url = 'login'

    def dispatch(self, request, *args, **kwargs):
        self.ad = get_object_or_404(Advertisement, slug=kwargs.get('slug'))
        if not is_ad_available_to_user(request.user, self.ad):
            return HttpResponseForbidden('You cannot buy this advertisement.')
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.setdefault('initial', {})
        kwargs['initial'].update({
            'buyer_name': self.request.user.get_full_name() or self.request.user.username,
            'buyer_email': self.request.user.email,
        })
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['advertisement'] = self.ad
        context['action'] = 'buy'
        return context

    def form_valid(self, form):
        order = Order.objects.create(
            user=self.request.user,
            advertisement=self.ad,
            quantity=form.cleaned_data['quantity'],
            status='completed'
        )
        return render(self.request, 'myapp/order_success.html', {
            'advertisement': self.ad,
            'order': order,
            'action': 'buy'
        })


# -------------------------  
# CART VIEWS
# -------------------------
class AddToCartView(View):
    def post(self, request, slug):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'login_required'}, status=403)
        
        ad = get_object_or_404(Advertisement, slug=slug)
        quantity = int(request.POST.get('quantity', 1))
        
        # Get or create cart for user
        cart, created = Cart.objects.get_or_create(user=request.user)
        
        # Get or create cart item
        cart_item, item_created = CartItem.objects.get_or_create(
            cart=cart,
            advertisement=ad,
            defaults={'quantity': quantity}
        )
        
        if not item_created:
            cart_item.quantity += quantity
            cart_item.save()
        
        return JsonResponse({
            'success': True,
            'cart_total_items': cart.get_total_items(),
            'cart_total_price': float(cart.get_total_price())
        })


class CartView(LoginRequiredMixin, TemplateView):
    template_name = 'myapp/cart.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        context['cart'] = cart
        context['cart_items'] = cart.items.select_related('advertisement').all()
        return context


class UpdateCartItemView(View):
    def post(self, request, item_id):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'login_required'}, status=403)
        
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        quantity = int(request.POST.get('quantity', 1))
        
        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
        else:
            cart_item.delete()
        
        cart = cart_item.cart
        return JsonResponse({
            'success': True,
            'item_total': float(cart_item.get_total_price()) if quantity > 0 else 0,
            'cart_total_items': cart.get_total_items(),
            'cart_total_price': float(cart.get_total_price())
        })


class RemoveCartItemView(View):
    def post(self, request, item_id):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'login_required'}, status=403)
        
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        cart = cart_item.cart
        cart_item.delete()
        
        return JsonResponse({
            'success': True,
            'cart_total_items': cart.get_total_items(),
            'cart_total_price': float(cart.get_total_price())
        })


class CheckoutView(LoginRequiredMixin, TemplateView):
    template_name = 'myapp/checkout.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        if not cart.items.exists():
            # Redirect to cart if empty
            return redirect('cart')
        context['cart'] = cart
        context['cart_items'] = cart.items.select_related('advertisement').all()
        return context


class ProcessCheckoutView(LoginRequiredMixin, View):
    def post(self, request):
        cart = get_object_or_404(Cart, user=request.user)
        if not cart.items.exists():
            return redirect('cart')
        
        # Validate form data
        buyer_name = request.POST.get('buyer_name')
        buyer_email = request.POST.get('buyer_email')
        payment_method = request.POST.get('payment_method')
        shipping_address = request.POST.get('shipping_address')
        notes = request.POST.get('notes', '')
        
        if not all([buyer_name, buyer_email, payment_method, shipping_address]):
            messages.error(request, 'Please fill in all required fields.')
            return redirect('checkout')
        
        # Create orders for each cart item
        orders = []
        for item in cart.items.all():
            order = Order.objects.create(
                user=request.user,
                advertisement=item.advertisement,
                quantity=item.quantity,
                status='completed'
            )
            orders.append(order)
        
        # Clear the cart
        cart.items.all().delete()
        
        return render(request, 'myapp/checkout_success.html', {
            'orders': orders,
            'cart': cart
        })
