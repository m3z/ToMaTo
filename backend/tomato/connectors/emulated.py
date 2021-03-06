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

from tomato.connectors import Connection
from tomato.generic import State
from tomato.topology import Permission
from tomato.lib import db, tc, tcpdump, tasks, ifaceutil
from tomato import fault
from tomato.hosts import resources

DEFAULT_CAPTURE_FILTER = ""
DEFAULT_CAPTURE_TO_FILE = False
DEFAULT_CAPTURE_VIA_NET = False

netemProperties = ["bandwidth", "delay", "jitter", "distribution", "lossratio", "lossratio_correlation", "duplicate", "corrupt"]
netemDefaults = {"bandwidth": 10000.0, "distribution": None}
netemValueConvert = {
	"bandwidth": lambda x: float(x if x else netemDefaults["bandwidth"]),
	"delay": lambda x: float(x if x else 0.0),
	"jitter": lambda x: float(x if x else 0.0),
	"delay_correlation": lambda x: float(x if x else 0.0),
	"distribution": lambda x: x if x in ["normal", "pareto", "paretonormal"] else None,
	"lossratio": lambda x: float(x if x else 0.0),
	"lossratio_correlation": lambda x: float(x if x else 0.0),
	"duplicate": lambda x: float(x if x else 0.0),
	"corrupt": lambda x: float(x if x else 0.0),	
}
netemValuesChecks = {
	"bandwidth": lambda x: x > 0.0,
	"delay": lambda x: x >= 0.0,
	"jitter": lambda x: x >= 0.0,
	"delay_correlation": lambda x: 0.0 <= x <= 100.0,
	"distribution": lambda x: x is None or x in ["normal", "pareto", "paretonormal"],
	"lossratio": lambda x: 0.0 <= x <= 100.0,
	"lossratio_correlation": lambda x: 0.0 <= x <= 100.0,
	"duplicate": lambda x: 0.0 <= x <= 100.0,
	"corrupt": lambda x: 0.0 <= x <= 100.0,
}

class EmulatedConnection(Connection):
	
	live_capture_port = models.ForeignKey(resources.ResourceEntry, null=True, related_name='+')
	LIVE_CAPTURE_PORT_SLOT = "lc"
	ifb_id = models.ForeignKey(resources.ResourceEntry, null=True, related_name='+')
	IFB_ID_SLOT = "ifb"

	class Meta:
		db_table = "tomato_emulatedconnection"
		app_label = 'tomato'

	@db.changeset
	def init(self):
		self.attrs = {}
		self.setCaptureFilter("")
		self.setCaptureToFile(False)
		self.setCaptureViaNet(False)
		for prop in netemProperties:
			val = netemValueConvert[prop]("")
			self.setAttribute(prop+"_to", val)
			self.setAttribute(prop+"_from", val)
		self.save()
	
	def upcast(self):
		if self.isVPN():
			return self.tincconnection # pylint: disable-msg=E1101
		return self

	def isVPN(self):
		try:
			self.tincconnection # pylint: disable-msg=E1101,W0104
			return True
		except: #pylint: disable-msg=W0702
			return False
			
	def getLiveCapturePort(self):
		res = resources.get(self, self.LIVE_CAPTURE_PORT_SLOT, "live_capture_port")
		if res:
			return res.num

	def getIfbId(self):
		res = resources.get(self, self.IFB_ID_SLOT, "ifb_id")
		if res:
			return res.num
		
	def hasIfbId(self):
		return resources.get(self, self.IFB_ID_SLOT, "ifb_id")
				
	def getNetemProp(self, prop, dir=None):
		if dir == "to":
			return self.getAttribute(prop+"_to", self.getNetemProp(prop))
		if dir == "from":
			return self.getAttribute(prop+"_from", self.getNetemProp(prop))
		return self.getAttribute(prop, netemDefaults.get(prop, 0.0))
				
	def getCaptureFilter(self):
		return self.getAttribute("capture_filter", DEFAULT_CAPTURE_FILTER)
	
	def setCaptureFilter(self, value):
		self.setAttribute("capture_filter", str(value))

	def getCaptureToFile(self):
		return self.getAttribute("capture_to_file", DEFAULT_CAPTURE_TO_FILE)
	
	def setCaptureToFile(self, value):
		self.setAttribute("capture_to_file", bool(value))

	def getCaptureViaNet(self):
		return self.getAttribute("capture_via_net", DEFAULT_CAPTURE_VIA_NET)
	
	def setCaptureViaNet(self, value):
		self.setAttribute("capture_via_net", bool(value))

	def getCapabilities(self, user):
		capabilities = Connection.getCapabilities(self, user)
		isUser = self.connector.topology.checkAccess(Permission.ROLE_USER, user)
		capabilities["configure"].update({
			"capture_filter": True,
			"capture_to_file": True,
			"capture_via_net": True,
		})
		for p in netemProperties:
			capabilities["configure"][p] = True
			capabilities["configure"][p+"_to"] = True
			capabilities["configure"][p+"_from"] = True
		capabilities["action"].update({
			"download_capture": isUser and not self.connector.state == State.CREATED and self.getCaptureToFile()
		})
		capabilities["other"] = {
			"live_capture": isUser and self.connector.state == State.STARTED and self.getCaptureViaNet()
		}
		return capabilities

	@db.changeset
	def configure(self, properties):
		oldCaptureToFile = self.getCaptureToFile()
		oldCaptureViaNet = self.getCaptureViaNet()
		oldCaptureFilter = self.getCaptureFilter()
		if "capture_filter" in properties:
			filter = properties["capture_filter"]
			host = self.getHost()
			if host:
				fault.check(tcpdump._checkSyntax(host, filter=filter), "Syntax error in filter")
			self.setCaptureFilter(properties["capture_filter"])
		if "capture_to_file" in properties:
			self.setCaptureToFile(properties["capture_to_file"])
		if "capture_via_net" in properties:
			self.setCaptureViaNet(properties["capture_via_net"])
		for p in netemProperties:
			if p in properties:
				val = properties[p]
				val = netemValueConvert[p](val)
				fault.check(netemValuesChecks[p](val), "Invalid value for %s: %s", (p, val))
				self.setAttribute(p, val)
			if p + "_to" in properties:
				val = properties[p+"_to"]
				val = netemValueConvert[p](val)
				fault.check(netemValuesChecks[p](val), "Invalid value for %s: %s", (p+"_to", val))
				self.setAttribute(p+"_to", val)
			if p + "_from" in properties:
				val = properties[p+"_from"]
				val = netemValueConvert[p](val)
				fault.check(netemValuesChecks[p](val), "Invalid value for %s: %s", (p+"_from", val))
				self.setAttribute(p+"_from", val)
		Connection.configure(self, properties)
		if self.connector.state == State.STARTED:
			self._configLink()
			if oldCaptureToFile and (not self.getCaptureToFile() or self.getCaptureFilter() != oldCaptureFilter):
				self._stopCaptureToFile()
			if oldCaptureViaNet and (not self.getCaptureViaNet() or self.getCaptureFilter() != oldCaptureFilter):
				self._stopCaptureViaNet()
			if self.getCaptureToFile() and (not oldCaptureToFile or self.getCaptureFilter() != oldCaptureFilter):
				self._startCaptureToFile()
			if self.getCaptureViaNet() and (not oldCaptureViaNet or self.getCaptureFilter() != oldCaptureFilter):
				self._startCaptureViaNet()
			
	def _configLink(self):
		host = self.getHost()
		iface = self.internalInterface()
		self._assignIfb()
		assert self.hasIfbId()
		ifb = "ifb%d" % self.getIfbId()
		ifaceutil.ifup(host, ifb)
		tc.setLinkEmulation(host, iface, 
			bandwidth=float(self.getNetemProp("bandwidth", "to")),
			delay=float(self.getNetemProp("delay", "to")),
			jitter=float(self.getNetemProp("jitter", "to")),
			delay_correlation=float(self.getNetemProp("delay_correlation", "to")),
			distribution=self.getNetemProp("distribution", "to"),
			loss=float(self.getNetemProp("lossratio", "to")),
			loss_correlation=float(self.getNetemProp("lossratio_correlation", "to")),
			duplicate=float(self.getNetemProp("duplicate", "to")),
			corrupt=float(self.getNetemProp("corrupt", "to")),
		)
		tc.setLinkEmulation(host, ifb,
			bandwidth=float(self.getNetemProp("bandwidth", "from")),
			delay=float(self.getNetemProp("delay", "from")),
			jitter=float(self.getNetemProp("jitter", "from")),
			delay_correlation=float(self.getNetemProp("delay_correlation", "from")),
			distribution=self.getNetemProp("distribution", "from"),
			loss=float(self.getNetemProp("lossratio", "from")),
			loss_correlation=float(self.getNetemProp("lossratio_correlation", "from")),
			duplicate=float(self.getNetemProp("duplicate", "from")),
			corrupt=float(self.getNetemProp("corrupt", "from")),
		)
		tc.setIncomingRedirect(host, iface, ifb)
		
	def _captureName(self):
		return "capture-%d-%s-%s" % (self.connector.topology.id, self.interface.device.name, self.interface.name)
		
	def _assignIfb(self):
		if not self.hasIfbId():
			self.ifb_id = resources.take(self.getHost(), "ifb", self, self.IFB_ID_SLOT)
			self.save()			
	
	def _unassignIfb(self):
		self.ifb_id = None
		self.save()
		resources.give(self, self.IFB_ID_SLOT)
	
	def _startCaptureToFile(self):
		host = self.interface.device.host
		tcpdump.startCaptureToFile(host, self._captureName(), self.getBridge(), self.getCaptureFilter())

	def _startCaptureViaNet(self):
		host = self.interface.device.host
		if not self.getLiveCapturePort():
			self.live_capture_port = resources.take(host, "port", self, self.LIVE_CAPTURE_PORT_SLOT)
			self.save()
		port = self.getLiveCapturePort()
		tcpdump.startCaptureViaNet(host, self._captureName(), port, self.getBridge(), self.getCaptureFilter())

	def _start(self):
		self._configLink()
		if self.getCaptureToFile():
			self._startCaptureToFile()
		if self.getCaptureViaNet():
			self._startCaptureViaNet()

	def getStartTasks(self):
		taskset = Connection.getStartTasks(self)
		start_task = tasks.Task("start", self._start)
		taskset.add([start_task])
		return taskset
	
	def _stopCapture(self):
		if self.getCaptureToFile():
			self._stopCaptureToFile()
		if self.getCaptureViaNet():
			self._stopCaptureViaNet()
			
	def _stopCaptureToFile(self):
		host = self.getHost()
		tcpdump.stopCaptureToFile(host, self._captureName())

	def _stopCaptureViaNet(self):
		host = self.getHost()
		if self.getLiveCapturePort():
			tcpdump.stopCaptureViaNet(host, self._captureName(), self.getLiveCapturePort())
			self.live_capture_port = None
			self.save()
			resources.give(self, self.LIVE_CAPTURE_PORT_SLOT)

	def _unconfigLink(self):
		host = self.getHost()
		iface = self.internalInterface()
		if ifaceutil.interfaceExists(host, iface):
			try:
				tc.clearIncomingRedirect(host, iface)
				tc.clearLinkEmulation(host, iface)
			except:
				#might still fail if interface is deleted in between
				pass
		if self.hasIfbId():
			ifb = "ifb%d" % self.getIfbId()
			tc.clearLinkEmulation(host, ifb)
		self._unassignIfb()
	
	def _stop(self):
		self._unconfigLink()
		self._stopCapture()
	
	def getStopTasks(self):
		taskset = Connection.getStopTasks(self)
		taskset.add(tasks.Task("stop", self._stop))
		return taskset
	
	def getPrepareTasks(self):
		return Connection.getPrepareTasks(self)

	def _removeCaptureDir(self):
		host = self.getHost()
		if host:
			tcpdump.removeCapture(host, self._captureName())
		
	def getDestroyTasks(self):
		taskset = Connection.getDestroyTasks(self)
		taskset.add(tasks.Task("remove-capture-dir", self._removeCaptureDir))
		return taskset

	def downloadCaptureUri(self, onlyLatest=False):
		fault.check(not self.connector.state == State.CREATED and self.getCaptureToFile(), "Captures not ready")
		host = self.getHost()
		return tcpdump.downloadCaptureUri(host, self._captureName(), onlyLatest)
	
	def repair(self):
		state = self.connector.state
		if state == State.STARTED:
			self._assignIfb()
			self._configLink()
			if self.getCaptureToFile() and not tcpdump.captureToFileRunning(self.getHost(), self._captureName()):
				self._startCaptureToFile()
			if self.getCaptureViaNet() and not tcpdump.captureViaNetRunning(self.getHost(), self._captureName()):
				self._startCaptureViaNet()
		if not self.getHost():
			return
		if state != State.STARTED:
			if tcpdump.captureToFileRunning(self.getHost(), self._captureName()):
				self._stopCaptureToFile()
			if tcpdump.captureViaNetRunning(self.getHost(), self._captureName()):
				self._stopCaptureViaNet()
	
	def toDict(self, auth):
		res = Connection.toDict(self, auth)
		res["attrs"].update(self.getAttributes())
		if self.connector.state == State.STARTED and self.getCaptureViaNet():
			res["attrs"].update(capture_port=self.getLiveCapturePort(), capture_host=self.getHost().name)
		return res