import sys
import common.connection

if __name__ == '__main__':
    try:
        common.connection.report_device_info()
        sys.exit(0)
    except Exception as error:
        print(f'Error: {error}')
        sys.exit(1)
