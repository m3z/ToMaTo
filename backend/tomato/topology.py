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

from django.db import models
import os, datetime
import attributes, auth, config
from lib import db, util
from lib.decorators import *

class Topology(db.ReloadMixin, attributes.Mixin, models.Model):
	"""
	This class represents a whole topology and offers methods to work with it
	"""
	
	id = models.AutoField(primary_key=True)
	# The id of the topology, this is an assigned value
	
	name = models.CharField(max_length=30, blank=True)
	# The name of the topology.

	owner = models.ForeignKey(auth.User)

	date_usage = models.DateTimeField(null=True)
	
	task = models.CharField(max_length=250, null=True)
		
	attrs = db.JSONField(default={})
		
	STOP_TIMEOUT = datetime.timedelta(weeks=config.TIMEOUTS["STOP"])
	DESTROY_TIMEOUT = datetime.timedelta(weeks=config.TIMEOUTS["DESTROY"])
	REMOVE_TIMEOUT = datetime.timedelta(weeks=config.TIMEOUTS["REMOVE"])

	class Meta:
		ordering=["-id"]	

	def _logger(self):
		if not os.path.exists(config.LOG_DIR + "/top"):
			os.makedirs(config.LOG_DIR + "/top")
		return log.getLogger(config.LOG_DIR + "/top/%s"%self.id)

	def log(self, *args, **kwargs):
		with self._logger() as logger:
			logger.log(*args, **kwargs)

	def init (self, owner):
		"""
		Creates a new topology
		@param owner the owner of the topology
		"""
		self.owner=owner
		self.date_usage = datetime.datetime.now()
		self.save()
		self.name = "Topology_%s" % self.id
		self.save()
		self.renew()

	def renew(self):
		if self.id:
			self.reload()
		if self.date_usage:
			self.date_usage = datetime.datetime.now()
		self.setAttribute("timeout_warning", None)
		self.save()
		
	def maxState(self):
		max_state = generic.State.CREATED
		for con in self.connectorSetAll():
			if not con.isExternal():
				if con.state == generic.State.PREPARED and max_state == generic.State.CREATED:
					max_state = generic.State.PREPARED
				if con.state == generic.State.STARTED and (max_state == generic.State.CREATED or max_state == generic.State.PREPARED):
					max_state = generic.State.STARTED
		for dev in self.deviceSetAll():
			if dev.state == generic.State.PREPARED and max_state == generic.State.CREATED:
				max_state = generic.State.PREPARED
			if dev.state == generic.State.STARTED and (max_state == generic.State.CREATED or max_state == generic.State.PREPARED):
				max_state = generic.State.STARTED
		return max_state

	def checkTimeout(self):
		now = datetime.datetime.now()
		date = self.date_usage
		max_state = self.maxState()
		if not date:
			return
		if max_state == generic.State.STARTED:
			self._timeoutActionWarning("stop", date + self.STOP_TIMEOUT)
		if max_state == generic.State.PREPARED or max_state == generic.State.STARTED:
			self._timeoutActionWarning("destroy", date + self.DESTROY_TIMEOUT)
		self._timeoutActionWarning("remove", date + self.REMOVE_TIMEOUT)
		if now > date + self.REMOVE_TIMEOUT:
			self._logTimeoutAction("remove")
			self.remove(True)
		elif now > date + self.DESTROY_TIMEOUT:
			if max_state == generic.State.PREPARED or max_state == generic.State.STARTED:
				self._logTimeoutAction("destroy")
				self.destroy(False)
		elif now > date + self.STOP_TIMEOUT:
			if max_state == generic.State.STARTED:
				self._logTimeoutAction("stop")
				self.stop(False)

	def _logTimeoutAction(self, action):
		now = datetime.datetime.now()
		self.log("timeout: %s" % action)
		out = tasks.get_current_task().output
		out.write("TIMEOUT %s topology %s [%d]" % (action, self.name, self.id))
		data = {"name": self.name, "owner": str(self.owner), "id": self.id, "action": {"stop": "STOPPED", "destroy": "DESTROYED", "remove": "REMOVED"}.get(action), "date": now}
		fault.log_info("Topology %(name)s [%(id)d] of %(owner)s %(action)s due to timeout" % data, "")
		self._sendToUsers("Topology timeout notification", "the topology \"%(name)s\" (ID %(id)d) has been %(action)s at %(date)s due to a timeout." % data)

	def _timeoutActionWarning(self, action, when):
		now = datetime.datetime.now()
		if when < now or when > now + datetime.timedelta(days=config.TIMEOUT_WARNING):
			#not within next week
			return
		if self.getAttribute("timeout_warning", None) == action:
			#already warned 
			return
		data = {"name": self.name, "id": self.id, "action": {"stop": "STOPPED", "destroy": "DESTROYED", "remove": "REMOVED"}.get(action), "date": when}
		self._sendToUsers("Topology timeout warning", "the topology \"%(name)s\" (ID %(id)d) will be %(action)s at %(date)s due to a timeout.\nPlease log in to ToMaTo to renew the topology and prevent the timeout." % data)
		self.setAttribute("timeout_warning", action)
		
	def _sendToUsers(self, subject, body):
		self.owner.sendMessage(subject, body)
		for perm in self.permissionsAll():
			perm.user.sendMessage(subject, body)
		
	def getTask(self):
		if not self.task:
			return None
		if not tasks.processes.has_key(self.task):
			return None
		return tasks.processes[self.task]

	def isBusy(self):
		t = self.getTask()
		if not t:
			return False
		return t.isActive()

	def checkBusy(self):
		fault.check(not self.isBusy(), "Topology is busy with a task")

	def startProcess(self, process, direct=False):
		self.checkBusy()
		self.task = process.id
		self.save()
		try:	
			return process.start(direct)
		except:
			if not process.isDone():
				self.task = None
				self.save()
		return process.dict(True)

	def deviceSetAll(self):
		return self.device_set.all() # pylint: disable-msg=E1101
	
	def deviceSetGet(self, name):
		return self.device_set.get(name=name).upcast() # pylint: disable-msg=E1101
	
	def interfacesGet(self, iface_name):
		iface_name = iface_name.split(".")
		return self.deviceSetGet(iface_name[0]).interfaceSetGet(iface_name[1])

	def deviceSetAdd(self, dev):
		exists = self.device_set.filter(name=dev.name).exclude(id=dev.id).count() > 0
		fault.check(not exists, "Duplicate device id: %s", dev.name)
		self.device_set.add(dev) # pylint: disable-msg=E1101

	def connectorSetAll(self):
		return self.connector_set.all() # pylint: disable-msg=E1101
	
	def connectorSetGet(self, name):
		return self.connector_set.get(name=name).upcast() # pylint: disable-msg=E1101

	def connectorSetAdd(self, con):
		exists = self.connector_set.filter(name=con.name).exclude(id=con.id).count() > 0 # pylint: disable-msg=E1101
		fault.check(not exists, "Duplicate connector id: %s", con.name)
		self.connector_set.add(con) # pylint: disable-msg=E1101

	def affectedHosts (self):
		"""
		The set of all hosts that this topology has devices on.
		"""
		import hosts
		return hosts.Host.objects.filter(device__topology=self).distinct() # pylint: disable-msg=E1101
	
	def getControlDir(self,host_name):
		"""
		The local directory where all control scripts and files are stored.
		@param host_name the name of the host for the deployment
		"""
		return config.LOCAL_TMP_DIR+"/"+host_name

	def getRemoteControlDir(self):
		"""
		The remote directory where all control scripts and files will be copied to.
		"""
		return config.REMOTE_DIR+"/"+str(self.id)

	def _selectHosts(self):
		for dev in self.deviceSetAll():
			if dev.state == generic.State.CREATED:
				dev.upcast().selectHost()

	def _getTasks(self):
		tmap = {"start": {}, "stop": {}, "prepare": {}, "destroy": {}}
		for dev in self.deviceSetAll():
			tmap["start"][dev] = dev.upcast().getStartTasks().prefix("start-%s" % dev)
			tmap["stop"][dev] = dev.upcast().getStopTasks().prefix("stop-%s" % dev)
			tmap["prepare"][dev] = dev.upcast().getPrepareTasks().prefix("prepare-%s" % dev)
			tmap["destroy"][dev] = dev.upcast().getDestroyTasks().prefix("destroy-%s" % dev)
		for con in self.connectorSetAll():
			tmap["start"][con] = con.upcast().getStartTasks().prefix("start-%s" % con)
			tmap["stop"][con] = con.upcast().getStopTasks().prefix("stop-%s" % con)
			tmap["prepare"][con] = con.upcast().getPrepareTasks().prefix("prepare-%s" % con)
			tmap["destroy"][con] = con.upcast().getDestroyTasks().prefix("destroy-%s" % con)
		return tmap
		
	def _stateForward(self, start, direct):
		proc = tasks.Process("topology-%s" % "start" if start else "prepare")
		proc.add(tasks.Task("renew", self.renew))
		tmap = self._getTasks()
		select_hosts = tasks.Task("select-hosts", self._selectHosts())
		proc.add(select_hosts)
		devs_prepared = tasks.Task("devices_prepared")
		for dev in self.deviceSetAll():
			if dev.state == generic.State.CREATED:
				t = tmap["prepare"][dev]
				proc.add(t)
				t.after(select_hosts)
				devs_prepared.after(t)
		cons_prepared = tasks.Task("connectors_prepared")
		for con in self.connectorSetAll():
			if con.state == generic.State.CREATED:
				t = tmap["prepare"][con]
				t.after(devs_prepared)
				proc.add(t)
				cons_prepared.after(t)
		proc.add([devs_prepared, cons_prepared])		
		if start:
			for dev in self.deviceSetAll():
				if dev.state != generic.State.STARTED:
					t = tmap["start"][dev]
					t.after([devs_prepared,cons_prepared])
					proc.add(t)
			for con in self.connectorSetAll():
				if con.state != generic.State.STARTED:
					t = tmap["start"][con]
					t.after([devs_prepared,cons_prepared])
					proc.add(t)
		return self.startProcess(proc, direct)

	def prepare(self, direct):
		return self._stateForward(False, direct)

	def start(self, direct):
		return self._stateForward(True, direct)

	def _stateBackward(self, destroy, remove, direct, renew):
		proc = tasks.Process("topology-%s" % "remove" if remove else "destroy" if destroy else "stop")
		if renew:
			proc.add(tasks.Task("renew", self.renew))
		tmap = self._getTasks()
		devs_stopped = tasks.Task("devices_stopped")
		for dev in self.deviceSetAll():
			if dev.state == generic.State.STARTED:
				t = tmap["stop"][dev]
				proc.add(t)
				devs_stopped.after(t)
		cons_stopped = tasks.Task("connectors_stopped")
		for con in self.connectorSetAll():
			if con.state == generic.State.STARTED:
				t = tmap["stop"][con]
				proc.add(t)
				cons_stopped.after(t)
		proc.add([devs_stopped, cons_stopped])		
		if destroy:
			cons_destroyed = tasks.Task("connectors_destroyed")
			for con in self.connectorSetAll():
				if con.state != generic.State.CREATED:
					t = tmap["destroy"][con]
					t.after([devs_stopped,cons_stopped])
					proc.add(t)
					cons_destroyed.after(t)
			devs_destroyed = tasks.Task("devices_destroyed")
			for dev in self.deviceSetAll():
				if dev.state != generic.State.CREATED:
					t = tmap["destroy"][dev]
					t.after([devs_stopped,cons_destroyed])
					proc.add(t)
					devs_destroyed.after(t)
			proc.add([devs_destroyed, cons_destroyed])		
			if remove:
				proc.add(tasks.Task("remove", self.delete, after=[devs_destroyed, cons_destroyed]))
		return self.startProcess(proc, direct)

	def stop(self, direct, renew=True):
		return self._stateBackward(False, False, direct, renew)

	def destroy(self, direct, renew=True):
		return self._stateBackward(True, False, direct, renew)

	def remove(self, direct):
		return self._stateBackward(True, True, direct, False)
			
	def _log(self, task, output):
		with log.getLogger(config.LOG_DIR+"/top_%s.log" % self.id) as logger:
			logger.log(task, bigmessage=output)
		
	def getCapabilities(self, user):
		isOwner = self.checkAccess(Permission.ROLE_OWNER, user)
		isManager = self.checkAccess(Permission.ROLE_MANAGER, user)
		isUser = self.checkAccess(Permission.ROLE_USER, user)
		isBusy = self.isBusy()
		return {
			"action": {
				"start": isUser and not isBusy, 
				"stop": isUser and not isBusy,
				"prepare": isManager and not isBusy,
				"destroy": isManager and not isBusy,
				"remove": isOwner and not isBusy,
				"renew": isUser,
				"disable_timeout": user.is_admin	
			},
			"modify": isManager and not isBusy,
			"permission_set": isOwner
		}
		
	def action(self, user, action, attrs, direct):
		capabilities = self.getCapabilities(user)
		fault.check(action in capabilities["action"], "Unknown action: %s", action)
		fault.check(capabilities["action"][action], "Action %s not available", action)
		if action == "start":
			return self.start(direct)
		elif action == "stop":
			return self.stop(direct)
		elif action == "prepare":
			return self.prepare(direct)
		elif action == "destroy":
			return self.destroy(direct)
		elif action == "remove":
			return self.remove(direct)
		elif action == "renew":
			return self.renew()
		elif action == "disable_timeout":
			self.date_usage = None
			self.save()
		
	def permissionsAdd(self, user_name, role):
		self.renew()
		user = auth.getUser(user_name)
		fault.check(user, "Unknown user: %s", user_name)
		self.permission_set.add(Permission(user=user, role=role)) # pylint: disable-msg=E1101
		self.save()
	
	def permissionsAll(self):
		return self.permission_set.all() # pylint: disable-msg=E1101
	
	def permissionsRemove(self, user_name):
		self.renew()
		user = auth.getUser(user_name)
		fault.check(user, "Unknown user: %s", user_name)
		self.permission_set.filter(user=user).delete() # pylint: disable-msg=E1101
		self.save()
		
	def permissionsGet(self, user):
		pset = self.permission_set.filter(user=user) # pylint: disable-msg=E1101
		if pset.count() > 0:
			return pset[0].role
		else:
			return None
		
	def checkAccess(self, atype, user):
		if user.is_admin:
			return True
		if user == self.owner:
			return True
		if atype == Permission.ROLE_MANAGER:
			return self.permissionsGet(user) == Permission.ROLE_MANAGER
		if atype == Permission.ROLE_USER:
			return self.permissionsGet(user) in [Permission.ROLE_USER, Permission.ROLE_MANAGER]

	def resources(self):
		return self.getAttribute("resources")

	def getIdUsage(self, host):
		ids = {}
		for dev in self.deviceSetAll():
			for (key, value) in dev.upcast().getIdUsage(host).iteritems():
				ids[key] = ids.get(key, set()) | value
		for con in self.connectorSetAll():
			for (key, value) in con.upcast().getIdUsage(host).iteritems():
				ids[key] = ids.get(key, set()) | value
		return ids

	def updateResourceUsage(self):
		res = {}
		for dev in self.deviceSetAll():
			try:
				dev.updateResourceUsage()
			except Exception, exc:
				fault.log(exc)
			r = dev.getAttribute("resources", {})
			for key in r:
				if not key in res:
					res[key] = 0
				res[key] += r[key]
		for con in self.connectorSetAll():
			try:
				con.updateResourceUsage()
			except Exception, exc:
				fault.log(exc)
			r = con.getAttribute("resources", {})
			for key in r:
				if not key in res:
					res[key] = 0
				res[key] += r[key]
		res["traffic"] = res.get("traffic", 0)/2 #traffic is counted on devices and connectors
		self.setAttribute("resources", res)
		
	def repair(self):
		if self.isBusy():
			return
		for dev in self.deviceSetAll():
			try:
				dev.upcast().repair()
			except Exception, exc:
				fault.log(exc)
		for con in self.connectorSetAll():
			try:
				con.upcast().repair()
			except Exception, exc:
				fault.log(exc)

	def configure(self, properties):
		self.setPrivateAttributes(properties)			
					
	@xmlRpcSafe
	def toDict(self, user, detail):
		res = {"id": self.id, 
			"attrs": {"name": self.name, "state": self.maxState(), "owner": str(self.owner),
					"device_count": len(self.deviceSetAll()), "connector_count": len(self.connectorSetAll()),
					},
			"resources": util.xml_rpc_sanitize(self.resources()),
			}
		if self.checkAccess(Permission.ROLE_USER, user):
			task = self.getTask()
			if task:
				if task.isActive():
					res.update(running_task=task.id)
				else:
					res.update(finished_task=task.id)
		if self.date_usage:
			res["attrs"].update(stop_timeout=str(self.date_usage + self.STOP_TIMEOUT), destroy_timeout=str(self.date_usage + self.DESTROY_TIMEOUT), remove_timeout=str(self.date_usage + self.REMOVE_TIMEOUT)) 
		else:
			res["attrs"].update(timeouts_disabled=True)
		if detail:
			res.update({"devices": dict([[v.name, v.upcast().toDict(user)] for v in self.deviceSetAll()]),
				"connectors": dict([[v.name, v.upcast().toDict(user)] for v in self.connectorSetAll()])
				})
			res.update(permissions=dict([[str(p.user), p.role] for p in self.permissionsAll()]))
			res["permissions"][str(self.owner)]="owner"
			res["capabilities"] = self.getCapabilities(user)
			res["resources"] = util.xml_rpc_sanitize(self.resources())
			res["attrs"].update(self.getPrivateAttributes())
		return res
						
class Permission(models.Model):
	ROLE_USER="user"
	ROLE_MANAGER="manager"
	ROLE_OWNER="owner"
	topology = models.ForeignKey(Topology)
	user = models.ForeignKey(auth.User)
	role = models.CharField(max_length=10, choices=((ROLE_USER, 'User'), (ROLE_MANAGER, 'Manager')))

	class Meta:
		unique_together = (("topology", "user"),)
		ordering=["role", "user"]

def get(top_id):
	try:
		return Topology.objects.get(id=top_id) # pylint: disable-msg=E1101
	except Topology.DoesNotExist: # pylint: disable-msg=E1101
		raise fault.new("No such topology: %s" % top_id, fault.USER_ERROR)

def all(): #pylint: disable-msg=W0622
	return Topology.objects.all() # pylint: disable-msg=E1101

def create(owner):
	top = Topology()
	top.init(owner)
	return top

def checkTimeout():
	for top in all():
		top.checkTimeout()

def updateResourceUsage():
	for top in all():
		top.updateResourceUsage()
		
def repairAll():
	for top in all():
		top.repair()
			
import fault, generic
from lib import log, tasks
