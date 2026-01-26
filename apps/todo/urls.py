from django.urls import path

from apps.todo import views

app_name = "todo"

urlpatterns = [
	path("", views.TodoListView.as_view(), name="list"),
	path("new/", views.TodoCreateView.as_view(), name="create"),
	path("<int:pk>/", views.TodoDetailView.as_view(), name="detail"),
	path("<int:pk>/edit/", views.TodoUpdateView.as_view(), name="edit"),
	path("<int:pk>/toggle/", views.todo_toggle_view, name="toggle"),
	path("<int:pk>/delete/", views.TodoDeleteView.as_view(), name="delete"),
]
