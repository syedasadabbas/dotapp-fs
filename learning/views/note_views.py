import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from learning.forms import NoteForm
from learning.models import Note, Progress
from editor.models import SubDot

@login_required
def add_note(request, subdot_id):
    subdot = get_object_or_404(SubDot, id=subdot_id)
    if request.method == 'POST':
        form = NoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.learner = request.user.learnerprofile
            note.subdot = subdot
            note.save()
            messages.success(request, 'Note added successfully!')
        else:
            messages.error(request, 'Please check your input and try again.')
    return redirect('subdot_detail', subdot_id=subdot_id)

@require_http_methods(["POST"])
def create_note(request):
    try:
        data = json.loads(request.body)
        content = data.get('content')
        subdot_id = data.get('subdot_id')

        if not content or not subdot_id:
            return JsonResponse({'success': False, 'error': 'Missing required fields'}, status=400)

        subdot = get_object_or_404(SubDot, id=subdot_id)
        note = Note.objects.create(
            learner=request.user.learnerprofile,
            subdot=subdot,
            content=content
        )

        return JsonResponse({
            'success': True,
            'note': {
                'id': note.id,
                'content': note.content,
                'subdot': {
                    'id': subdot.id,
                    'title': subdot.title
                },
                'updated_at': note.updated_at.strftime("%b %d, %Y %H:%M")
            }
        })
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["PUT"])
def update_note(request, note_id):
    try:
        data = json.loads(request.body)
        content = data.get('content')

        if not content:
            return JsonResponse({'success': False, 'error': 'Content is required'}, status=400)

        note = Note.objects.get(id=note_id, learner=request.user.learnerprofile)
        note.content = content
        note.updated_at = timezone.now()
        note.save()

        return JsonResponse({
            'success': True,
            'note': {
                'id': note.id,
                'content': note.content,
                'subdot': {
                    'id': note.subdot.id,
                    'title': note.subdot.title
                },
                'updated_at': note.updated_at.strftime("%b %d, %Y %H:%M")
            }
        })
    except Note.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Note not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["DELETE"])
def delete_note(request, note_id):
    try:
        note = Note.objects.get(id=note_id, learner=request.user.learnerprofile)
        note.delete()
        return JsonResponse({'success': True})
    except Note.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Note not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["GET"])
def get_note(request, note_id):
    try:
        note = Note.objects.get(id=note_id, learner=request.user.learnerprofile)
        return JsonResponse({
            'success': True,
            'note': {
                'id': note.id,
                'content': note.content,
                'subdot': {
                    'id': note.subdot.id,
                    'title': note.subdot.title
                },
                'updated_at': note.updated_at.strftime("%b %d, %Y %H:%M")
            }
        })
    except Note.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Note not found'}, status=404)

@require_http_methods(["GET"])
def get_all_notes(request, subdot_id):
    try:
        notes = Note.objects.filter(learner=request.user.learnerprofile, subdot_id=subdot_id).order_by('-updated_at')
        return JsonResponse({
            'success': True,
            'notes': [{
                'id': note.id,
                'content': note.content,
                'subdot': {
                    'id': note.subdot.id,
                    'title': note.subdot.title
                },
                'updated_at': note.updated_at.strftime("%b %d, %Y %H:%M")
            } for note in notes]
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
