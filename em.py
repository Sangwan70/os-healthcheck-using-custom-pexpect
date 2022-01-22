import commands
import sys
import os
from tempfile import mkstemp
fd,scriptFile =  mkstemp()
with os.fdopen (fd, "w") as fp:
        fp.write("""\
#!/bin/bash
tempFile=$(mktemp)
tgt="$1"
if [ -z ${tgt} ] || [ $# -ne 1 ]
then
        echo "Only One Input Argument .. Target Name Is Required"
        rm -rf ${tempFile}
        exit 1
fi
. /stage/PS4ES/common.sh
. /stage/PS4ES/common_validation.sh
emcli_login &>/dev/null
if [ -z $EMCLI_PATH ]
then
   res="EMCLI Login Failed"
   rm -rf ${tempFile}
   exit 1
fi
if timeout 60 sudo -u oracle $EMCLI_PATH  get_targets -target=oracle_emd -noheader -format=name:csv &> ${tempFile}
then
        if [ $( grep -ic $tgt ${tempFile} 2> /dev/null) -eq 1 ]
        then
                        tgt=$(grep $tgt ${tempFile} |cut -d, -f4)
                        timeout 60 sudo -u oracle $EMCLI_PATH get_agent_property -agent_name="${tgt}" -name=agentStateDir &> ${tempFile}
                        agentpath=$(echo $(grep "Property Value:" ${tempFile} |cut -d: -f2 ))
                        echo $agentpath
        else
                        echo "No Agent Target Found For Target Host ${tgt}"
        fi
else
        echo "Failed To Fetch Target Details From OEM"
fi
rm -rf ${tempFile}
""")
os.chmod(scriptFile,0o777)
def find_em_path(Host_name):
    cmd="sudo " + scriptFile + " " + Host_name
    status,output=commands.getstatusoutput(cmd)
    if not "No Agent Target Found For" in output:
        return True,output
    else:
        return False,''

if __name__=='__main__':
  Host_name=raw_input('Enter Hostname: ')
  print find_em_path(Host_name)
  os.unlink(scriptFile)
