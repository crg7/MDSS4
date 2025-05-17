from django.contrib import admin
from users import models

admin.site.register(models.User)
admin.site.register(models.Vote)
admin.site.register(models.Topic)
admin.site.register(models.Answer)
admin.site.register(models.Question)
admin.site.register(models.Notification)