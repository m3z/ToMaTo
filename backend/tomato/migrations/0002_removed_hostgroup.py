# encoding: utf-8
#@PydevCodeAnalysisIgnore, pylint: disable-all
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
	
	def forwards(self, orm):
		
		# Deleting model 'HostGroup'
		db.delete_table('tomato_hostgroup')

		# Renaming column for 'Device.hostgroup' to match new field type.
		db.rename_column('tomato_device', 'hostgroup_id', 'hostgroup')
		# Changing field 'Device.hostgroup'
		db.alter_column('tomato_device', 'hostgroup', self.gf('django.db.models.fields.CharField')(max_length=10, null=True))

		try:
			# Removing index on 'Device', fields ['hostgroup']
		 	db.delete_index('tomato_device', ['hostgroup_id'])
		except:
			pass

		# Renaming column for 'Host.group' to match new field type.
		db.rename_column('tomato_host', 'group_id', 'group')
		# Changing field 'Host.group'
		db.alter_column('tomato_host', 'group', self.gf('django.db.models.fields.CharField')(max_length=10, blank=True))

		try:
			# Removing index on 'Host', fields ['group']
			db.delete_index('tomato_host', ['group_id'])
		except:
			pass

		# Renaming column for 'PhysicalLink.src_group' to match new field type.
		db.rename_column('tomato_physicallink', 'src_group_id', 'src_group')
		# Changing field 'PhysicalLink.src_group'
		db.alter_column('tomato_physicallink', 'src_group', self.gf('django.db.models.fields.CharField')(max_length=10))

		try:
			# Removing index on 'PhysicalLink', fields ['src_group']
			db.delete_index('tomato_physicallink', ['src_group_id'])
		except:
			pass

		# Renaming column for 'PhysicalLink.dst_group' to match new field type.
		db.rename_column('tomato_physicallink', 'dst_group_id', 'dst_group')
		# Changing field 'PhysicalLink.dst_group'
		db.alter_column('tomato_physicallink', 'dst_group', self.gf('django.db.models.fields.CharField')(max_length=10))

		try:
			# Removing index on 'PhysicalLink', fields ['dst_group']
			db.delete_index('tomato_physicallink', ['dst_group_id'])
		except:
			pass
	
	
	def backwards(self, orm):
		
		# Adding model 'HostGroup'
		db.create_table('tomato_hostgroup', (
			('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
			('name', self.gf('django.db.models.fields.CharField')(max_length=10)),
		))
		db.send_create_signal('tomato', ['HostGroup'])

		# Renaming column for 'Device.hostgroup' to match new field type.
		db.rename_column('tomato_device', 'hostgroup', 'hostgroup_id')
		# Changing field 'Device.hostgroup'
		db.alter_column('tomato_device', 'hostgroup_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.HostGroup'], null=True))

		# Adding index on 'Device', fields ['hostgroup']
		db.create_index('tomato_device', ['hostgroup_id'])

		# Renaming column for 'Host.group' to match new field type.
		db.rename_column('tomato_host', 'group', 'group_id')
		# Changing field 'Host.group'
		db.alter_column('tomato_host', 'group_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.HostGroup']))

		# Adding index on 'Host', fields ['group']
		db.create_index('tomato_host', ['group_id'])

		# Renaming column for 'PhysicalLink.src_group' to match new field type.
		db.rename_column('tomato_physicallink', 'src_group', 'src_group_id')
		# Changing field 'PhysicalLink.src_group'
		db.alter_column('tomato_physicallink', 'src_group_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.HostGroup']))

		# Adding index on 'PhysicalLink', fields ['src_group']
		db.create_index('tomato_physicallink', ['src_group_id'])

		# Renaming column for 'PhysicalLink.dst_group' to match new field type.
		db.rename_column('tomato_physicallink', 'dst_group', 'dst_group_id')
		# Changing field 'PhysicalLink.dst_group'
		db.alter_column('tomato_physicallink', 'dst_group_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tomato.HostGroup']))

		# Adding index on 'PhysicalLink', fields ['dst_group']
		db.create_index('tomato_physicallink', ['dst_group_id'])
	
	
	models = {
		'tomato.configuredinterface': {
			'Meta': {'object_name': 'ConfiguredInterface', '_ormbases': ['tomato.Interface']},
			'interface_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Interface']", 'unique': 'True', 'primary_key': 'True'}),
			'ip4address': ('django.db.models.fields.CharField', [], {'max_length': '18', 'null': 'True'}),
			'use_dhcp': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'})
		},
		'tomato.connection': {
			'Meta': {'object_name': 'Connection'},
			'bridge_id': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
			'connector': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Connector']"}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'interface': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Interface']", 'unique': 'True'})
		},
		'tomato.connector': {
			'Meta': {'object_name': 'Connector'},
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'name': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
			'pos': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True'}),
			'resources': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Resources']", 'null': 'True'}),
			'state': ('django.db.models.fields.CharField', [], {'default': "'created'", 'max_length': '10'}),
			'topology': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Topology']"}),
			'type': ('django.db.models.fields.CharField', [], {'max_length': '10'})
		},
		'tomato.device': {
			'Meta': {'object_name': 'Device'},
			'host': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Host']", 'null': 'True'}),
			'hostgroup': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True'}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'name': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
			'pos': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True'}),
			'resources': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Resources']", 'null': 'True'}),
			'state': ('django.db.models.fields.CharField', [], {'default': "'created'", 'max_length': '10'}),
			'topology': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Topology']"}),
			'type': ('django.db.models.fields.CharField', [], {'max_length': '10'})
		},
		'tomato.emulatedconnection': {
			'Meta': {'object_name': 'EmulatedConnection', '_ormbases': ['tomato.Connection']},
			'bandwidth': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
			'capture': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
			'connection_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Connection']", 'unique': 'True', 'primary_key': 'True'}),
			'delay': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
			'lossratio': ('django.db.models.fields.FloatField', [], {'null': 'True'})
		},
		'tomato.error': {
			'Meta': {'object_name': 'Error'},
			'date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'message': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
			'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
		},
		'tomato.host': {
			'Meta': {'object_name': 'Host'},
			'bridge_range_count': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1000'}),
			'bridge_range_start': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1000'}),
			'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
			'group': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
			'port_range_count': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1000'}),
			'port_range_start': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '7000'}),
			'vmid_range_count': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '200'}),
			'vmid_range_start': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1000'})
		},
		'tomato.interface': {
			'Meta': {'object_name': 'Interface'},
			'device': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Device']"}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'name': ('django.db.models.fields.CharField', [], {'max_length': '5'})
		},
		'tomato.kvmdevice': {
			'Meta': {'object_name': 'KVMDevice', '_ormbases': ['tomato.Device']},
			'device_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Device']", 'unique': 'True', 'primary_key': 'True'}),
			'kvm_id': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
			'template': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
			'vnc_port': ('django.db.models.fields.IntegerField', [], {'null': 'True'})
		},
		'tomato.openvzdevice': {
			'Meta': {'object_name': 'OpenVZDevice', '_ormbases': ['tomato.Device']},
			'device_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Device']", 'unique': 'True', 'primary_key': 'True'}),
			'gateway': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True'}),
			'openvz_id': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
			'root_password': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
			'template': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
			'vnc_port': ('django.db.models.fields.IntegerField', [], {'null': 'True'})
		},
		'tomato.permission': {
			'Meta': {'object_name': 'Permission'},
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'role': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
			'topology': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Topology']"}),
			'user': ('django.db.models.fields.CharField', [], {'max_length': '30'})
		},
		'tomato.physicallink': {
			'Meta': {'object_name': 'PhysicalLink'},
			'delay_avg': ('django.db.models.fields.FloatField', [], {}),
			'delay_stddev': ('django.db.models.fields.FloatField', [], {}),
			'dst_group': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'loss': ('django.db.models.fields.FloatField', [], {}),
			'src_group': ('django.db.models.fields.CharField', [], {'max_length': '10'})
		},
		'tomato.resources': {
			'Meta': {'object_name': 'Resources'},
			'disk': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'memory': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
			'ports': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
			'special': ('django.db.models.fields.IntegerField', [], {'default': '0'})
		},
		'tomato.specialfeature': {
			'Meta': {'object_name': 'SpecialFeature'},
			'bridge': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
			'feature_group': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
			'feature_type': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
			'host': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Host']"}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
		},
		'tomato.specialfeatureconnector': {
			'Meta': {'object_name': 'SpecialFeatureConnector', '_ormbases': ['tomato.Connector']},
			'connector_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Connector']", 'unique': 'True', 'primary_key': 'True'}),
			'feature_group': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
			'feature_type': ('django.db.models.fields.CharField', [], {'max_length': '50'})
		},
		'tomato.template': {
			'Meta': {'object_name': 'Template'},
			'default': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
			'download_url': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255'}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
			'type': ('django.db.models.fields.CharField', [], {'max_length': '12'})
		},
		'tomato.tincconnection': {
			'Meta': {'object_name': 'TincConnection', '_ormbases': ['tomato.EmulatedConnection']},
			'emulatedconnection_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.EmulatedConnection']", 'unique': 'True', 'primary_key': 'True'}),
			'gateway': ('django.db.models.fields.CharField', [], {'max_length': '18', 'null': 'True'}),
			'tinc_port': ('django.db.models.fields.IntegerField', [], {'null': 'True'})
		},
		'tomato.tincconnector': {
			'Meta': {'object_name': 'TincConnector', '_ormbases': ['tomato.Connector']},
			'connector_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['tomato.Connector']", 'unique': 'True', 'primary_key': 'True'})
		},
		'tomato.topology': {
			'Meta': {'object_name': 'Topology'},
			'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
			'date_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
			'date_usage': ('django.db.models.fields.DateTimeField', [], {}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
			'owner': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
			'resources': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tomato.Resources']", 'null': 'True'}),
			'task': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
		}
	}
	
	complete_apps = ['tomato']
