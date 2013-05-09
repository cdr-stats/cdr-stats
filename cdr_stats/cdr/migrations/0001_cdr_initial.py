# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Switch'
        db.create_table('voip_switch', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100, unique=True, null=True)),
            ('ipaddress', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
            ('key_uuid', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
        ))
        db.send_create_signal(u'cdr', ['Switch'])

        # Adding model 'HangupCause'
        db.create_table('hangup_cause', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('code', self.gf('django.db.models.fields.PositiveIntegerField')(unique=True)),
            ('enumeration', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('cause', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'cdr', ['HangupCause'])


    def backwards(self, orm):
        # Deleting model 'Switch'
        db.delete_table('voip_switch')

        # Deleting model 'HangupCause'
        db.delete_table('hangup_cause')


    models = {
        u'cdr.hangupcause': {
            'Meta': {'object_name': 'HangupCause', 'db_table': "'hangup_cause'"},
            'cause': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'code': ('django.db.models.fields.PositiveIntegerField', [], {'unique': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'enumeration': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'cdr.switch': {
            'Meta': {'object_name': 'Switch', 'db_table': "'voip_switch'"},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ipaddress': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'key_uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'unique': 'True', 'null': 'True'})
        }
    }

    complete_apps = ['cdr']