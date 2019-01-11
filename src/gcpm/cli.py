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

    def help(self):
        Gcpm.help()

    def show_config(self):
        Gcpm(config=self.config).show_config()

    def install(self):
        """Install service related files."""
        Gcpm(config=self.config, service=True).install()

    def uninstall(self):
        """Uninstall service related files."""
        Gcpm(config=self.config, service=True).uninstall()

    def run(self):
        """Main function to run the loop."""
        Gcpm(config=self.config).run()

    def service(self):
        """Run the loop as service."""
        Gcpm(config=self.config, service=True).run()

    def set_pool_password(self, pool_password):
        """Set pool_password file in google storage."""
        Gcpm(config=self.config).get_gcs().upload_file(pool_password)


def cli():
    fire.Fire(CliObject)
