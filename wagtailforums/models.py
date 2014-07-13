from django.db import models
from django.shortcuts import render, redirect
from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailcore.models import Page
from wagtail.wagtailcore.signals import page_published
from wagtail.wagtailcore.url_routing import RouteResult
from wagtail.wagtailadmin.edit_handlers import FieldPanel


class ForumReply(Page):
    message = models.TextField(_("Message"))

    subpage_types = (
        'wagtailforums.ForumReply',
    )

    def get_replies(self):
        return ForumReply.objects.child_of(self)

    @classmethod
    def get_form_class(cls):
        from wagtailforums.forms import ForumReplyForm
        return ForumReplyForm

    @property
    def edit_url(self):
        return self.url + 'edit/'

    @property
    def delete_url(self):
        return self.url + 'delete/'

    def route(self, request, path_components):
        if self.live:
            if path_components == ['edit']:
                return RouteResult(self, kwargs=dict(action='edit'))

            if path_components == ['delete']:
                return RouteResult(self, kwargs=dict(action='delete'))

        return super(ForumReply, self).route(request, path_components)

    def edit_view(self, request):
        form = self.get_form_class()(request.POST or None, request.FILES or None, instance=self)

        if form.is_valid():
            form.save()
            self.save_revision(user=request.user)
            page_published.send(sender=self.__class__, instance=self)

            return redirect(self.get_parent().url)
        else:
            context = self.get_context(request)
            context['form'] = form
            return render(request, 'wagtailforums/forum_reply_edit.html', context)

    def delete_view(self, request):
        if request.method == 'POST':
            self.live = False
            self.save()
            return redirect(self.get_parent().url)
        else:
            return render(request, 'wagtailforums/forum_reply_delete.html', self.get_context(request))

    def serve(self, request, action='view'):
        if action == 'edit':
            return self.edit_view(request)

        if action == 'delete':
            return self.delete_view(request)

        return super(ForumReply, self).serve(request)

ForumReply.content_panels = Page.content_panels + [
    FieldPanel('message', classname="full"),
]


class ForumTopic(Page):
    in_forum_index = models.BooleanField(_("Show in forum index"), default=True)
    message = models.TextField(_("Message"))

    subpage_types = (
        'wagtailforums.ForumReply',
    )

    def get_replies(self):
        return ForumReply.objects.child_of(self)

    def get_all_replies(self):
        return ForumReply.objects.descendant_of(self)

ForumTopic.content_panels = Page.content_panels + [
    FieldPanel('message', classname="full"),
]

ForumTopic.promote_panels = Page.promote_panels + [
    FieldPanel('in_forum_index'),
]


class ForumIndex(Page):
    in_forum_index = models.BooleanField(_("Show in forum index"), default=True)

    def get_forums(self):
        return ForumIndex.objects.child_of(self)

    def get_all_forums(self):
        return ForumIndex.objects.descendant_of(self)

    def get_topics(self):
        return ForumTopic.objects.child_of(self)

    def get_all_topics(self):
        return ForumTopic.objects.descendant_of(self)

    def get_all_replies(self):
        return ForumReply.objects.descendant_of(self)

ForumIndex.promote_panels = Page.promote_panels + [
    FieldPanel('in_forum_index'),
]
