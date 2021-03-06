#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Tests for openslides.motion.models
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2011–2013 by OpenSlides team, see AUTHORS.
    :license: GNU GPL, see LICENSE for more details.
"""

import StringIO
import os

from django.test.client import Client

from openslides.config.api import config
from openslides.motion.models import Motion, Category
from openslides.motion.csv_import import import_motions
from openslides.participant.models import User
from openslides.utils.test import TestCase


class CSVImport(TestCase):
    def setUp(self):
        # Admin
        self.admin = User.objects.create_superuser('Admin_ieY0Eereimeimeizuosh', 'admin@admin.admin', 'eHiK1aiRahxaix0Iequ2')
        self.admin_client = Client()
        self.admin_client.login(username='Admin_ieY0Eereimeimeizuosh', password='eHiK1aiRahxaix0Iequ2')

        # Normal user
        self.normal_user = User.objects.create_user('User_CiuNgo4giqueeChie5oi', 'user@user.user', 'eihi1Eequaek4eagaiKu')
        self.normal_client = Client()
        self.normal_client.login(username='User_CiuNgo4giqueeChie5oi', password='eihi1Eequaek4eagaiKu')

        # Category
        self.category1 = Category.objects.create(name='Satzungsanträge', prefix='SA')
        self.category2 = Category.objects.create(name='Bildung', prefix='B1')
        self.category3 = Category.objects.create(name='Bildung', prefix='B2')

    def test_example_file_de(self):
        special_user = User.objects.create_user(username='Harry_Holland',
                                                password='iegheeChaje7guthie4a',
                                                first_name='Harry',
                                                last_name='Holland')
        for i in range(2):
            username = 'John_Doe_%d' % i
            User.objects.create_user(username=username,
                                     password='default',
                                     first_name='John',
                                     last_name='Doe')

        csv_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'extras', 'csv-examples')
        self.assertEqual(Motion.objects.count(), 0)
        with open(csv_dir + '/motions-demo_de.csv') as f:
            count_success, count_lines, error_messages, warning_messages = import_motions(csv_file=f, default_submitter=self.normal_user.person_id)
        self.assertEqual(Motion.objects.count(), 11)
        self.assertEqual(count_success, 11)

        motion1 = Motion.objects.get(pk=1)
        self.assertEqual(motion1.identifier, '1')
        self.assertEqual(motion1.title, u'Entlastung des Vorstandes')
        self.assertEqual(motion1.text, u'Die Versammlung möge beschließen, den Vorstand für seine letzte Legislaturperiode zu entlasten.')
        self.assertEqual(motion1.reason, u'Bericht erfolgt mündlich.')
        self.assertEqual(len(motion1.submitter.all()), 1)
        self.assertEqual(motion1.submitter.all()[0].person, self.normal_user)
        self.assertTrue(motion1.category is None)
        self.assertTrue(any('Submitter unknown.' in w for w in warning_messages))
        self.assertTrue(any('Category unknown.' in w for w in warning_messages))

        motion2 = Motion.objects.get(pk=2)
        self.assertEqual(motion2.identifier, 'SA 1')
        self.assertEqual(motion2.title, u'Satzungsänderung § 2 Abs. 3')
        self.assertHTMLEqual(motion2.text, u'''<p>Die Versammlung möge beschließen, die Satzung in § 2 Abs. 3 wie folgt zu ändern:</p>
                                               <p>Es wird vor dem Wort "Zweck" das Wort "gemeinnütziger" eingefügt.</p>''')
        self.assertEqual(motion2.reason, u'Die Änderung der Satzung ist aufgrund der letzten Erfahrungen eine sinnvolle Maßnahme, weil ...')
        self.assertEqual(len(motion2.submitter.all()), 1)
        self.assertEqual(motion2.submitter.all()[0].person, special_user)
        self.assertEqual(motion2.category, self.category1)

        # check user 'John Doe'
        self.assertTrue(any('Several suitable submitters found.' in w for w in warning_messages))
        # check category 'Bildung'
        self.assertTrue(any('Several suitable categories found.' in w for w in warning_messages))

    def test_malformed_file(self):
        csv_file = StringIO.StringIO()
        csv_file.write('Header\nMalformed data,\n,Title,Text,,,\n')
        count_success, count_lines, error_messages, warning_messages = import_motions(csv_file=csv_file, default_submitter=self.normal_user.person_id)
        self.assertEqual(count_success, 0)
        self.assertTrue(any('Line is malformed.' in e for e in error_messages))

    def test_wrong_encoding(self):
        csv_file = StringIO.StringIO()
        text = u'Müller'.encode('iso-8859-15')
        csv_file.write(text)
        csv_file.seek(0)
        count_success, error_messages, warning_messages = import_motions(csv_file=csv_file, default_submitter=self.normal_user.person_id)
        self.assertEqual(count_success, 0)
        self.assertTrue('Import file has wrong character encoding, only UTF-8 is supported!' in error_messages)
