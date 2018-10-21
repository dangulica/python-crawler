import datetime
import getpass
import ipaddress
import os
import platform
import socket
import subprocess
import sys
import telnetlib
import time


def processHost(ipaddress):
    print(timeStamp(), 'Processing host', ipaddress, '...', end=' ')
    logTelnet = ''
    logCisco = ''
    logCredentials = ''
    logSerianNumber = ''
    logModel = ''
    needsFailover = False
    logConnected = ''
    isPingUP, logPing = pingUP(ipaddress)
    if isPingUP:
        isTelnetAble, logTelnet = telnetVerify(ipaddress)
        if isTelnetAble:
            isCisco, logCisco = ciscoVerify(ipaddress)
            if isCisco:
                isLoginAble, logCredentials, userName, passWord, needsFailover = loginVerify(ipaddress, userAD, passAD)
                logConnected = 'YES' if isLoginAble else 'NO'
                if isLoginAble:
                    logModel, logSerianNumber = getModelSerialNumber(ipaddress, userName, passWord, needsFailover)
    logFailover = 'YES' if needsFailover else ''
    try:
        with open('result.csv', 'a') as resultFile:
            resultFile.write(str(ipaddress) + ','
                             + logPing + ','
                             + logTelnet + ','
                             + logCisco + ','
                             + logCredentials + ','
                             + logFailover + ','
                             + logConnected + ','
                             + logModel + ','
                             + logSerianNumber + ','
                             + timeStamp() + '\n')
    except PermissionError:
        print(timeStamp(), 'No permission to access result.csv')
        sys.exit()
    print('... Done!')


def pingUP(ipaddress):
    pingCountParam = '-n' if platform.system().lower() == 'windows' else '-c'
    with open(os.devnull, 'w') as devNull:
        ret_code = subprocess.call(['ping', pingCountParam, '2', ipaddress], stdout=devNull, stderr=devNull)
        result, answer = (True, 'UP') if ret_code == 0 else (False, 'DOWN')
    print('Ping', answer, end=', ')
    return (result, answer)


def telnetVerify(ipaddress, port=23):
    try:
        with telnetlib.Telnet(ipaddress, port, 5):
            connected = True
            answer = 'Open'
            time.sleep(0.1)
    except TimeoutError:
        connected = False
        answer = 'Timeout'
    except ConnectionRefusedError:
        connected = False
        answer = 'Refused'
    except socket.timeout:
        connected = False
        answer = 'Timeout'
    except EOFError:
        connected = False
        answer = 'EOFError'
    except BrokenPipeError:
        connected = False
        answer = 'BrokenPipe'
    print('Telnet', answer, end=', ')
    return (connected, answer)


def ciscoVerify(ipaddress):
    outputcisco = 'User Access Verification\r\n\r\nUsername:'
    with telnetlib.Telnet(ipaddress, '23') as tn:
        time.sleep(0.1)
        output = tn.read_very_eager().decode('utf-8')
    result, answer = ((True, 'Cisco') if outputcisco in output else (False, "NOT Cisco"))
    print('Brand', answer, end=', ')
    return (result, answer)


def getUserPassLists(userAD, passAD, position):
    try:
        with open('userpass.txt', 'r') as userpassFile:
            for i, line in enumerate(userpassFile):
                if i == 0:
                    usernames = line.strip('\n').split(',')
                elif i == 1:
                    passwords = line.strip('\n').split(',')
                elif i == 2:
                    failoverPasswords = line.strip('\n').split(',')
                else:
                    break
        usernames.insert(position, userAD)
        passwords.insert(position, passAD)
    except PermissionError:
        print(timeStamp(), 'No permission to access userpass.txt')
        sys.exit()
    except FileNotFoundError:
        print(timeStamp(), 'File userpass.txt does not exist')
        sys.exit()
    return (usernames, passwords, failoverPasswords)


def loginVerify(ipaddress, userAD, passAD):
    loginCredentials = ''
    needsFailover = False
    failoverAttempt = 0
    connected = False
    loginAttempt = 0
    usernames, passwords, failoverPasswords = getUserPassLists(userAD, passAD, int(position))
    while not connected and loginAttempt < len(usernames) and failoverAttempt < len(failoverPasswords):
        try:
            with telnetlib.Telnet(ipaddress, '23', 10) as tn:
                time.sleep(0.1)
                tn.read_until('Username'.encode('utf-8'), 10).decode('utf-8')
                userName = usernames[loginAttempt]
                passWord = passwords[loginAttempt]
                tn.write((userName + '\n').encode('utf-8'))
                tn.read_until('Password:'.encode('utf-8'), 10).decode('utf-8')
                tn.write((passWord + '\n').encode('utf-8'))
                output = tn.read_until('#'.encode('utf-8')
                                       or '%'.encode('utf-8')
                                       or 'Password:'.encode('utf-8'), 10).decode('utf-8')
                if '#' in output:
                    connected = True
                    break
                elif '%' in output:
                    connected = False
                    loginAttempt += 1
                else:
                    needsFailover = True
                    connected = False
                if needsFailover:
                    passWord = failoverPasswords[failoverAttempt]
                    tn.write((passWord + '\n').encode('utf-8'))
                    output4 = tn.read_until('#'.encode('utf-8') or '%'.encode('utf-8'), 10).decode('utf-8')
                    if '#' in output4:
                        connected = True
                        break
                    else:
                        connected = False
                        failoverAttempt += 1
        except TimeoutError:
            connected = False
            print('error')
        except ConnectionRefusedError:
            connected = False
            print('refused')
        except EOFError:
            connected = False
            print('EOFError')
        except BrokenPipeError:
            connected = False
            print('BrokenPipe')
    if connected:
        loginCredentials = passWord if passWord != passAD else 'AD Password'
    print('Login with ' + loginCredentials + ', Needs failover ' + str(needsFailover)
          + ', Connected ' + str(connected), end=', ')
    return (connected, loginCredentials, userName, passWord, needsFailover)


def getModelSerialNumber(ipaddress, userName, passWord, needsFailover):
    logSerialNumber = ''
    logModel = ''
    try:
        with telnetlib.Telnet(ipaddress, '23') as tn:
            time.sleep(0.1)
            tn.read_until('Username:'.encode('utf-8'), 5)
            tn.write((userName + '\n').encode('utf-8'))
            tn.read_until('Password:'.encode('utf-8'), 5)
            tn.write((passWord + '\n').encode('utf-8'))
            if needsFailover:
                tn.read_until('Password:'.encode('utf-8'), 10)
                tn.write((passWord + '\n').encode('utf-8'))
            tn.read_until('#'.encode('utf-8'))
            tn.write('terminal length 0\n'.encode('utf-8'))
            time.sleep(0.5)
            tn.write('show inventory\n'.encode('utf-8'))
            time.sleep(0.5)
            output = tn.read_very_eager().decode('utf-8')
            logSerialNumberList = []
            logModelList = []
            wantedSerial = 'SN: '
            wantedModel = 'PID: '
            for searchLine in output.split('\n'):
                if wantedSerial in searchLine:
                    logSerialNumberList.append(searchLine.split()[-1])
                if wantedModel in searchLine:
                    logModelList.append(searchLine.split()[1])
            logModel = ';'.join(logModelList)
            logSerialNumber = ';'.join(logSerialNumberList)
    except TimeoutError:
        print('Timeout')
        logSerialNumber = 'TimeoutError'
        logModel = 'TimeoutError'
    except EOFError:
        print('EOFError')
        logSerialNumber = 'EOFError'
        logModel = 'EOFError'
    except BrokenPipeError:
        print('BrokenPipe')
        logSerialNumber = 'BrokenPipe'
        logModel = 'BrokenPipe'
    print('Serial', logSerialNumber, end=', ')
    print('Model', logModel, end=' ')
    return logModel, logSerialNumber


def timeStamp():
    return datetime.datetime.now().strftime('%Y/%m/%d - %H:%M:%S')


if __name__ == "__main__":
    userAD = input('AD username: ')
    passAD = getpass.getpass('AD password: ')
    position = input('Used at position: ')
    print('Starting ...\n')
    if len(sys.argv) > 1:
        for argument in range(1, len(sys.argv)):
            try:
                host = ipaddress.IPv4Address(sys.argv[argument])
                processHost(str(host))
            except ValueError:
                print(timeStamp(), 'Host', sys.argv[argument], 'is not a valid IPv4 address')
    else:
        try:
            with open('iplist.txt', 'r') as inputFile:
                for host in inputFile:
                    try:
                        ipaddr = ipaddress.IPv4Address(host.strip('\n'))
                        processHost(str(ipaddr))
                    except ValueError:
                        print(timeStamp(), 'Host', host.strip('\n'), 'is not a valid IPv4 address')
        except PermissionError:
            print(timeStamp(), 'No permission to access input.txt')
            sys.exit()
        except FileNotFoundError:
            print(timeStamp(), 'File input.txt does not exist')
            sys.exit()
    print('\nCode executed')
