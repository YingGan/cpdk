import settings
from unittest import TestCase
from cpdk_db import import_user_models, unimport_user_modules


class TestCPDKModelMultiFile(TestCase):
    def test_import_multiple_files(self):

        settings.MODELS_DIR = 'tests/model_import/models/multiple_files/'
        print "importing from %s" % settings.MODELS_DIR
        models = import_user_models(settings.MODELS_DIR)
        print "%d models imported: %s" % (len(models), str(models))
        self.assertEqual(len(models), 2)