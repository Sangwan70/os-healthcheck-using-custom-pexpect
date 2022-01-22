import os
import re
import sys
import pssh
import getpass
import datetime
import argparse
from em import *
from cprint import *
from up_time import *

class NotLinux(Exception):
  pass

class NotEmTarget(Exception):
  pass

class Emdetails:
  em_homedir='/opt/OracleHomes/agent_home/agent_inst'
  em_owner='orarom'
  def __init__(self,host):
    self.host=host

  def get_em_owner(self):
    try:
      emctl_owner_cmd="if test -d {0} ; then  echo `stat -c %U {0}`; else echo 'DIR-NOT-FOUND'; fi".format(Emdetails.em_homedir)
      if Target_host.exec_command(emctl_owner_cmd)[-1] == 'DIR-NOT-FOUND':
        raise IOError
      else:
        pass
    except IOError:
      is_em_installed,actual_em_homedir=find_em_path(self.host)
      if is_em_installed:
        actual_emctl_owner_cmd="stat -c %U {0}".format(actual_em_homedir)
        actual_em_owner= Target_host.exec_command(actual_emctl_owner_cmd)[-1]
        Emdetails.em_owner=actual_em_owner
        Emdetails.em_homedir=actual_em_homedir
      else:
        raise NotEmTarget
    except NotEmTarget:
        col_print("Em target is not defined OMS...EXITING",Colors.ERROR)

  def exec_em_commands(self):
    if User_name == 'root':
      Em_agent_status = Target_host.exec_command("su - {1} -c '{0}/bin/emctl status agent'".format(Emdetails.em_homedir,Emdetails.em_owner))
      Em_agent_pingoms = Target_host.exec_command("su - {1} -c '{0}/bin/emctl pingOMS'".format(Emdetails.em_homedir,Emdetails.em_owner))
      Em_upload_agent = Target_host.exec_command("su - {1} -c '{0}/bin/emctl upload agent'".format(Emdetails.em_homedir,Emdetails.em_owner))
    elif User_name == Emdetails.em_owner:
      Em_agent_status =  Target_host.exec_command("{0}/bin/emctl status agent".format(Emdetails.em_homedir))
      Em_agent_pingoms = Target_host.exec_command("{0}/bin/emctl pingOMS".format(Emdetails.em_homedir))
      Em_upload_agent =  Target_host.exec_command("{0}/bin/emctl upload agent".format(Emdetails.em_homedir))
    elif not Target_host.whats_mysudo == 'no_sudo':
      Em_agent_status = Target_host.exec_command("sudo su - {1} -c '{0}/bin/emctl status agent'".format(Emdetails.em_homedir,Emdetails.em_owner))
      Em_agent_pingoms = Target_host.exec_command("sudo su - {1} -c '{0}/bin/emctl pingOMS'".format(Emdetails.em_homedir,Emdetails.em_owner))
      Em_upload_agent = Target_host.exec_command("sudo su - {1} -c '{0}/bin/emctl upload agent'".format(Emdetails.em_homedir,Emdetails.em_owner))
      
    else:
      col_print(("User {0} not {1} not 'root'".format(User_name,Emdetails.em_owner)),Colors.WARNING)
      sys.exit()
    return Em_agent_status,Em_agent_pingoms,Em_upload_agent

class Ilomdetails:
  cmd1="ipmitool sunoem cli 'show -d properties /SP/clock uptime'"
  cmd2="ipmitool sunoem cli 'show /SP'"
  cmd3="ipmitool sunoem cli 'show -l all /SYS fault_state==Faulted fru_part_number -t'"

  def get_ilom_details(self):
    if not User_name == 'root':
      Sudo=Target_host.whats_mysudo()
      if not Sudo == 'no_sudo':
        Ilom_uptime= Target_host.exec_command(Ilomdetails.cmd1,sudo=True)
        System_desc_iden=Target_host.exec_command(Ilomdetails.cmd2,sudo=True)
        Faulty_part=Target_host.exec_command(Ilomdetails.cmd3,sudo=True)
        return Ilom_uptime,System_desc_iden,Faulty_part
      else:
        col_print("User does not any sudo privilages to run ipmitool commands",Colors.ERROR)
    else:
      Ilom_uptime= (Target_host.exec_command(Ilomdetails.cmd1))
      System_desc_iden=(Target_host.exec_command(Ilomdetails.cmd2))
      Faulty_part=(Target_host.exec_command(Ilomdetails.cmd3))
      return Ilom_uptime,System_desc_iden,Faulty_part



parser = argparse.ArgumentParser(description="This script to collect resource utilization,Em agent and Hardware/ILOM details", add_help=False)
parser.add_argument('-h', action="store", dest="host", required=True, help="Command to run")
parser.add_argument('-u', action="store", dest="user", required=True, help="Login username ")
parser.add_argument('-k', action="store", dest="keypath", required=False, help="ssh private key with obsolute path")
parser.add_argument('--help',help="Please check the usage")
args = parser.parse_args()

Host_name=args.host
User_name=args.user
SshKey=args.keypath

if not args.keypath:
  PassWord=getpass.getpass("Enter the password:- ")
  Target_host=pssh.Connect(Host_name,22,User_name,PassWord)
else:
  if os.path.exists(SshKey):
      Target_host=pssh.Connect(Host_name,22,User_name,ssh_key=SshKey)
  else:
      print("The file {0} is not found".format(SshKey))
      sys.exit()

do_print("Trying to connect to Host {0}".format(Host_name),st_info,with_time)
Target_host.connect_ssh()

try:
  Uname_op = (Target_host.exec_command('uname -a')[0]).encode('utf-8').split()
  while not Uname_op[0] == 'Linux':
    raise NotLinux
    break
except NotLinux as e:
  do_print("The Host operating system is not Linux ..EXITING",st_err)
else:
  Hostname = Uname_op[1]
  Operating_System = Uname_op[-1]
  Kernel_version = Uname_op[2]
  Uptrack_Kernel_version = (Target_host.exec_command('/usr/bin/uptrack-uname -r')[0].encode('utf-8'))
  Os_release = (Target_host.exec_command('cat /etc/os-release |egrep PRETTY |cut -f2 -d=')[0].encode('utf-8'))
  Prod_name = (Target_host.exec_command('cat /sys/class/dmi/id/product_name')[0].encode('utf-8'))
  Physical_Virtual = 'Virtual' if 'HVM domU' or 'Standard PC' in Prod_name else 'Physical'
  Up_time = (Target_host.exec_command('cat /proc/uptime|cut -f1 -d.')[0].encode('utf-8'))
  Rpms_installed=(Target_host.exec_command('rpm -qa --qf "%{NAME},%{VERSION}\n"'))
  Df_output = (Target_host.exec_command('df -hP|egrep -v "tmpfs|Use%"'))
  Sar_U = (Target_host.exec_command('sar -u 1 3 |grep Average'))
  Free_M = (Target_host.exec_command('free -m'))
  Top_10_mem = (Target_host.exec_command('ps -eo pid,ppid,cmd,%mem,%cpu --sort=-%mem|head'))
  Top_10_cpu = (Target_host.exec_command('ps -eo pid,ppid,cmd,%mem,%cpu --sort=-%cpu|head'))
print_headline('Host Details',80)
print 'Hostname                 :    '+ Hostname
print 'Operating_System         :    '+ Operating_System
print 'Kernel_version           :    '+ Kernel_version
print 'Uptrack_Kernel_version   :    '+ Uptrack_Kernel_version
print 'Os_release               :    '+ Os_release
print 'Physical_Virtual         :    '+ Physical_Virtual
print 'Prod_name                :    '+ Prod_name
if Up_time > 86400:
  print 'Uptime                   :    '+Colors.SUCCESS+Con_secs(Up_time)+Colors.END
else:
  print 'Uptime                   :    '+Colors.ERROR+Con_secs(Up_time)+Colors.END
print 'Last Reboot              :    '+ str(datetime.datetime.now()-datetime.timedelta(seconds=int(Up_time)))
Rpm_to_machinetype_match={
                         'oasg-meta':'OASG Gateway',
                         'exadata-sun-vm-computenode-minimum':'Exadata Database node VIRTUAL',
                         'exadata-sun-computenode-minimum':'Exadata Database node BAREMETAL',
                         'oci-utils':'Orcale Cloud Infrastructure Host'
                         }
for rpm,mess in Rpm_to_machinetype_match.items():
  if any(rpm in rpms_list for rpms_list in Rpms_installed):
    print "Configuration item Type  :    "+mess
print_headline('Storage details',80)
for x in Df_output:
  Fs_usage=x.encode('utf-8').split()[4][0:-1]
  if int(Fs_usage) > 50:
    col_print(x,Colors.ERROR)
  else:
    col_print(x,Colors.SUCCESS)


print_headline('Memory and swap usage details',80)
for line in Free_M:
  if line.split()[0] == 'Mem:':
    if int(line.split()[2])*100/int(line.split()[1]) > 85:
      col_print("Memory Usage is above threshold "+ str(int(line.split()[2])*100/int(line.split()[1])),Colors.ERROR)
    else:
      col_print("Memory Usage is withing threshold "+ str(int(line.split()[2])*100/int(line.split()[1])),Colors.SUCCESS)
  if line.split()[0] == 'Swap:':
    if int(line.split()[2])*100/int(line.split()[1]) > 85:
      col_print("Swap Usage is above threshold "+ str(int(line.split()[2])*100/int(line.split()[1])),Colors.ERROR)
    else:
      col_print("Swap Usage is withing threshold "+ str(int(line.split()[2])*100/int(line.split()[1])),Colors.SUCCESS)
print_headline('Top ten memory consuming processes',80)
for line in Top_10_mem:
  print(line)

print_headline('CPU  usage details',80)
Sar_output=(Sar_U[0].encode('utf-8').split())
print "Normal User Cpu Usage %     :------>", Sar_output[2]
print "System User CPU Usage %     :------>", Sar_output[4]
print "Cpu Usage due to I/O wait % :------>", Sar_output[5]
if Sar_output[-1] < 20 :
   col_print(('Cpu Idle %                  :------> '+ Sar_output[-1]),Colors.ERROR)
else:
   col_print(('Cpu Idle %                  :------> '+ Sar_output[-1]),Colors.SUCCESS)

print_headline('Top ten cpu consuming processes',80)
for line in Top_10_cpu:
  print(line)


print_headline('EM Agent status and details',80)
e=Emdetails(Host_name)
e.get_em_owner()
Em_agent_status,Em_agent_pingoms,Em_upload_agent=e.exec_em_commands()
xx=["Agent Version","OMS Version","Started at","Collection Status","Heartbeat Status"]
for xxx in xx:
  for x in Em_agent_status:
    if xxx in x:
      print((x.split(': ')[0].strip()).ljust(25) + ':  ' + (x.split(': ')[1]))
if Em_agent_status[-1] == "Agent is Running and Ready":
  col_print(Em_agent_status[-1],Colors.SUCCESS)
else:
  col_print(Em_agent_status[-1],Colors.ERROR)
if 'successfully' in Em_agent_pingoms[-1]:
  col_print(Em_agent_pingoms[-1],Colors.SUCCESS)
else:
  col_print(Em_agent_pingoms[-1],Colors.ERROR)
if 'successfully' in Em_upload_agent[-1]:
  col_print(Em_upload_agent[-1],Colors.SUCCESS)
else:
  col_print(Em_upload_agent[-1],Colors.ERROR)


if not Physical_Virtual == 'Virtual':
  print_headline('Ilom status and details',80)
  i=Ilomdetails()
  Ilom_uptime,System_desc_iden,Faulty_part=i.get_ilom_details()
  for ilom_uptime in Ilom_uptime:
    if 'day' in ilom_uptime:
      print "Ilom "+ (ilom_uptime.strip())
  for desc_iden in System_desc_iden:
    if 'system_desc' in desc_iden or 'system_iden' in desc_iden:
      print desc_iden.strip()
  if any('Query found no matches' in string for string in Faulty_part):
    col_print("Faulty Parts : None",Colors.SUCCESS)
  else:
    for line in Faulty_part:
      print line 

