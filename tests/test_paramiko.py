import paramiko
import socket


def doTests():
    hostname = '192.168.2.114'
    port = 22
    username = 'frank'
    password = 'kerstin'

    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh_client.connect(hostname=hostname, port=port, username=username, password=password)
        stdin, stdout, stderr = ssh_client.exec_command("sudo -S -p '' dmesg")
        stdin.write(f'{password}\n')
        stdin.flush()

        if stdout is not None:
            print(f'sshclient.receive (stdout): "{stdout.readlines()}"')
        if stderr is not None:
            print(f'sshclient.receive (stderr): "{stderr.readlines()}"')

    except paramiko.ssh_exception.BadHostKeyException as badhostEx:
        print(f'BadHostKeyException: {str(badhostEx)}')

    except paramiko.ssh_exception.AuthenticationException as authEx:
        print(f'AuthenticationException: {str(authEx)}')

    except paramiko.ssh_exception.UnableToAuthenticate as unableEx:
        print(f'UnableToAuthenticate: {str(unableEx)}')

    except socket.error as socketEx:
        print(f'socket.error: {str(socketEx)}')

    except paramiko.ssh_exception.NoValidConnectionsError as novalidConEx:
        print(f'NoValidConnectionsError: {str(novalidConEx)}')

    except paramiko.ssh_exception.SSHException as sshEx:
        print(f'SSHException: {str(sshEx)}')


if __name__ == '__main__':
    doTests()