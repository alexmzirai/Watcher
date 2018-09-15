from django.shortcuts import render
from django.http import HttpResponse
import json
from main.models import FormSchema, FormResponse
from django import forms
from django.views.generic import FormView, ListView
from main.models import FormSchema
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView
from main.forms import NewDynamicFormForm

"""
def current_url_view(request):
	return HttpResponse("welcome to the page at {}".format(request.path))


def display_meta(request):
	values = request.META.items()
	values.sort()
	html = []
	for k, v in values:
		html.append('<tr><td>{}</td><td>{}</td></tr>'.format(k, v))
	return HttpResponse('<table>{}</table>'.format(join(html)))


def search(request):
	if 'q' in request.GET and request.GET['q']:
		error = False
		q = request.GET['q']
		books = Book.objects.filter(title__icontains=q)
		return render(request, 'search.html', {'books': books, 'query': q})

 	else:
 		error = True  # now you can use this in your object template
 		return render(request, 'search.html', {'error': True})

"""



class HomePageView(ListView):
	model = FormSchema
	template_name = "home.html"

# constructing a dynamic form using json
class CustomFormView(FormView):
	template_name = "custom_form.html"

	def get_form(self):
		
		form_structure = FormSchema.objects.get(pk=self.kwargs["form_pk"]).schema	# convert json string to a python object which is a dict as well
		custom_form = forms.Form(**self.get_form_kwargs())	# create an instance of the base django.forms.Form class

		for key, value in form_structure.items():
				field_class = self.get_field_class_from_type(value)
				if field_class is not None:
					custom_form.fields[key] = field_class()
				else:
					raise TypeError("invalid field type {}".format(value))
		return custom_form

	def get_field_class_from_type(self, value_type):
		if value_type == 'string':
			return forms.CharField
		elif value_type == 'number':
			return forms.IntegerField
		else:
			return None


	def form_valid(self, form):
		custom_form = FormSchema.objects.get(pk=self.kwargs["form_pk"])
		user_response = form.cleaned_data

		form_response = FormResponse(form=custom_form, response=user_response)

		form_response.save()

		return HttpResponseRedirect(reverse('home'))

	def get_context_data(self, **kwargs):
		ctx = super(CustomFormView, self).get_context_data(**kwargs)	# current context from super class
		form_schema = FormSchema.objects.get(pk=self.kwargs['form_pk'])
		ctx['form_schema'] = form_schema

		return ctx


class FormResponsesListView(ListView):
	template_name = "form_responses.html"

	def get_context_data(self, **kwargs):
		"""get_context_data() can be overriden to allow adding more context variables.
		First get the existing context from our superclass.
		Then add your new context information.
		Then return the new (updated) context.

		"""
		ctx = super(FormResponsesListView, self).get_context_data(**kwargs)	# existing context from superclass
		ctx['form'] = self.get_form()	# new context information
		return ctx 	# return updated context


	def get_queryset(self):
		form = self.get_form()
		return FormResponse.objects.filter(form=form)

	def get_form(self):
		return FormSchema.objects.get(pk=self.kwargs['form_pk'])


class FormResponsesListView(TemplateView):
	template_name = 'form_responses.html'

	def get_context_data(self, **kwargs):
		"""this method is mainly used to get the context data for variables to be fed to template"""
		ctx = super(FormResponsesListView, self).get_context_data(**kwargs)

		form = self.get_form()
		schema = form.schema
		form_fields = schema.keys()	# notice how the keys() method pulls the keys from the dict to get headers
		ctx['headers'] = form_fields	# the form fields will be used with 'headers' context
		ctx['form'] = form

		responses = self.get_queryset()
		responses_list = list()	#initialize an empty list

		for response in responses:
			response_values = list()
			response_data = response.response

			for field_name in form_fields:
				if field_name in response_data:
					response_values.append(response_data[field_name])
				else:
					response_values.append('')
			if any(response_values):	# a builtin python method that returns true if any of the values in the list evaluates to true
				responses_list.append(response_values)
			

		ctx['object_list'] = responses_list
		return ctx

	def get_queryset(self):
		form = self.get_form()
		return FormResponse.objects.filter(form=form)


	def get_form(self):
		return FormSchema.objects.get(pk=self.kwargs['form_pk'])


class CreateEditFormView(FormView):
	form_class = NewDynamicFormForm
	template_name = "create_edit_form.html"

	def get_initial(self):
		if "form_pk" in self.kwargs: # if the 'form_pk' kwarg was matched from the url
			form = FormSchema.objects.get(pk=self.kwargs['form_pk'])
			# initial data is from a FormSchema object.

			initial = {
				"form_pk": form.pk,
				"title": form.title,
				"schema": json.dumps(form.schema)	# converting from a python object to a json string
			}

		else:	# if not matched, we are creating a new form
			initial = {}
		return initial

	def get_context_data(self, **kwargs):
		ctx = super(CreateEditFormView, self).get_context_data(**kwargs)
		if 'form_pk' in self.kwargs:
			ctx['form_pk'] = self.kwargs['form_pk']
		return ctx

	def form_valid(self, form):
		cleaned_data = form.cleaned_data	# inbuilt method to clean form data

		if cleaned_data.get('form_pk'):
			old_form = FormSchema.objects.get(pk=cleaned_data['form_pk'])
			old_form.title = cleaned_data['title']
			old_form.schema = cleaned_data['schema']
			old_form.save()

		else:
			new_form = FormSchema(title=cleaned_data['title'], schema=cleaned_data['schema'])
			new_form.save()

		return HttpResponseRedirect(reverse('home'))











