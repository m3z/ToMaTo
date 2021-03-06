# -*- coding: utf-8 -*-

# ToMaTo (Topology management software) 
# Copyright (C) 2010 Dennis Schwerdel, University of Kaiserslautern
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
	(r'^$', 'tomato.main.index'),
	(r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': 'static'}),
	(r'^help$', 'tomato.main.help'),
	(r'^help/(?P<page>.*)$', 'tomato.main.help'),
	(r'^ticket$', 'tomato.main.ticket'),
	(r'^project$', 'tomato.main.project'),
	(r'^logout$', 'tomato.main.logout'),
	(r'^link_stats$', 'tomato.main.physical_links'),
	(r'^statistics$', 'tomato.main.statistics'),
	(r'^resource_stats/by_topology$', 'tomato.main.resource_usage_by_topology'),
	(r'^resource_stats/by_user$', 'tomato.main.resource_usage_by_user'),
	(r'^errors$', 'tomato.main.error_list'),
	(r'^errors/remove/(?P<error_id>.*)$', 'tomato.main.error_remove'),
	(r'^tasks$', 'tomato.main.task_list'),
	(r'^task/run/(?P<task>.*)$', 'tomato.main.task_run'),
	(r'^task/(?P<task_id>.*)$', 'tomato.main.task_status'),
	(r'^top/$', 'tomato.top.index'),
	(r'^top\?host_filter=(?P<host_filter>.*)$', 'tomato.top.index'),
	(r'^top/create$', 'tomato.top.create'),
	(r'^top/import$', 'tomato.top.import_form'),
	(r'^top/(?P<top_id>\d+)/edit$', 'tomato.top.edit'),
	(r'^top/(?P<top_id>\d+)/show$', 'tomato.top.show'),
	(r'^top/(?P<top_id>\d+)/export$', 'tomato.top.export'),
	(r'^top/(?P<top_id>\d+)/remove$', 'tomato.top.remove'),
	(r'^top/(?P<top_id>\d+)/renew$', 'tomato.top.renew'),
	(r'^top/console/$', 'tomato.top.console'),
	(r'^host/$', 'tomato.host.index'),
	(r'^host/public_key$', 'tomato.host.public_key'),
	(r'^host/(?P<hostname>.*)/devices$', 'tomato.host.device_list'),
	(r'^host/(?P<hostname>.*)/device_migrate/(?P<topid>\d+)/(?P<devname>.*)$', 'tomato.host.device_migrate'),
	(r'^host/(?P<hostname>.*)/detail$', 'tomato.host.detail'),
	(r'^host/(?P<hostname>.*)/remove$', 'tomato.host.remove'),
	(r'^host/(?P<hostname>.*)/debug$', 'tomato.host.debug'),
	(r'^host/(?P<hostname>.*)/check$', 'tomato.host.check'),
	(r'^host/(?P<hostname>.*)/update$', 'tomato.host.update'),
	(r'^host/(?P<hostname>.*)/edit$', 'tomato.host.edit'),
	(r'^host/add$', 'tomato.host.edit', {"hostname": None}),
	(r'^external_networks$', 'tomato.external_networks.index'),
	(r'^external_networks/add$', 'tomato.external_networks.add'),
	(r'^external_networks/(?P<type>.*)/(?P<group>.*)/remove$', 'tomato.external_networks.remove'),
	(r'^external_networks/(?P<type>.*)/(?P<group>.*)/change$', 'tomato.external_networks.change'),
	(r'^external_networks/addbridge', 'tomato.external_networks.add_bridge'),
	(r'^external_networks/(?P<type>.*)/(?P<group>.*)/removebridge/(?P<hostname>.*)$', 'tomato.external_networks.remove_bridge'),
	(r'^template/$', 'tomato.template.index'),
	(r'^template/add$', 'tomato.template.add'),
	(r'^template/detail/(?P<type>.*)/(?P<name>.*)$', 'tomato.template.detail'),
	(r'^template/edit/(?P<type>.*)/(?P<name>.*)$', 'tomato.template.edit'),
	(r'^template/remove/(?P<type>.*)/(?P<name>.*)$', 'tomato.template.remove'),
	(r'^template/set_default/(?P<type>.*)/(?P<name>.*)$', 'tomato.template.set_default'),
	(r'^device_profile/$', 'tomato.device_profile.index'),
	(r'^device_profile/add$', 'tomato.device_profile.add'),
	(r'^device_profile/detail/(?P<type>.*)/(?P<name>.*)$', 'tomato.device_profile.detail'),
	(r'^device_profile/edit/(?P<type>.*)/(?P<name>.*)$', 'tomato.device_profile.edit'),
	(r'^device_profile/remove/(?P<type>.*)/(?P<name>.*)$', 'tomato.device_profile.remove'),
	(r'^device_profile/set_default/(?P<type>.*)/(?P<name>.*)$', 'tomato.device_profile.set_default'),
	(r'^ajax/top/(?P<top_id>\d+)/modify$', 'tomato.ajax.modify'),
	(r'^ajax/top/(?P<top_id>\d+)/info$', 'tomato.ajax.info'),
	(r'^ajax/top/(?P<top_id>\d+)/action$', 'tomato.ajax.action'),
	(r'^ajax/top/(?P<top_id>\d+)/permission$', 'tomato.ajax.permission'),
	(r'^ajax/top/(?P<top_id>\d+)/upload_image_uri/(?P<device>.*)$', 'tomato.ajax.upload_image_uri'),
	(r'^ajax/top/(?P<top_id>\d+)/download_image_uri/(?P<device>.*)$', 'tomato.ajax.download_image_uri'),
	(r'^ajax/top/(?P<top_id>\d+)/use_uploaded_image/(?P<device>.*)$', 'tomato.ajax.use_uploaded_image'),
	(r'^ajax/task/(?P<task_id>.*)$', 'tomato.ajax.task_status'),
	(r'^ajax/top/(?P<top_id>\d+)/download_capture_uri/(?P<connector>.*)/(?P<ifname>.*)$', 'tomato.ajax.download_capture_uri'),
	(r'^ajax/template/(?P<type>.*)/(?P<name>.*)/info$', 'tomato.ajax.template_info'),
)
