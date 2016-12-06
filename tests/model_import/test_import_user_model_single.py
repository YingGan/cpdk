import settings
from unittest import TestCase
from cpdk_db import import_user_models, unimport_user_modules


class TestCPDKModelSingle(TestCase):
    def test_import_single_file(self):
        """
        Verify that the import_user_models() method correctly parses a single model file
        :return: None
        """
        # Local models directory in the 'tests' directory
        settings.MODELS_DIR = 'tests/model_import/models/single_file/'
        print "importing from %s" % settings.MODELS_DIR

        # Import all of the models defined in the model.py file
        models = import_user_models(settings.MODELS_DIR)

        print "%d models imported: %s" % (len(models), str(models))

        # Make sure no extra models were imported
        self.assertEqual(len(models), 1)

        # Verify the models were correctly instantiated
        self.assertIn('TestModel', models)
        self.assertNotIn('NonModel', models)

        # Verify that all the attributes of TestModel are present
        for member in ['string', 'integer', 'boolean', 'floating_point']:
            self.assertIn(member, dir(models['TestModel']))
