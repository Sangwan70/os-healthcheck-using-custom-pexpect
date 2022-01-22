#!/usr/bin/python
#Author: CCSD Automation Team. acs-amr-unix-tier3_ww_grp@oracle.com
#Version 1.2.0.1    #pushed on 1st Nov 2021  16:00 IST

'''
The script is a propriatery tool developed by CCSD Automation team.
It is a custom utility class, adopted from pexpect module. The intention is to just import this
class to execute the command and get the output from the host.
A ssh session to object will be invoked and commands will be sent to expect terminal by the methods
'''

import pexpect
import socket
import logging
from sys import exit

logging.Formatter(fmt='%(asctime)s',datefmt='%Y-%m-%d,%H:%M:%S')
#LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
logging.basicConfig(level=10,format="%(asctime)s [%(levelname)s] %(message)s",datefmt='%d-%m-%Y %H:%M:%S')
logger=logging.getLogger()

class MutualconflictArgs(Exception):
    pass

class IncorrectIpAddress(Exception):
    pass

class Connect:
    def __init__(self,Host,Port,User,Password=None,ssh_key=None,custom_prompt=None):
        self.Host=Host
        self.Port=Port
        self.User=User
        self._Password=Password
        self.ssh_key=ssh_key
        if self._Password and self.ssh_key:
            raise MutualconflictArgs("Both sshkey and Passwords are not accepted at same time.")
        self.PROMPT=['# ','\$ ']
        if custom_prompt:
            if isinstance(custom_prompt, str):
                self.PROMPT.append(custom_prompt)
            else:
                logger.error('The {0} is not a string'.format(custom_prompt))

    def __str__(self):
        return "ssh session to host {0} will be  initiated by user {1}".format(self.Host,self.User)
    def __repr__(self):
        return 'Connect({self.Host},{self.Port},{self.User})'.format(self=self)

    @property
    def Password(self):
        return self._Password

    def check_connectivity(self):
        '''
        A  method to validate if ssh port is accessible on Host
        '''
        retry = 0
        while self.Host and retry < 3:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex((self.Host,self.Port))
            if result == 0:
                return True
            else:
                retry += 1
                if retry == 1:
                    logger.error(" [ERR] Targte IP Address [ " + self.Host + " ] Not Responding SSH Connections .. Validate IP Address & Retry\n")
                elif retry == 2:
                    logger.critical(" [ERR] OASG IP Address [ " + self.Host + " ] Not Responding SSH Connections .. Closing The Execution\n")
                    return False

    def connect_ssh(self):
        '''
        Esatblish a ssh connection to server and return a command prompt
        '''
        sshRefused = 'Connection refused'
        noRoute = 'No route to host'
        message='Are you sure you want to continue connecting'
        hostnameResolve = 'Could not resolve'
        if self.ssh_key:
            conn_str = 'ssh '+ '-i {0} -oPasswordAuthentication=no '.format(self.ssh_key) + self.User+'@'+self.Host
        else:
            conn_str = 'ssh ' +self.User+'@'+self.Host
        if self.check_connectivity():
            try:
                self.child=pexpect.spawn(conn_str)
                self.child=pexpect.spawn(conn_str)
                data=self.child.expect([pexpect.TIMEOUT, sshRefused, message,'[P|p]assword: ',noRoute,hostnameResolve, '[#$] ','passphrase','bad permissions',pexpect.EOF])
                if data == 9:
                    logger.critical("ssh connection failed with EOF error")
                    exit()
                elif data == 8:
                    logger.critical("SSH key file permissions are too open ..")
                    exit()
                elif data == 7:
                    logger.critical("[-] Error connecting..passphrase asked for key")
                    exit()
                elif data == 0:
                    logger.critical("[-] Error connecting..")
                    exit()
                elif data == 1:
                    logger.critical("[-] Ssh connection refused by target")
                    exit()
                elif data == 4:
                    logger.critical("Unable to connect. No route to host")
                    exit()
                elif data == 5:
                    logger.critical("Unable to connect,Hostname resolution issue")
                    exit()
                elif data == 2:
                    self.child.sendline('yes')
                    data=self.child.expect([pexpect.TIMEOUT,'[P|p]assword: '])
                    if data == 0:
                        logger.critical("[-] Error connecting..")
                        return
                elif data == 6:
                    logger.info('Connected Successfully.')
                else:
                    self.child.sendline(self.Password)
                    i=self.child.expect(['Permission denied','[#$] '])
                    if i == 0:
                        logger.critical("Permission denied by host. Unable to login")
                    elif i == 1:
                        logger.info('Connected to {0} Successfully.'.format(self.Host))
            except Exception as e:
                print(e)
        else:
            logger.critical("Port {0} on host {1} is unreachable".format(self.Port,self.Host))

    def whats_mysudo(self):
        '''
        This function will check what kind of sudo access the user has.
        '''
        self.command='sudo -nv ; echo $?'
        self.child.sendline(self.command)
        self.child.expect(self.PROMPT)
        self.output=self.child.before
        op=(self.output.decode('utf-8').splitlines())[1:-1]
        if 'password is required' in op[0] and int(op[-1])==1:
            return 'sudo_with_password'
        elif 'may not run' in op[0] and int(op[-1])==1:
            return 'no_sudo'
        elif int(op[-1])==0:
            return 'sudo_without_password'
        else:
            logger.warning("Please check your sudo access  manually")
            return "check_manually"

    def exec_command(self,command,sudo=False):
        '''
        This function works like an interactive shell.
        '''
        if self.child.isalive():
          if sudo:
              my_sudo=self.whats_mysudo()
              #logger.info("{0} has {1} privilages".format(self.User,my_sudo))
              if my_sudo=='no_sudo':
                  print('User {0} does not have sudo privilages'.format(self.User))
                  exit()
              elif my_sudo=='sudo_without_password':
                  self.command='sudo '+command
                  self.child.sendline(self.command)
                  self.child.expect(self.PROMPT)
                  self.output=self.child.before
                  cmd_op=(self.output.decode('utf-8').splitlines())
                  return cmd_op
              elif my_sudo=='sudo_with_password':
                  self.command='sudo '+command
                  self.child.sendline(self.command)
                  self.child.expect('assword')
                  self.child.sendline(self.Password)
                  self.child.expect(self.PROMPT)
                  self.child.sendline(self.command)
                  self.child.expect(self.PROMPT)
                  self.output=self.child.before
                  cmd_op=(self.output.decode('utf-8').splitlines())
                  return cmd_op[1:-1]
          else:
              self.command=command
              self.child.sendline(self.command)
              self.child.expect(self.PROMPT)
              self.output=self.child.before
              cmd_op=(self.output.decode('utf-8').splitlines())
              return cmd_op[1:-1]


    def interact(self):
        '''An interactive session will be opened from here..'''
        print("You are in interactive mode..Press ENTER...")
        self.child.interact()

    def scp(self,srcfile,dest_path):
        '''
        securely copy the file from source  to destination directory.
        This function does not use connect_ssh function.
        '''
        self.srcfile=srcfile
        self.dest_path=dest_path
        scp_command_str='scp '+srcfile+' ' + self.User+'@'+self.Host+':'+self.dest_path
        (output,exit_status)=pexpect.run(scp_command_str,events={'(?i)password':self.Password+'\n','(?i)yes/no':'yes'+'\n'},withexitstatus=1)
        return exit_status,output

    def nested_ssh(self,THost,TUser,TPassword=None,TSsh_key=None,Tcommand=None):
        '''
        Esatblish a ssh connection to server and return a command prompt
        '''
        if TSsh_key:
            nested_ssh_str = 'ssh '+ '-i {0} -oPasswordAuthentication=no '.format(TSsh_key) + TUser+'@'+THost
        else:
            nested_ssh_str = 'ssh -oNumberOfPasswordPrompts=1 '+TUser+'@'+THost

        try:
            self.child.sendline(nested_ssh_str)
            i = self.child.expect([pexpect.TIMEOUT,'[P|p]assword: ',pexpect.EOF,'[#$] ','passphrase','Permission denied'])
            if i == 3:
                print('Connected Successfully.')
                if Tcommand:
                    self.child.sendline(Tcommand)
                    self.child.expect('[#\$] ')
                    output=self.child.before
                    self.child.sendline('exit')
                    self.child.expect('[#\$] ')
                    op=(output.decode('utf-8').splitlines())
                    for line in op[1:-1]:
                        print(line)
                else:
                    self.child.interact()
            if i == 5:
                print("ssh key permissions issue")
            if i == 4:
                print("ssh key is asking passphrase, probably keys are not matching")
            if i == 0:
                print("Connection to Target {0} timedout".format(THost))
                exit()
            if i == 1:
                self.child.sendline(TPassword)
                i=self.child.expect(['Permission denied','[#\$] '])
                if i == 0:
                    print("Permission denied by host. Unable to login")
                    self.child.kill(0)
                elif i == 1:
                    print('Connected Successfully.')
                    if Tcommand:
                        self.child.sendline(Tcommand)
                        self.child.expect('[#\$] ')
                        output=self.child.before
                        self.child.sendline('exit')
                        self.child.expect('[#\$] ')
                        op=(output.decode('utf-8').splitlines())
                        for line in op[1:-1]:
                            print(line)
                    else:
                        self.child.interact()
        except pexpect.EOF as e:
            print(e)
        except Exception as e:
            print(e)
