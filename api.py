import requests
import os, sys
import json
import random
import urllib3
from FileItem import FileItem
import argparse
import logging
from urllib.parse import urlparse

"""
Web File Browser API Client
A command line utility tool for HTTP File Browser that implements basic file operations like upload, download, delete, 
and get file info.

Author: Eric You
"""

logger = logging.getLogger()

# For windows curl to disable ssl certificate verification
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Global variable for the API URL
HOME_URL = os.getenv('FILEBROWSER_HOME', 'https://demo.filebrowser.org/')
parsed_home_url = urlparse(HOME_URL)
HOSTNAME = parsed_home_url.netloc

API_URL = os.getenv('FILEBROWSER_API', HOME_URL + "api" if HOME_URL.endswith("/") else HOME_URL + "/api")
FILEBROWSER_USERNAME = os.getenv('FILEBROWSER_USERNAME', 'demo')  # Default to 'demo' if not set
FILEBROWSER_PASSWORD = os.getenv('FILEBROWSER_PASSWORD', 'demo')  # Default to 'demo' if not set

# For windows curl to disable ssl certificate verification
DISABLE_VERIFY = True
TEST_RANDOM_ERROR = False

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:135.0) Gecko/20100101 Firefox/135.0"


# Function to get the access token from the FileBrowser server, only works if using http form authentication
def get_token():
    logger.info('Requesting access token...')
    try:
        headers = {
            'Content-Type': 'application/json',
            'Accept': '*/*',  # now it returns text instead of json
            'Accept-Encoding': '',  # do NOT use any compression
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': HOME_URL + '/login',
            'Origin': HOME_URL,
            'User-Agent': UA,
            'Connection': 'keep-alive',
            'Host': HOSTNAME,
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-GPC': '1'
        }

        username = FILEBROWSER_USERNAME
        password = FILEBROWSER_PASSWORD
        data = {
            'username': username,
            'password': password,
            'recaptcha': ''
        }
        logger.debug(json.dumps(data))
        response = requests.post(f'{API_URL}/login', data=json.dumps(data), headers=headers,
                                 verify=not DISABLE_VERIFY)
        response.raise_for_status()
        logger.info('Access token received.')
        return response.content.decode(response.encoding or 'utf-8')
    except requests.exceptions.RequestException as error:
        logger.error(f"Error while requesting access token: {str(error)}")
        exit(13)


def create_folder(token: str, target_path: str, override=False):
    if not target_path.endswith("/"):
        target_path = target_path + "/"
    if target_path.startswith("/"):
        target_path = target_path[1:]
    logger.debug('Creating folder at', target_path)
    request_url = f'{API_URL}/resources/{target_path}?override={str(override)}'
    try:
        request_headers = {
            'Content-Type': 'text/plain;charset=UTF-8',
            'X-Auth': token,
            "Referrer": HOME_URL,
            "Origin": HOME_URL,
            "User-Agent": UA,
            "Connection": "keep-alive",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.5",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Sec-GPC": "1",
            "Cookie": f"auth={token}"
        }
        response = requests.post(request_url, headers=request_headers, verify=not DISABLE_VERIFY)
        response.raise_for_status()

        logger.info(f'Folder created successfully at {target_path}.')

    except requests.exceptions.RequestException as error:
        logger.error(f"Error while creating folder at {target_path}: {str(error)}")
        exit(15)


# Function to upload a chunk of the file
def upload_chunk(url, chunk, headers, attempt, max_attempts):
    while attempt < max_attempts:
        try:
            response = requests.patch(url, data=chunk, headers=headers, verify=not DISABLE_VERIFY)
            response.raise_for_status()
            return response.status_code, response.text
        except requests.exceptions.RequestException as error:
            attempt += 1
            logger.error(
                f"Error while uploading chunk at {headers.get('Upload-Offset', 0)}, "
                f"attempt {attempt}/{max_attempts}: {str(error)}")
            if attempt == max_attempts:
                raise Exception(
                    f"Max attempts reached while uploading chunk offset {headers.get('Upload-Offset', 0)}. Aborting.")
    return None


# Function to upload a text file to the FileBrowser server with retry logic
def upload_file(token, file_path, target_path, override=False, max_attempts=3, chunk_size=10485760):
    if target_path.startswith('/'):
        target_path = target_path[1:]
    logger.info(f'Uploading file {file_path} to remote {target_path}')
    if check_remote_exists(token, target_path):
        logger.error(f'Remote path already exists at {target_path}. Aborting.')
        exit(11)
    request_url = f'{API_URL}/tus/{target_path}?override={str(override)}'
    failure = False
    expected_file_size = -1 if os.path.isdir(file_path) else os.path.getsize(file_path)

    try:
        file_created = requests.post(request_url,
                                     headers={'X-Auth': token},
                                     verify=not DISABLE_VERIFY)
        file_created.raise_for_status()
        logger.debug(f"status code: {file_created.status_code} , response: {file_created.text}")
        logger.debug('File created successfully. start uploading chunks...')

        upload_chunk_headers = {
            'Content-Type': 'application/offset+octet-stream',
            #content_type,  #TODO ADJUST THIS PER FILETYPE (img, pdf, etc)?
            'X-Auth': token,
            "Tus-Resumable": "1.0.0",
            "Referrer": HOME_URL,
            "Origin": HOME_URL,
            "User-Agent": UA,
            "Connection": "keep-alive",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.5",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Sec-GPC": "1",
            "Cookie": f"auth={token}"
        }

        with open(file_path, 'rb') as file:
            while chunk := file.read(chunk_size):
                new_headers = upload_chunk_headers.copy()
                new_headers['Upload-Offset'] = str(file.tell() - len(chunk))
                logger.debug(f'Processing chunk at offset {new_headers["Upload-Offset"]}...')
                attempt = 0
                while attempt < max_attempts:
                    try:
                        if TEST_RANDOM_ERROR:
                            test = random.randrange(1, 10)
                            if test <= 6:
                                failure = True
                                raise requests.exceptions.RequestException('Random error')
                        response = requests.patch(request_url, data=chunk, headers=new_headers,
                                                  verify=not DISABLE_VERIFY)
                        response.raise_for_status()
                        logger.debug(
                            f"processing chunk at {new_headers.get('Upload-Offset', 0)} "
                            f"status code: {response.status_code} , response: {response.text}")
                        break
                    except requests.exceptions.RequestException as error:
                        attempt += 1
                        logger.error(
                            f'Error while uploading chunk at {new_headers.get("Upload-Offset", 0)}, '
                            f'attempt {attempt}/{max_attempts}:',
                            error)
                        if attempt == max_attempts:
                            failure = True
                            raise Exception(f'Max attempts reached while processing chunk at '
                                            f'{new_headers.get("Upload-Offset", 0)}. Aborting.')

        logger.info('File uploaded successfully.')
    except (KeyboardInterrupt, SystemExit):
        logger.info('Upload process cancelled by user.')
        failure = True
    except (requests.exceptions.RequestException, IOError) as error:
        logger.error('Error while uploading file: ', error)
        failure = True
    finally:
        logger.info('Finalizing upload...')
        if failure:
            logger.info('deleting unfinished file because of a failure...')
            delete_file(token, target_path, expected_file_size)
            exit(16)
        else:
            logger.info('file uploaded successfully.')


def upload_file_or_folder(token, file_path, target_path, override=False, max_attempts=3, chunk_size=10485760):
    if not os.path.exists(file_path):
        logger.error(f"Local file '{file_path}' does not exist. Aborting.")
        exit(12)

    # now starts the os walk
    if not os.path.isdir(file_path):
        return upload_file(token, file_path, target_path, override=override, max_attempts=max_attempts,
                           chunk_size=chunk_size)

    for root, dirs, files in os.walk(file_path):
        # if uploading files first, it will create non-existing folders recursively first, this is safe.
        # if creating folder first, it will yield error of 404 not found, it doesn't support create folder recursively
        for file in files:
            new_src_path = os.path.join(root, file)
            new_target_path = target_path + file if target_path.endswith('/') else target_path + '/' + file
            logger.info(f'Uploading file to remote path {new_target_path} ...')
            upload_file(token, new_src_path, new_target_path, override=override, max_attempts=max_attempts,
                        chunk_size=chunk_size)
        for dirname in dirs:
            new_src_path = os.path.join(root, dirname)
            new_target_path = target_path + dirname if target_path.endswith('/') else target_path + '/' + dirname
            logger.info(f'Uploading directory to remote path {new_target_path} ...')
            create_folder(token, new_target_path)
            # os.walk() uses dfs, so no need to use recursion. just create all directory here.
            # upload_file_or_folder(token, new_src_path, new_target_path, override=override, max_attempts=max_attempts,
            #                       chunk_size=chunk_size)
    return None


def delete_file(token, target_path, compare_size=-1):
    if target_path.startswith('/'):
        target_path = target_path[1:]
    request_url = f'{API_URL}/tus/{target_path}'

    if compare_size <= 0:
        requests.delete(request_url, headers={'X-Auth': token}, verify=not DISABLE_VERIFY)
    else:
        #get file size and compare
        logger.debug('not implemented the file size compare...')
        requests.delete(request_url, headers={'X-Auth': token}, verify=not DISABLE_VERIFY)
        pass


def check_remote_exists(token, target_path) -> bool:
    logger.debug("Checking remote existence... " + target_path)
    current_file, sub_files = get_file_info(token, target_path)
    return current_file is not None


def get_file_info(token, target_path):
    if target_path.startswith('/'):
        target_path = target_path[1:]
    response = requests.get(f"{API_URL}/resources/{target_path}", headers={'X-Auth': token},
                            verify=not DISABLE_VERIFY)
    logger.debug(f"status code: {response.status_code}")
    if not response.ok:
        logger.error(f'get_file_info response: {response.text}')
        exit(18)
    decoded = json.loads(response.text)
    current_file = FileItem(decoded['name'], decoded['size'], decoded['path'], decoded['extension'],
                            decoded['modified'], decoded['mode'], decoded['isDir'], decoded['isSymlink'],
                            decoded['type'])
    sub_files = [
        FileItem(x['name'], x['size'], x['path'], x['extension'], x['modified'], x['mode'], x['isDir'], x['isSymlink'],
                 x['type']) for x in decoded.get('items', [])]
    return current_file, sub_files


# Function to download a text file from the FileBrowser server
def get_download_link(token, target_path):
    if target_path.startswith('/'):
        target_path = target_path[1:]
    # Why use different endpoints for upload and download? (resources vs raw)
    return f'{API_URL}/raw/{target_path}?auth={token}'


def download_file(token, target_path, local_download_path, chunk_size=10485760):
    if target_path.startswith('/'):
        target_path = target_path[1:]

    logger.info(f'Downloading file {target_path} to {local_download_path}...')
    download_url = get_download_link(token,
                                     target_path)

    headers = {
        'X-Auth': token
    }
    try:
        response = requests.get(download_url, headers=headers, stream=True, verify=not DISABLE_VERIFY)
        response.raise_for_status()
        with open(local_download_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=chunk_size):
                file.write(chunk)
        logger.info('File downloaded successfully.')
    except requests.exceptions.RequestException as error:
        logger.error('Error while requesting file download:', error)
        exit(19)


# Function to configure the logger level
def configure_logger_level(level: int):
    logger.setLevel(level)
    for handler in logger.handlers:
        handler.setLevel(level)


# Function to configure the logging
def configure_logging(to_file=False, to_stdout=True, filename='app.log'):
    # Remove any existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(funcName)s() %(message)s')

    if to_file:
        # Create file handler
        file_handler = logging.FileHandler(filename)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    if to_stdout:
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)


# Main function to control the flow of the program
def main():
    def parse_arguments():
        parser = argparse.ArgumentParser(
            description='FileBrowser API Client, a command line utility tool for HTTP File Browser, Author: Eric You')

        parser.add_argument('--json-output', action='store_true', default=False,
                            help='Enable JSON output, will disable stdout log messages but produce formatted JSON '
                                 'string reporting to stdout [NOT IMPLEMENTED YET]')

        parser.add_argument('--loglevel', type=str, default='INFO',
                            help='Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)')
        parser.add_argument('--logfile', type=str, default='app.log', help='Set the log file path')

        subparsers = parser.add_subparsers(dest='command', required=True)

        # Upload command
        upload_parser = subparsers.add_parser('upload', help='Upload a file or a folder')
        upload_parser.add_argument('file_path', type=str, help='Path to the file or folder to upload')
        upload_parser.add_argument('target_path', type=str, help='Target path on the server')
        upload_parser.add_argument('--override', action='store_true', help='Override existing file')
        upload_parser.add_argument('--max_attempts', type=int, default=3, help='Maximum upload attempts')
        upload_parser.add_argument('--chunk_size', type=int, default=10485760, help='Chunk size in bytes')

        # Download command
        download_parser = subparsers.add_parser('download', help='Download a file')
        download_parser.add_argument('target_path', type=str, help='Target path on the server')
        download_parser.add_argument('local_download_path', type=str,
                                     help='Local path to save the downloaded file')
        download_parser.add_argument('--chunk_size', type=int, default=10485760,
                                     help='Chunk size in bytes')

        # Get download link command
        get_download_link_parser = subparsers.add_parser('getdownloadlink', help='Get download link for a file')
        get_download_link_parser.add_argument('target_path', type=str, help='Target path on the server')

        # Get file info command
        get_file_info_parser = subparsers.add_parser('getfileinfo', help='Get file information')
        get_file_info_parser.add_argument('target_path', type=str, help='Target path on the server')

        return parser.parse_args()

    args = parse_arguments()

    # json output
    enable_json_output = args.json_output

    # Set up logging
    numeric_level = getattr(logging, args.loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {args.loglevel}')

    configure_logging()
    configure_logger_level(numeric_level)
    if enable_json_output:
        if args.logfile:
            configure_logging(to_file=True, to_stdout=False, filename=args.logfile)
        else:
            configure_logging(to_file=False, to_stdout=False)

    token_data = get_token()
    if not token_data:
        logger.error('No access token received. Aborting.')
        exit(20)
    token = token_data
    # parse commands
    if args.command == 'upload':
        upload_file_or_folder(token, args.file_path, args.target_path, args.override, args.max_attempts,
                              args.chunk_size)

    elif args.command == 'download':
        download_file(token, args.target_path, args.local_download_path, args.chunk_size)

    elif args.command == 'getdownloadlink':
        logger.info(get_download_link(token, args.target_path))

    elif args.command == 'getfileinfo':
        current, children = get_file_info(token, args.target_path)
        logger.info(repr(current))
        [logger.info(repr(child)) for child in children]
    # TODO delete file/folder sub-command
    else:
        logger.error('Invalid command. Aborting.')
        exit(17)

    exit(0)


# Start the program
if __name__ == '__main__':
    main()
