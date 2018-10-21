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
        for line in inputFile:
            if line.strip('\n') != '':
                try:
                    ipNet = ipaddress.IPv4Network(line.strip('\n'))
                    try:
                        with open('iplist.txt', 'a') as resultFile:
                            if ipNet.num_addresses == 1:
                                resultFile.write(str(ipNet[0]) + '\n')
                            else:
                                for i in range(2, ipNet.num_addresses - 1):
                                    resultFile.write(str(ipNet[i]) + '\n')
                    except PermissionError:
                        print('No permission to access iplist.txt')
                        sys.exit()
                except ValueError:
                    print(line.strip('\n'), 'is not a valid IPv4Network')
    print('\nDone!')
except PermissionError:
    print('No permission to access input.txt')
    sys.exit()
except FileNotFoundError:
    print('File input.txt does not exist')
    sys.exit()
