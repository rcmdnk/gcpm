# -*- coding: utf-8 -*-

"""
    Command line interface for core object
"""


from .core import Gcpm
import fire


class CliObject(object):
    """HTCondor pool manager for Google Cloud Platform."""

    def __init__(self, config="~/.config/gcpm/gcpm.yml"):
        self.config = config

    def show_config(self):
        Gcpm(config=self.config).show_config()

    def run(self):
        """Main function to run the loop."""
        Gcpm(config=self.config).run()
        pass

    def service(self):
        """Run the loop as service."""
        Gcpm(config=self.config, service=True).run()
        pass

    def set_pool_password(self, pool_password):
        """Set pool_password file in google storage."""
        Gcpm(config=self.config).get_gcs().upload_file(pool_password)
        pass


def cli():
    fire.Fire(CliObject)
