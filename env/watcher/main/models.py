from __future__ import unicode_literals
from django.db import models


from jsonfield import JSONField    # converts from python dict to a json string when saving to the db


class FormSchema(models.Model):
	title = models.CharField(max_length=100)
	schema = JSONField()


class FormResponse(models.Model):
	form = models.ForeignKey(FormSchema)
	response = JSONField()




