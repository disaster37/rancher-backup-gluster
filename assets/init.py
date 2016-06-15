#!/usr/bin/python
import os
import re
import sys
import time
from rancher_metadata import MetadataAPI

__author__ = 'Sebastien LANGOUREAUX'

BACKUP_DIR = '/backup/gluster'


class ServiceRun():


  def backup_duplicity_ftp(self, ftp_server, ftp_port, ftp_user, ftp_password, target_path, is_init=False):
      global BACKUP_DIR
      if ftp_server is None or ftp_server == "":
          raise KeyError("You must set the ftp server")
      if ftp_port is None:
          raise KeyError("You must set the ftp port")
      if ftp_user is None or ftp_user == "":
          raise KeyError("You must set the ftp user")
      if ftp_password is None or ftp_password == "":
          raise KeyError("You must set the ftp password")
      if target_path is None or target_path == "":
          raise KeyError("You must set the target path")

      ftp = "ftp://%s@%s:%d%s" % (ftp_user, ftp_server, ftp_port, target_path)
      cmd = "FTP_PASSWORD=%s duplicity" % (ftp_password)

      # First, we restore the last backup
      if is_init is True:
          print("Starting init the backup folder")
          os.system("%s --no-encryption %s %s/" % (cmd, ftp, BACKUP_DIR))


      else:
          # We backup on FTP
          print("Starting backup")
          os.system("%s --no-encryption --allow-source-mismatch --full-if-older-than 7D %s %s" % (cmd, BACKUP_DIR, ftp))

          # We clean old backup
          print("Starting cleanup")
          os.system("%s remove-all-but-n-full 3 --force --allow-source-mismatch --no-encryption %s" % (cmd, ftp))
          os.system("%s cleanup --force --no-encryption %s" % (cmd, ftp))


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
    service.backup_duplicity_ftp(os.getenv('FTP_SERVER'), os.getenv('FTP_PORT', 21), os.getenv('FTP_LOGIN'), os.getenv('FTP_PASSWORD'), os.getenv('FTP_TARGET_PATH', BACKUP_DIR), True)
    list_gluster = service.detect_gluster()
    service.mount_gluster(list_gluster)
    service.backup_duplicity_ftp(os.getenv('FTP_SERVER'), os.getenv('FTP_PORT', 21), os.getenv('FTP_LOGIN'), os.getenv('FTP_PASSWORD'), os.getenv('FTP_TARGET_PATH', BACKUP_DIR))
    service.umount_gluster(list_gluster)
