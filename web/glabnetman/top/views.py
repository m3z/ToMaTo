# -*- coding: utf-8 -*-

from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.http import Http404

from lib import *
import xmlrpclib

def index(request):
	try:
		if not getapi(request):
			return HttpResponseNotAuthorized("Authorization required!")
		api = request.session.api
		return render_to_response("top/index.html", {'top_list': api.top_list()})
	except xmlrpclib.Fault, f:
		return render_to_response("main/error.html", {'error': f})

def create(request):
	try:
		if not request.REQUEST.has_key("xml"):
			return render_to_response("top/create.html")
		xml=request.REQUEST["xml"]
		if not getapi(request):
			return HttpResponseNotAuthorized("Authorization required!")
		api = request.session.api
		top_id=api.top_import(xml)
		top=api.top_info(int(top_id))
		return render_to_response("top/detail.html", {'top_id': top_id, 'top': top})
	except xmlrpclib.Fault, f:
		return render_to_response("main/error.html", {'error': f})
	
def action(request, top_id, action=None):
	try:
		if not getapi(request):
			return HttpResponseNotAuthorized("Authorization required!")
		api = request.session.api
		if action=="showxml":
			xml=api.top_get(int(top_id))
			if request.REQUEST.has_key("plain"):
				return HttpResponse(xml, mimetype="text/plain")
			else:
				top=api.top_info(int(top_id))
				return render_to_response("top/showxml.html", {'top_id': top_id, 'top': top, 'xml': xml})
		if action=="remove":
			api.top_remove(int(top_id))
			return index(request)
		task_id=None
		if action=="upload":
			task_id=api.top_upload(int(top_id))
		elif action=="prepare":
			task_id=api.top_prepare(int(top_id))
		elif action=="destroy":
			task_id=api.top_destroy(int(top_id))
		elif action=="start":
			task_id=api.top_start(int(top_id))
		elif action=="stop":
			task_id=api.top_stop(int(top_id))
		top=api.top_info(int(top_id))
		if not top:
			raise Http404
		return render_to_response("top/detail.html", {'top_id': top_id, 'top': top, 'action' : action, 'task_id' : task_id })
	except xmlrpclib.Fault, f:
		return render_to_response("main/error.html", {'error': f})