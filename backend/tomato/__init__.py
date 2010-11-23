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

import os, sys
os.environ['DJANGO_SETTINGS_MODULE']="tomato.config"

def db_migrate():
	from django.core.management import call_command
	call_command('syncdb', verbosity=0)
	from south.management.commands import migrate
	cmd = migrate.Command()
	cmd.handle(app="tomato", verbosity=1)
db_migrate()

import config, log, generic, topology, hosts, fault, tasks
import tinc, kvm, openvz

def _resources_info(res):
	return {"disk": str(res.disk), "memory": str(res.memory), "ports": res.ports, "special": res.special}

def _topology_info(top, auth, detail):
	res = {"id": top.id, "name": top.name, "state": top.max_state(), "owner": str(top.owner),
		"device_count": len(top.devices_all()), "connector_count": len(top.connectors_all()),
		"date_created": top.date_created, "date_modified": top.date_modified, "date_usage": top.date_usage
		}
	if detail:
		try:
			analysis = top.analysis()
		except Exception, exc:
			analysis = "Error in analysis: %s" % exc
		res.update({"analysis": analysis, 
			"devices": [(v.name, _device_info(v, auth)) for v in top.devices_all()],
			"connectors": [(v.name, _connector_info(v, auth)) for v in top.connectors_all()]
			})
		if auth:
			task = top.get_task()
			if top.resources:
				res.update(resources=_resources_info(top.resources))
			if task:
				if task.is_active():
					res.update(running_task=task.id)
				else:
					res.update(finished_task=task.id)
			res.update(permissions=[p.dict() for p in top.permissions_all()])
			captures = []
			for con in top.connectors_all():
				for c in con.connections_all():
					c = c.upcast()
					if hasattr(c, "download_supported") and c.download_supported():
						captures.append({"connector":con.name, "device": c.interface.device.name, "interface": c.interface.name})
			res.update(captures=captures)
	return res

def _device_info(dev, auth):
	state = str(dev.state)
	res = {"name": dev.name, "type": dev.type, "host": str(dev.host),
		"state": state,
		"is_created": state == generic.State.CREATED,
		"is_prepared": state == generic.State.PREPARED,
		"is_started": state == generic.State.STARTED,
		"upload_supported": dev.upcast().upload_supported(),
		"download_supported": dev.upcast().download_supported(),
		}
	if auth:
		dev = dev.upcast()
		if dev.resources:
			res.update(resources=_resources_info(dev.resources))
		if hasattr(dev, "vnc_port") and dev.vnc_port:
			res.update(vnc_port=dev.vnc_port)
		if hasattr(dev, "vnc_password"):
			res.update(vnc_password=dev.vnc_password())
	return res

def _connector_info(con, auth):
	state = str(con.state)
	res = {"name": con.name, "type": ("special: %s" % con.upcast().feature_type if con.is_special() else con.type),
		"state": state,
		"is_created": state == generic.State.CREATED,
		"is_prepared": state == generic.State.PREPARED,
		"is_started": state == generic.State.STARTED,
		}
	if auth:
		if con.resources:
			res.update(resources=_resources_info(con.resources))
	return res

def _special_feature_info(sf):
	return {"type": sf.feature_type, "group": sf.feature_group, "bridge": sf.bridge}

def _host_info(host):
	return {"name": host.name, "group": host.group.name, "enabled": host.enabled, 
		"device_count": host.device_set.count(),
		"vmid_start": host.vmid_range_start, "vmid_count": host.vmid_range_count,
		"port_start": host.port_range_start, "port_count": host.port_range_count,
		"bridge_start": host.bridge_range_start, "bridge_count": host.bridge_range_count,
		"special_features": [_special_feature_info(sf) for sf in host.special_features()]}

def _template_info(template):
	return {"name": template.name, "type": template.type, "default": template.default, "url": template.download_url}

def _physical_link_info(link):
	return {"src": link.src_group.name, "dst": link.dst_group.name, "loss": link.loss, "delay_avg": link.delay_avg, "delay_stddev": link.delay_stddev}

def _top_access(top, role, user):
	if not top.check_access(role, user):
		raise fault.new(fault.ACCESS_TO_TOPOLOGY_DENIED, "access to topology %s denied" % top.id)

def _admin_access(user):
	if not user.is_admin:
		raise fault.new(fault.ACCESS_TO_HOST_DENIED, "access to host denied")
	
def login(username, password):
	if config.auth_dry_run:
		if username=="guest":
			return generic.User(username, False, False)
		elif username=="admin":
			return generic.User(username, True, True)
		else:
			return generic.User(username, True, False)
	else:
		import ldapauth
		return ldapauth.login(username, password)

def account(user=None):
	"""
	Returns details of the user account.
	"""
	return user

def host_info(hostname, user=None):
	"""
	Returns details about a host. If the host does not exist False is returned.
	"""
	try:
		return _host_info(hosts.get_host(hostname))
	except hosts.Host.DoesNotExist:
		return False

def host_list(group_filter="*", user=None):
	"""
	Returns details about all hosts as a list.
	"""
	res=[]
	qs = hosts.Host.objects.all()
	if not group_filter=="*":
		qs=qs.filter(group__name=group_filter)
	for h in qs:
		res.append(_host_info(h))
	return res

def host_add(host_name, group_name, enabled, vmid_start, vmid_count, port_start, port_count, bridge_start, bridge_count, user=None):
	_admin_access(user)
	return hosts.create(host_name, group_name, enabled, vmid_start, vmid_count, port_start, port_count, bridge_start, bridge_count)

def host_change(host_name, group_name, enabled, vmid_start, vmid_count, port_start, port_count, bridge_start, bridge_count, user=None):
	_admin_access(user)
	hosts.change(host_name, group_name, enabled, vmid_start, vmid_count, port_start, port_count, bridge_start, bridge_count)
	return True

def host_remove(host_name, user=None):
	_admin_access(user)
	host = hosts.get_host(host_name)
	if host.group.host_set.count()==1:
		host.group.delete()
	host.delete()
	return True

def host_debug(host_name, user=None):
	_admin_access(user)
	host = hosts.get_host(host_name)
	return host.debug_info()

def host_check(host_name, user=None):
	_admin_access(user)
	host = hosts.get_host(host_name)
	return hosts.host_check(host)

def host_groups(user=None):
	return [h.name for h in hosts.get_host_groups()]

def special_features_add(host_name, feature_type, feature_group, bridge, user=None):
	_admin_access(user)
	host = hosts.get_host(host_name)
	host.special_features_add(feature_type, feature_group, bridge)
	return True

def special_features_remove(host_name, feature_type, feature_group, user=None):
	_admin_access(user)
	host = hosts.get_host(host_name)
	host.special_features_remove(feature_type, feature_group)
	return True

def special_features_map(user=None):
	return hosts.special_feature_map()

def _parse_xml(xml, root_tag):
	try:
		from xml.dom import minidom
		dom = minidom.parseString(xml)
		return dom.getElementsByTagName ( root_tag )[0]
	except IndexError:
		raise fault.new(fault.MALFORMED_TOPOLOGY_DESCRIPTION, "Malformed xml: must contain a <%s> tag" % root_tag)
	except Exception, exc:
		raise fault.new(fault.MALFORMED_XML, "Malformed XML: %s" % exc )

def top_info(id, user=None):
	top = topology.get(id)
	return _topology_info(top, top.check_access("user", user), True)

def top_list(owner_filter, host_filter, access_filter, user=None):
	tops=[]
	all = topology.all()
	if not owner_filter=="*":
		all = all.filter(owner=owner_filter)
	if not host_filter=="*":
		all = all.filter(device__host__name=host_filter).distinct()
	for t in all:
		if access_filter=="*" or t.check_access(access_filter, user):
			tops.append(_topology_info(t, t.check_access("user", user), False))
	return tops
	
def top_get(top_id, include_ids=False, user=None):
	top = topology.get(top_id)
	_top_access(top, "user", user)
	from xml.dom import minidom
	doc = minidom.Document()
	dom = doc.createElement ( "topology" )
	top.save_to(dom, doc, include_ids)
	return dom.toprettyxml(indent="\t", newl="\n")

def top_import(xml, user=None):
	if not user.is_user:
		raise fault.new(fault.NOT_A_REGULAR_USER, "only regular users can create topologies")
	top=topology.create(user.name)
	top.save()
	import modification
	dom = _parse_xml(xml, "topology")
	modification.apply_spec(top.id, dom)
	top.logger().log("imported", user=user.name, bigmessage=xml)
	return top.id
	
def top_create(user=None):
	if not user.is_user:
		raise fault.new(fault.NOT_A_REGULAR_USER, "only regular users can create topologies")
	top=topology.create(user.name)
	top.save()
	top.logger().log("created", user=user.name)
	return top.id

def top_modify(top_id, xml, user=None):
	top = topology.get(top_id)
	_top_access(top, "manager", user)
	top.logger().log("modifying topology", user=user.name, bigmessage=xml)
	dom = _parse_xml(xml, "modifications")
	import modification
	task_id = modification.modify(top, dom)
	top.logger().log("started task %s" % task_id, user=user.name)
	return task_id

def top_remove(top_id, user=None):
	top = topology.get(top_id)
	_top_access(top, "owner", user)
	top.logger().log("removing topology", user=user.name)
	task_id = top.remove()
	top.logger().log("started task %s" % task_id, user=user.name)
	return task_id
	
def top_prepare(top_id, user=None):
	top = topology.get(top_id)
	_top_access(top, "manager", user)
	top.logger().log("preparing topology", user=user.name)
	task_id = top.prepare()
	top.logger().log("started task %s" % task_id, user=user.name)
	return task_id
	
def top_destroy(top_id, user=None):
	top = topology.get(top_id)
	_top_access(top, "manager", user)
	top.logger().log("destroying topology", user=user.name)
	task_id = top.destroy()
	top.logger().log("started task %s" % task_id, user=user.name)
	return task_id
	
def top_start(top_id, user=None):
	top = topology.get(top_id)
	_top_access(top, "user", user)
	top.logger().log("starting topology", user=user.name)
	task_id = top.start()
	top.logger().log("started task %s" % task_id, user=user.name)
	return task_id
	
def top_stop(top_id, user=None):
	top = topology.get(top_id)
	_top_access(top, "user", user)
	top.logger().log("stopping topology", user=user.name)
	task_id = top.stop()
	top.logger().log("started task %s" % task_id, user=user.name)
	return task_id

def top_renew(top_id, user=None):
	top = topology.get(top_id)
	_top_access(top, "user", user)
	top.logger().log("renewing topology", user=user.name)
	top.renew()
	return True

def device_prepare(top_id, device_name, user=None):
	top = topology.get(top_id)
	_top_access(top, "manager", user)
	top.logger().log("preparing device %s" % device_name, user=user.name)
	device = top.devices_get(device_name)
	task_id = device.prepare()
	top.logger().log("started task %s" % task_id, user=user.name)
	return task_id
	
def device_destroy(top_id, device_name, user=None):
	top = topology.get(top_id)
	_top_access(top, "manager", user)
	top.logger().log("destroying device %s" % device_name, user=user.name)
	device = top.devices_get(device_name)
	task_id = device.destroy()
	top.logger().log("started task %s" % task_id, user=user.name)
	return task_id
	
def device_start(top_id, device_name, user=None):
	top = topology.get(top_id)
	_top_access(top, "user", user)
	top.logger().log("starting device %s" % device_name, user=user.name)
	device = top.devices_get(device_name)
	task_id = device.start()
	top.logger().log("started task %s" % task_id, user=user.name)
	return task_id
	
def device_stop(top_id, device_name, user=None):
	top = topology.get(top_id)
	_top_access(top, "user", user)
	top.logger().log("stopping device %s" % device_name, user=user.name)
	device = top.devices_get(device_name)
	task_id = device.stop()
	top.logger().log("started task %s" % task_id, user=user.name)
	return task_id

def connector_prepare(top_id, connector_name, user=None):
	top = topology.get(top_id)
	_top_access(top, "manager", user)
	top.logger().log("preparing connector %s" % connector_name, user=user.name)
	connector = top.connectors_get(connector_name)
	task_id = connector.prepare()
	top.logger().log("started task %s" % task_id, user=user.name)
	return task_id
	
def connector_destroy(top_id, connector_name, user=None):
	top = topology.get(top_id)
	_top_access(top, "manager", user)
	top.logger().log("destroying connector %s" % connector_name, user=user.name)
	connector = top.connectors_get(connector_name)
	task_id = connector.destroy()
	top.logger().log("started task %s" % task_id, user=user.name)
	return task_id
	
def connector_start(top_id, connector_name, user=None):
	top = topology.get(top_id)
	_top_access(top, "user", user)
	top.logger().log("starting connector %s" % connector_name, user=user.name)
	connector = top.connectors_get(connector_name)
	task_id = connector.start()
	top.logger().log("started task %s" % task_id, user=user.name)
	return task_id
	
def connector_stop(top_id, connector_name, user=None):
	top = topology.get(top_id)
	_top_access(top, "user", user)
	top.logger().log("stopping connector %s" % connector_name, user=user.name)
	connector = top.connectors_get(connector_name)
	task_id = connector.stop()
	top.logger().log("started task %s" % task_id, user=user.name)
	return task_id

def task_list(user=None):
	return [t.dict() for t in tasks.TaskStatus.tasks.values()]

def task_status(id, user=None):
	return tasks.TaskStatus.tasks[id].dict()
	
def upload_start(user=None):
	task = tasks.UploadTask()
	return task.id

def upload_chunk(upload_id, chunk, user=None):
	task = tasks.UploadTask.tasks[upload_id]
	task.chunk(chunk.data)
	return 0

def upload_image(top_id, device_id, upload_id, user=None):
	upload = tasks.UploadTask.tasks[upload_id]
	upload.finished()
	top=topology.get(top_id)
	_top_access(top, "manager", user)
	top.logger().log("uploading image %s" % device_id, user=user.name)
	task_id =  top.upload_image(device_id, upload.filename)
	top.logger().log("started task %s" % task_id, user=user.name)
	return task_id

def download_image(top_id, device_id, user=None):
	top=topology.get(top_id)
	_top_access(top, "manager", user)
	filename = top.download_image(device_id)
	task = tasks.DownloadTask(filename)
	return task.id

def download_capture(top_id, connector_id, device_id, interface_id, user=None):
	top=topology.get(top_id)
	_top_access(top, "user", user)
	filename = top.download_capture(connector_id, device_id, interface_id)
	task = tasks.DownloadTask(filename)
	return task.id

def download_chunk(download_id, user=None):
	task = tasks.DownloadTask.tasks[download_id]
	data = task.chunk()
	import xmlrpclib
	return xmlrpclib.Binary(data)

def template_list(type, user=None):
	if type=="*":
		type = None
	return [_template_info(t) for t in hosts.get_templates(type)]

def template_add(name, type, url, user=None):
	_admin_access(user)
	return hosts.add_template(name, type, url)

def template_remove(name, user=None):
	_admin_access(user)
	hosts.remove_template(name)
	return True

def template_set_default(type, name, user=None):
	_admin_access(user)
	hosts.get_template(type, name).set_default()
	return True

def errors_all(user=None):
	_admin_access(user)
	return [f.dict() for f in fault.errors_all()]

def errors_remove(id, user=None):
	_admin_access(user)
	fault.errors_remove(id)
	return True

def permission_add(top_id, user_name, role, user=None):
	top = topology.get(top_id)
	_top_access(top, "owner", user)
	top.permissions_add(user_name, role)
	return True
	
def permission_remove(top_id, user_name, user=None):
	top = topology.get(top_id)
	_top_access(top, "owner", user)
	top.permissions_remove(user_name)
	return True
		
def resource_usage_by_user(user=None):
	_admin_access(user)
	usage={}
	for top in topology.all():
		if not top.owner in usage:
			usage[top.owner] = generic.Resources()
		if top.resources:
			usage[top.owner].add(top.resources)
	for owner in usage:
		usage[owner]=_resources_info(usage[owner])
	return usage
		
def resource_usage_by_topology(user=None):
	_admin_access(user)
	usage={}
	for top in topology.all():
		if top.resources:
			d = _resources_info(top.resources)
			d.update(top_id=top.id)
			usage[top.name]=d
	return usage

def physical_links_get(src_group, dst_group, user=None):
	return _physical_link_info(hosts.get_physical_link(src_group, dst_group))
	
def physical_links_get_all(user=None):
	return [_physical_link_info(l) for l in hosts.get_all_physical_links()]