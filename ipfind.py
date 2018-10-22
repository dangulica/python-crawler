import ipaddress
import sys


try:
    with open('input.txt', 'r') as inputFile:
        try:
            with open('iplist.txt', 'w'):
                pass
        except PermissionError:
            print('No permission to access iplist.txt')
            sys.exit()
        setIP = set()
        for line in inputFile:
            if line.strip('\n') != '':
                try:
                    ipNet = ipaddress.IPv4Network(line.strip('\n'))
                    if ipNet.num_addresses == 1:
                        setIP.add(ipNet[0])
                    else:
                        for index in range(2, ipNet.num_addresses - 1):
                            setIP.add(ipNet[index])
                except ValueError:
                    print(line.strip('\n'), 'is not a valid IPv4Network')
        try:
            with open('iplist.txt', 'a') as resultFile:
                for ipAddr in sorted(setIP):
                    resultFile.write(str(ipAddr) + '\n')
        except PermissionError:
            print('No permission to access iplist.txt')
            sys.exit()
    print('\nDone!')
except PermissionError:
    print('No permission to access input.txt')
    sys.exit()
except FileNotFoundError:
    print('File input.txt does not exist')
    sys.exit()
