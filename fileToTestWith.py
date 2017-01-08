import pylog

def main():
    pyLog = pylog.PyLog(indentingWith='    ')
    fileToTestOn = pyLog.import_file('fileToTestOn.py')
    fileToTestOn.main()

if __name__ == '__main__':
    main()