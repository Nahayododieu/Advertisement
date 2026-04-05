from django.urls import path
from . import views

urlpatterns = [

    # Landing page (public)
    path('', views.LandingPageView.as_view(), name='landing'),

    # Advertisement URLs
    path('advertisements/', views.AdvertisementListView.as_view(), name='advertisement-list'),
    path('advertisement/create/', views.AdvertisementCreateView.as_view(), name='advertisement-create'),
    path('advertisement/<slug:slug>/', views.AdvertisementDetailView.as_view(), name='advertisement-detail'),
    path('advertisement/<slug:slug>/edit/', views.AdvertisementUpdateView.as_view(), name='advertisement-update'),
    path('advertisement/<slug:slug>/delete/', views.AdvertisementDeleteView.as_view(), name='advertisement-delete'),
    path('advertisement/<slug:slug>/download-image/', views.DownloadAdvertisementImageView.as_view(), name='download-image'),
    path('advertisement/<slug:slug>/like-toggle/', views.ToggleLikeView.as_view(), name='advertisement-like-toggle'),
    path('advertisement/<slug:slug>/share/', views.IncrementShareView.as_view(), name='advertisement-share'),
    path('advertisement/<slug:slug>/comment/', views.AddCommentView.as_view(), name='advertisement-add-comment'),
    path('advertisement/<slug:slug>/order/', views.OrderFormView.as_view(), name='advertisement-order'),
    path('advertisement/<slug:slug>/buy/', views.BuyNowFormView.as_view(), name='advertisement-buy'),
    path('advertisement/<slug:slug>/add-to-cart/', views.AddToCartView.as_view(), name='add-to-cart'),

    # Cart URLs
    path('cart/', views.CartView.as_view(), name='cart'),
    path('cart/item/<int:item_id>/update/', views.UpdateCartItemView.as_view(), name='update-cart-item'),
    path('cart/item/<int:item_id>/remove/', views.RemoveCartItemView.as_view(), name='remove-cart-item'),
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    path('checkout/process/', views.ProcessCheckoutView.as_view(), name='process-checkout'),

    # Authentication
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='user-logout'),
    path('signup/', views.SignupView.as_view(), name='signup'),

    # Categories
    path('categories/', views.CategoryListView.as_view(), name='category-list'),

    # Messaging
    path('messages/inbox/', views.InboxView.as_view(), name='inbox'),
    path('messages/sent/', views.SentMessagesView.as_view(), name='sent-messages'),
    path('messages/compose/', views.ComposeMessageView.as_view(), name='compose-message'),
    path('messages/<int:pk>/', views.MessageDetailView.as_view(), name='message-detail'),

    # Reporting
    path('advertisement/<slug:slug>/report/', views.ReportAdvertisementView.as_view(), name='report-ad'),
    path('admin/reports/', views.ReportListView.as_view(), name='admin-reports'),
    path('admin/reports/<int:pk>/', views.ReportDetailView.as_view(), name='admin-report-detail'),
    path('admin/reports/<int:pk>/update/', views.UpdateReportStatusView.as_view(), name='update-report-status'),

    # Admin Dashboard
    path('admin/dashboard/', views.AdminDashboardView.as_view(), name='admin-dashboard'),
    path('admin/share-analytics/', views.ShareAnalyticsView.as_view(), name='share-analytics'),

    # Admin Management
    path('admin/users/', views.AdminUserManagementView.as_view(), name='admin-users'),
    path('admin/ads/', views.AdminAdvertisementManagementView.as_view(), name='admin-ads'),
    path('admin/ads/<int:pk>/status/', views.AdminUpdateAdStatusView.as_view(), name='admin-update-ad-status'),
    path('admin/users/<int:pk>/toggle/', views.AdminToggleUserStatusView.as_view(), name='admin-toggle-user-status'),

    # User Dashboard
    path('dashboard/', views.UserDashboardView.as_view(), name='user-dashboard'),
    path('profile/', views.UserProfileView.as_view(), name='user-profile'),
    path('user/share-history/', views.UserShareHistoryView.as_view(), name='user-share-history'),
    path('user/roles/', views.UserRolesView.as_view(), name='user-roles'),
]