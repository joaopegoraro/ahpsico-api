from django.contrib import admin

from .models import *

admin.site.register(Doctor)
admin.site.register(Patient)
admin.site.register(Invite)
admin.site.register(Advice)
admin.site.register(Assignment)
admin.site.register(Session)
admin.site.register(SessionGroup)
