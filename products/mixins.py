from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class AuthorRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        product = self.get_object()
        return self.request.user == product.author or self.request.user.is_staff
