#!/usr/bin/python
import os
import re
import sys
import time
from rancher_metadata import MetadataAPI

__author__ = 'Sebastien LANGOUREAUX'

BACKUP_DIR = '/backup/gluster'


class ServiceRun():


  def backup_duplicity_ftp(self, backend, target_path, full_backup_frequency, nb_full_backup_keep, nb_increment_backup_chain_keep, volume_size, is_init=False):
      global BACKUP_DIR
      if backend is None or backend == "":
          raise KeyError("You must set the target backend")
      if target_path is None or target_path == "":
          raise KeyError("You must set the target path")
      if full_backup_frequency is None or full_backup_frequency == "":
          raise KeyError("You must set the full backup frequency")
      if nb_full_backup_keep is None or nb_full_backup_keep == "":
          raise KeyError("You must set how many full backup you should to keep")
      if nb_increment_backup_chain_keep is None or nb_increment_backup_chain_keep == "":
          raise KeyError("You must set how many incremental chain with full backup you should to keep")
      if volume_size is None or volume_size == "":
          raise KeyError("You must set the volume size")

      backend = "%s%s" % (backend, target_path)
      cmd = "duplicity"

      # First, we restore the last backup
      if is_init is True:
          print("Starting init the backup folder")
          os.system("%s --no-encryption %s %s" % (cmd, backend, BACKUP_DIR))


      else:
          # We backup on FTP
          print("Starting backup")
          os.system("%s --volsize %s --no-encryption --allow-source-mismatch --full-if-older-than %s %s %s" % (cmd, volume_size, full_backup_frequency, BACKUP_DIR, backend))

          # We clean old backup
          print("Starting cleanup")
          os.system("%s remove-all-but-n-full %s --force --allow-source-mismatch --no-encryption %s" % (cmd, nb_full_backup_keep, backend))
          os.system("%s remove-all-inc-of-but-n-full %s --force --allow-source-mismatch --no-encryption %s" % (cmd, nb_increment_backup_chain_keep, backend))
          os.system("%s cleanup --force --no-encryption %s" % (cmd, backend))



  def detect_gluster(self):
      global BACKUP_DIR

      # Identity database to backup
      metadata_manager = MetadataAPI()
      list_services = metadata_manager.get_service_links()
      list_gluster = []
      for service in list_services:
          service_name = list_services[service]
          service_name_env = service_name.upper().replace('-', '_')
          gluster = {}
          gluster['host'] = service_name
          gluster['name'] = service
          gluster['volumes'] = os.getenv(service_name_env + '_ENV_GLUSTER_VOLUMES').split(',')

          list_gluster.append(gluster)
          print("Found Gluster host to backup : %s (%s)" % (service, service_name))


      return list_gluster

  def mount_gluster(self, list_gluster):
      global BACKUP_DIR

      # Loop over gluster host and volume to mount it
      for gluster in list_gluster:
          for volume in gluster['volumes']:
              # We mount the volume to backup it
              path = "%s/%s/%s" % (BACKUP_DIR, gluster['name'], volume)
              os.system('mkdir -p ' + path)
              cmd = "mount -t glusterfs %s:%s %s" % (gluster['host'], volume, path)
              os.system(cmd)
              print("Mount %s:%s in %s to backup it" % (gluster['host'], volume, path))

  def umount_gluster(self, list_gluster):
      global BACKUP_DIR

      # Loop over gluster host and volume to mount it
      for gluster in list_gluster:
          for volume in gluster['volumes']:
              # We mount the volume to backup it
              path = "%s/%s/%s" % (BACKUP_DIR, gluster['name'], volume)
              os.system("umount " + path)
              print("Umount %s" % (path))


if __name__ == '__main__':
    service = ServiceRun()
    service.backup_duplicity_ftp(os.getenv('TARGET_BACKEND'), os.getenv('TARGET_PATH', "/backup/postgres"),os.getenv('BK_FULL_FREQ', "7D"), os.getenv('BK_KEEP_FULL', "3"), os.getenv('BK_KEEP_FULL_CHAIN', "1"), os.getenv('VOLUME_SIZE', "25"), True)
    list_gluster = service.detect_gluster()
    service.mount_gluster(list_gluster)
    service.backup_duplicity_ftp(os.getenv('TARGET_BACKEND'), os.getenv('TARGET_PATH', "/backup/postgres"),os.getenv('BK_FULL_FREQ', "7D"), os.getenv('BK_KEEP_FULL', "3"), os.getenv('BK_KEEP_FULL_CHAIN', "1"), os.getenv('VOLUME_SIZE', "25"))
    service.umount_gluster(list_gluster)
